#!/usr/bin/env python3
"""Migrador controlado de la SQLite de futbol-db a PostgreSQL/Supabase.

Modos disponibles:

    python scripts/migrate_sqlite_to_supabase.py --dry-run
    python scripts/migrate_sqlite_to_supabase.py --apply \
        --confirm MIGRATE_SQLITE_TO_SUPABASE

``--dry-run`` abre SQLite en modo lectura, deriva el esquema real y ejecuta
validaciones locales. No importa psycopg2, no lee credenciales y no establece
ninguna conexión de red.

``--apply`` queda preparado para una fase posterior. Solo acepta un esquema
destino donde no exista ninguna de las tablas de origen, usa una única
transacción y nunca elimina ni vacía tablas.
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Iterable, Optional


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "database" / "futbol_entrenamiento.sqlite"
NORMALIZATION_REPORT = ROOT / "docs" / "database_normalization_report.md"
OBJECTIVE_MAPPING = ROOT / "docs" / "normalizacion_objetivos.csv"
CATALOG_MAPPING = ROOT / "docs" / "normalizacion_catalogos.csv"
IMAGE_DIRECTORY = ROOT / "database" / "imagenes"
CONFIRMATION = "MIGRATE_SQLITE_TO_SUPABASE"
LOGGER = logging.getLogger("sqlite_to_supabase")

EXPECTED_NORMALIZED_COUNTS = {
    "ejercicios": 114,
    "imagenes": 122,
    "texto_original": 989,
    "objetivos": 129,
    "ejercicio_objetivo": 709,
    "tipos_tarea": 10,
    "espacios": 31,
    "tiempos": 23,
    "materiales": 44,
}

NORMALIZED_CATALOGS = {
    "objetivos": "nombre_normalizado",
    "tipos_tarea": "nombre",
    "espacios": "descripcion_original",
    "tiempos": "descripcion_original",
    "materiales": "nombre_normalizado",
}

SUPPORTED_DELETE_ACTIONS = {"NO ACTION", "RESTRICT", "CASCADE", "SET NULL", "SET DEFAULT"}
SUPPORTED_UPDATE_ACTIONS = SUPPORTED_DELETE_ACTIONS


@dataclass(frozen=True)
class ColumnInfo:
    cid: int
    name: str
    declared_type: str
    not_null: bool
    default: Optional[str]
    pk_order: int


@dataclass(frozen=True)
class ForeignKeyInfo:
    identifier: int
    sequence: int
    target_table: str
    source_column: str
    target_column: str
    on_update: str
    on_delete: str
    match: str


@dataclass(frozen=True)
class IndexInfo:
    name: str
    unique: bool
    origin: str
    partial: bool
    columns: tuple[str, ...]
    sql: Optional[str] = None


@dataclass
class TableInfo:
    name: str
    create_sql: str
    columns: list[ColumnInfo]
    foreign_keys: list[ForeignKeyInfo]
    indexes: list[IndexInfo]
    row_count: int
    uses_autoincrement_keyword: bool
    sequence_value: Optional[int]
    check_expressions: list[str]

    @property
    def primary_key(self) -> list[ColumnInfo]:
        return sorted(
            (column for column in self.columns if column.pk_order),
            key=lambda column: column.pk_order,
        )

    @property
    def identity_column(self) -> Optional[ColumnInfo]:
        primary_key = self.primary_key
        if len(primary_key) == 1 and type_family(primary_key[0].declared_type) == "integer":
            return primary_key[0]
        return None


@dataclass
class AuditResult:
    database: Path
    tables: list[TableInfo]
    migration_order: list[str]
    table_ddl: list[str]
    index_ddl: list[str]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    allowed_nulls: dict[str, dict[str, int]] = field(default_factory=dict)
    type_mappings: set[tuple[str, str]] = field(default_factory=set)
    unique_keys_checked: int = 0
    foreign_keys_checked: int = 0
    check_constraints: int = 0
    image_files_checked: int = 0

    @property
    def total_rows(self) -> int:
        return sum(table.row_count for table in self.tables)

    @property
    def ok(self) -> bool:
        return not self.errors


def sqlite_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def postgres_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def validate_schema_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Nombre de esquema PostgreSQL no válido: {value!r}")
    return value


def constraint_name(prefix: str, *parts: str) -> str:
    raw = "_".join((prefix, *parts))
    if len(raw) <= 63:
        return raw
    import hashlib
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]
    return f"{raw[:52]}_{digest}"


def type_family(declared_type: str) -> str:
    normalized = declared_type.strip().upper()
    base = normalized.split("(", 1)[0].strip()
    if "BOOL" in base:
        return "boolean"
    if "INT" in base:
        return "integer"
    if base in {"DATE"}:
        return "date"
    if base in {"TIME"}:
        return "time"
    if base in {"DATETIME", "TIMESTAMP"}:
        return "datetime"
    if any(token in base for token in ("CHAR", "CLOB", "TEXT", "VARCHAR")):
        return "text"
    if any(token in base for token in ("REAL", "FLOA", "DOUB")):
        return "real"
    if any(token in base for token in ("NUMERIC", "DECIMAL")):
        return "numeric"
    if "BLOB" in base or not base:
        return "blob"
    return "unsupported"


def postgres_type(declared_type: str) -> str:
    family = type_family(declared_type)
    mapping = {
        "boolean": "BOOLEAN",
        "integer": "INTEGER",
        "date": "DATE",
        "time": "TIME WITHOUT TIME ZONE",
        "datetime": "TIMESTAMP WITHOUT TIME ZONE",
        "text": "TEXT" if declared_type.strip().upper().startswith("TEXT") else "VARCHAR",
        "real": "DOUBLE PRECISION",
        "numeric": "NUMERIC",
        "blob": "BYTEA",
    }
    if family not in mapping:
        raise ValueError(f"Tipo SQLite no soportado: {declared_type!r}")
    return mapping[family]


def translate_default(
    default: Optional[str],
    declared_type: Optional[str] = None,
) -> Optional[str]:
    if default is None:
        return None

    value = default.strip()
    normalized_type = (declared_type or "").strip().upper()
    family = type_family(declared_type) if declared_type else None

    if value.upper() in {"CURRENT_TIMESTAMP", "CURRENT_DATE", "CURRENT_TIME"}:
        current_value = value.upper()

        # PostgreSQL no permite directamente CURRENT_TIMESTAMP como
        # DEFAULT de una columna TEXT. SQLite sí lo permite.
        # Conservamos el tipo TEXT de SQLite haciendo un cast explícito.
        if family == "text":
            return f"{current_value}::TEXT"

        return current_value

    # SQLite suele representar BOOLEAN como 0/1.
    # Solo debemos convertir 0/1 a FALSE/TRUE cuando la columna
    # realmente está declarada como BOOLEAN.
    if value == "0":
        return "FALSE" if family == "boolean" else "0"

    if value == "1":
        return "TRUE" if family == "boolean" else "1"

    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", value):
        return value

    if re.fullmatch(r"'(?:''|[^'])*'", value, flags=re.DOTALL):
        return value

    raise ValueError(
        f"Default SQLite no soportado de forma segura: "
        f"{default!r} para tipo {normalized_type or '<desconocido>'!r}"
    )


def extract_check_expressions(create_sql: str) -> list[str]:
    expressions: list[str] = []
    upper = create_sql.upper()
    position = 0
    while True:
        check_at = upper.find("CHECK", position)
        if check_at < 0:
            break
        opening = create_sql.find("(", check_at + len("CHECK"))
        if opening < 0:
            raise ValueError("CHECK sin paréntesis de apertura")
        depth = 0
        in_quote = False
        closing = None
        index = opening
        while index < len(create_sql):
            char = create_sql[index]
            if char == "'":
                if in_quote and index + 1 < len(create_sql) and create_sql[index + 1] == "'":
                    index += 2
                    continue
                in_quote = not in_quote
            elif not in_quote:
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        closing = index
                        break
            index += 1
        if closing is None:
            raise ValueError("CHECK sin paréntesis de cierre")
        expressions.append(create_sql[opening + 1:closing].strip())
        position = closing + 1
    return expressions


def named_unique_constraints(create_sql: str) -> dict[tuple[str, ...], str]:
    result: dict[tuple[str, ...], str] = {}
    pattern = re.compile(
        r"CONSTRAINT\s+([\w]+)\s+UNIQUE\s*\(([^)]+)\)", re.IGNORECASE
    )
    for match in pattern.finditer(create_sql):
        columns = tuple(
            value.strip().strip('"`[]') for value in match.group(2).split(",")
        )
        result[columns] = match.group(1)
    return result


def connect_sqlite_read_only(database: Path) -> sqlite3.Connection:
    if not database.is_file():
        raise FileNotFoundError(database)
    connection = sqlite3.connect(
        f"file:{database.resolve().as_posix()}?mode=ro", uri=True
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def inspect_schema(connection: sqlite3.Connection) -> list[TableInfo]:
    names = [
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    sequences = {
        row["name"]: row["seq"]
        for row in connection.execute(
            "SELECT name, seq FROM sqlite_sequence"
        )
    }
    tables: list[TableInfo] = []
    for name in names:
        create_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()["sql"]
        columns = [
            ColumnInfo(
                cid=row["cid"],
                name=row["name"],
                declared_type=row["type"],
                not_null=bool(row["notnull"]),
                default=row["dflt_value"],
                pk_order=row["pk"],
            )
            for row in connection.execute(
                f"PRAGMA table_xinfo({sqlite_identifier(name)})"
            )
            if row["hidden"] == 0
        ]
        foreign_keys = [
            ForeignKeyInfo(
                identifier=row["id"],
                sequence=row["seq"],
                target_table=row["table"],
                source_column=row["from"],
                target_column=row["to"],
                on_update=row["on_update"],
                on_delete=row["on_delete"],
                match=row["match"],
            )
            for row in connection.execute(
                f"PRAGMA foreign_key_list({sqlite_identifier(name)})"
            )
        ]
        indexes: list[IndexInfo] = []
        for row in connection.execute(
            f"PRAGMA index_list({sqlite_identifier(name)})"
        ):
            index_columns = tuple(
                info["name"]
                for info in connection.execute(
                    f"PRAGMA index_info({sqlite_identifier(row['name'])})"
                )
            )
            index_sql_row = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'index' AND name = ?",
                (row["name"],),
            ).fetchone()

            indexes.append(IndexInfo(
                name=row["name"],
                unique=bool(row["unique"]),
                origin=row["origin"],
                partial=bool(row["partial"]),
                columns=index_columns,
                sql=index_sql_row["sql"] if index_sql_row else None,
            ))
        tables.append(TableInfo(
            name=name,
            create_sql=create_sql,
            columns=columns,
            foreign_keys=foreign_keys,
            indexes=indexes,
            row_count=connection.execute(
                f"SELECT COUNT(*) FROM {sqlite_identifier(name)}"
            ).fetchone()[0],
            uses_autoincrement_keyword="AUTOINCREMENT" in create_sql.upper(),
            sequence_value=sequences.get(name),
            check_expressions=extract_check_expressions(create_sql),
        ))
    return tables


def topological_order(tables: Iterable[TableInfo]) -> list[str]:
    table_list = list(tables)
    names = {table.name for table in table_list}
    dependencies = {
        table.name: {
            foreign_key.target_table
            for foreign_key in table.foreign_keys
            if foreign_key.target_table in names and foreign_key.target_table != table.name
        }
        for table in table_list
    }
    result: list[str] = []
    while dependencies:
        ready = sorted(
            name for name, required in dependencies.items()
            if required.issubset(result)
        )
        if not ready:
            raise ValueError(
                "Hay un ciclo de claves foráneas no soportado: "
                + ", ".join(sorted(dependencies))
            )
        for name in ready:
            result.append(name)
            dependencies.pop(name)
    return result


def build_postgres_ddl(
    tables: list[TableInfo], schema_name: str
) -> tuple[list[str], list[str]]:
    schema = postgres_identifier(validate_schema_name(schema_name))
    by_name = {table.name: table for table in tables}
    table_statements: list[str] = []
    index_statements: list[str] = []
    for table_name in topological_order(tables):
        table = by_name[table_name]
        definitions: list[str] = []
        for column in table.columns:
            definition = (
                f"{postgres_identifier(column.name)} "
                f"{postgres_type(column.declared_type)}"
            )
            if table.identity_column and column.name == table.identity_column.name:
                definition += " GENERATED BY DEFAULT AS IDENTITY"
            if column.not_null or column.pk_order:
                definition += " NOT NULL"
            translated_default = translate_default(column.default, column.declared_type)
            if translated_default is not None:
                definition += f" DEFAULT {translated_default}"
            definitions.append(definition)

        primary_key = table.primary_key
        if primary_key:
            columns = ", ".join(
                postgres_identifier(column.name) for column in primary_key
            )
            definitions.append(
                f"CONSTRAINT {postgres_identifier(constraint_name('pk', table.name))} "
                f"PRIMARY KEY ({columns})"
            )

        named_uniques = named_unique_constraints(table.create_sql)
        for index in table.indexes:
            if not index.unique or index.origin != "u":
                continue
            name = named_uniques.get(
                index.columns,
                constraint_name("uq", table.name, *index.columns),
            )
            columns = ", ".join(postgres_identifier(value) for value in index.columns)
            definitions.append(
                f"CONSTRAINT {postgres_identifier(name)} UNIQUE ({columns})"
            )

        grouped_foreign_keys: dict[int, list[ForeignKeyInfo]] = defaultdict(list)
        for foreign_key in table.foreign_keys:
            grouped_foreign_keys[foreign_key.identifier].append(foreign_key)
        for identifier, group in sorted(grouped_foreign_keys.items()):
            ordered = sorted(group, key=lambda item: item.sequence)
            source_columns = ", ".join(
                postgres_identifier(item.source_column) for item in ordered
            )
            target_columns = ", ".join(
                postgres_identifier(item.target_column) for item in ordered
            )
            target_table = ordered[0].target_table
            name = constraint_name(
                "fk", table.name,
                *(item.source_column for item in ordered),
                str(identifier),
            )
            definition = (
                f"CONSTRAINT {postgres_identifier(name)} FOREIGN KEY ({source_columns}) "
                f"REFERENCES {schema}.{postgres_identifier(target_table)} "
                f"({target_columns})"
            )
            if ordered[0].on_update != "NO ACTION":
                definition += f" ON UPDATE {ordered[0].on_update}"
            if ordered[0].on_delete != "NO ACTION":
                definition += f" ON DELETE {ordered[0].on_delete}"
            definitions.append(definition)

        for number, expression in enumerate(table.check_expressions, start=1):
            definitions.append(
                f"CONSTRAINT {postgres_identifier(constraint_name('ck', table.name, str(number)))} "
                f"CHECK ({expression})"
            )

        joined = ",\n    ".join(definitions)
        table_statements.append(
            f"CREATE TABLE {schema}.{postgres_identifier(table.name)} (\n"
            f"    {joined}\n);"
        )

        for index in table.indexes:
            if index.origin != "c":
                continue
            if not index.columns or any(column is None for column in index.columns):
                raise ValueError(f"Índice de expresión no soportado: {index.name}")

            unique = "UNIQUE " if index.unique else ""
            columns = ", ".join(
                postgres_identifier(value) for value in index.columns
            )

            where_clause = ""
            if index.partial and index.sql:
                match = re.search(
                    r"\bWHERE\s+(.+)$",
                    index.sql,
                    flags=re.IGNORECASE | re.DOTALL,
                )
                if match:
                    where_clause = f" WHERE {match.group(1).strip()}"

            index_statements.append(
                f"CREATE {unique}INDEX {postgres_identifier(index.name)} "
                f"ON {schema}.{postgres_identifier(table.name)} "
                f"({columns}){where_clause};"
            )
    return table_statements, index_statements


def comparison_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = "".join(
        character for character in normalized
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def duplicate_group_count(
    connection: sqlite3.Connection, table: str, columns: Iterable[str]
) -> int:
    names = ", ".join(sqlite_identifier(column) for column in columns)
    query = (
        f"SELECT COUNT(*) FROM (SELECT {names}, COUNT(*) AS amount "
        f"FROM {sqlite_identifier(table)} GROUP BY {names} HAVING amount > 1)"
    )
    return connection.execute(query).fetchone()[0]


def temporal_value_is_valid(value: str, family: str) -> bool:
    try:
        if family == "date":
            date.fromisoformat(value)
        elif family == "time":
            time.fromisoformat(value)
        elif family == "datetime":
            datetime.fromisoformat(value)
        else:
            return False
    except (TypeError, ValueError):
        return False
    return True


def audit_columns_and_keys(
    connection: sqlite3.Connection, result: AuditResult
) -> None:
    for table in result.tables:
        if not table.primary_key:
            result.errors.append(f"{table.name}: no tiene clave primaria")
        else:
            primary_key_columns = [column.name for column in table.primary_key]
            result.unique_keys_checked += 1
            if duplicate_group_count(connection, table.name, primary_key_columns):
                result.errors.append(f"{table.name}: clave primaria duplicada")
            null_condition = " OR ".join(
                f"{sqlite_identifier(column)} IS NULL"
                for column in primary_key_columns
            )
            null_primary_keys = connection.execute(
                f"SELECT COUNT(*) FROM {sqlite_identifier(table.name)} "
                f"WHERE {null_condition}"
            ).fetchone()[0]
            if null_primary_keys:
                result.errors.append(
                    f"{table.name}: {null_primary_keys} PK con NULL"
                )

        allowed_nulls: dict[str, int] = {}
        for column in table.columns:
            family = type_family(column.declared_type)
            try:
                target_type = postgres_type(column.declared_type)
                result.type_mappings.add((column.declared_type or "<sin tipo>", target_type))
                translate_default(column.default, column.declared_type)
            except ValueError as error:
                result.errors.append(f"{table.name}.{column.name}: {error}")
                continue

            null_count = connection.execute(
                f"SELECT COUNT(*) FROM {sqlite_identifier(table.name)} "
                f"WHERE {sqlite_identifier(column.name)} IS NULL"
            ).fetchone()[0]
            if null_count and (column.not_null or column.pk_order):
                result.errors.append(
                    f"{table.name}.{column.name}: {null_count} NULL no permitidos"
                )
            elif null_count:
                allowed_nulls[column.name] = null_count

            storage_types = {
                row[0]
                for row in connection.execute(
                    f"SELECT DISTINCT typeof({sqlite_identifier(column.name)}) "
                    f"FROM {sqlite_identifier(table.name)} "
                    f"WHERE {sqlite_identifier(column.name)} IS NOT NULL"
                )
            }
            expected_storage = {
                "integer": {"integer"},
                "boolean": {"integer"},
                "date": {"text"},
                "time": {"text"},
                "datetime": {"text"},
                "text": {"text"},
                "real": {"real", "integer"},
                "numeric": {"real", "integer", "text"},
                "blob": {"blob"},
            }.get(family, set())
            unexpected = storage_types - expected_storage
            if unexpected:
                result.errors.append(
                    f"{table.name}.{column.name}: almacenamiento SQLite "
                    f"{sorted(unexpected)} incompatible con {column.declared_type}"
                )

            if family == "boolean":
                invalid = connection.execute(
                    f"SELECT COUNT(*) FROM {sqlite_identifier(table.name)} "
                    f"WHERE {sqlite_identifier(column.name)} IS NOT NULL "
                    f"AND {sqlite_identifier(column.name)} NOT IN (0, 1)"
                ).fetchone()[0]
                if invalid:
                    result.errors.append(
                        f"{table.name}.{column.name}: {invalid} booleanos fuera de 0/1"
                    )
            if family == "integer":
                invalid = connection.execute(
                    f"SELECT COUNT(*) FROM {sqlite_identifier(table.name)} "
                    f"WHERE {sqlite_identifier(column.name)} IS NOT NULL AND "
                    f"({sqlite_identifier(column.name)} < -2147483648 OR "
                    f"{sqlite_identifier(column.name)} > 2147483647)"
                ).fetchone()[0]
                if invalid:
                    result.errors.append(
                        f"{table.name}.{column.name}: {invalid} valores exceden INTEGER PostgreSQL"
                    )
            if family in {"date", "time", "datetime"}:
                invalid_values = [
                    row[0]
                    for row in connection.execute(
                        f"SELECT DISTINCT {sqlite_identifier(column.name)} "
                        f"FROM {sqlite_identifier(table.name)} "
                        f"WHERE {sqlite_identifier(column.name)} IS NOT NULL"
                    )
                    if not temporal_value_is_valid(row[0], family)
                ]
                if invalid_values:
                    result.errors.append(
                        f"{table.name}.{column.name}: valores temporales inválidos "
                        f"{invalid_values[:3]}"
                    )
            if family == "text":
                nul_characters = connection.execute(
                    f"SELECT COUNT(*) FROM {sqlite_identifier(table.name)} "
                    f"WHERE instr({sqlite_identifier(column.name)}, char(0)) > 0"
                ).fetchone()[0]
                if nul_characters:
                    result.errors.append(
                        f"{table.name}.{column.name}: {nul_characters} textos contienen NUL"
                    )

        if allowed_nulls:
            result.allowed_nulls[table.name] = allowed_nulls

        for index in table.indexes:
            if index.partial and not index.sql:
                result.errors.append(
                    f"{table.name}.{index.name}: índice parcial sin definición SQL"
                )
            if not index.columns:
                result.errors.append(f"{table.name}.{index.name}: índice sin columnas")
            if index.unique and index.origin != "pk":
                result.unique_keys_checked += 1
                if duplicate_group_count(connection, table.name, index.columns):
                    result.errors.append(
                        f"{table.name}.{index.name}: clave UNIQUE duplicada"
                    )


def audit_foreign_keys(
    connection: sqlite3.Connection, result: AuditResult
) -> None:
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        result.errors.append(f"PRAGMA integrity_check: {integrity}")
    violations = connection.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        result.errors.append(
            f"PRAGMA foreign_key_check detectó {len(violations)} relaciones huérfanas"
        )

    for table in result.tables:
        grouped: dict[int, list[ForeignKeyInfo]] = defaultdict(list)
        for foreign_key in table.foreign_keys:
            grouped[foreign_key.identifier].append(foreign_key)
            if foreign_key.on_delete not in SUPPORTED_DELETE_ACTIONS:
                result.errors.append(
                    f"{table.name}: ON DELETE no soportado {foreign_key.on_delete}"
                )
            if foreign_key.on_update not in SUPPORTED_UPDATE_ACTIONS:
                result.errors.append(
                    f"{table.name}: ON UPDATE no soportado {foreign_key.on_update}"
                )
        for group in grouped.values():
            result.foreign_keys_checked += 1
            ordered = sorted(group, key=lambda item: item.sequence)
            source_columns = [item.source_column for item in ordered]
            target_columns = [item.target_column for item in ordered]
            target_table = ordered[0].target_table
            join = " AND ".join(
                f"source.{sqlite_identifier(source)} = target.{sqlite_identifier(target)}"
                for source, target in zip(source_columns, target_columns)
            )
            non_null = " AND ".join(
                f"source.{sqlite_identifier(source)} IS NOT NULL"
                for source in source_columns
            )
            orphan_count = connection.execute(
                f"SELECT COUNT(*) FROM {sqlite_identifier(table.name)} AS source "
                f"LEFT JOIN {sqlite_identifier(target_table)} AS target ON {join} "
                f"WHERE {non_null} AND "
                f"target.{sqlite_identifier(target_columns[0])} IS NULL"
            ).fetchone()[0]
            if orphan_count:
                result.errors.append(
                    f"{table.name}->{target_table}: {orphan_count} relaciones huérfanas"
                )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def audit_normalization(
    connection: sqlite3.Connection, result: AuditResult
) -> None:
    if not NORMALIZATION_REPORT.is_file():
        result.errors.append(f"Falta {NORMALIZATION_REPORT.relative_to(ROOT)}")
    for table, expected in EXPECTED_NORMALIZED_COUNTS.items():
        actual = connection.execute(
            f"SELECT COUNT(*) FROM {sqlite_identifier(table)}"
        ).fetchone()[0]
        if actual != expected:
            result.errors.append(
                f"Normalización {table}: esperado {expected}, encontrado {actual}"
            )

    for table, column in NORMALIZED_CATALOGS.items():
        rows = connection.execute(
            f"SELECT {sqlite_identifier(column)} FROM {sqlite_identifier(table)}"
        ).fetchall()
        keys = [comparison_key(row[0]) for row in rows]
        if len(keys) != len(set(keys)):
            result.errors.append(f"{table}: quedan duplicados formales")

    objective_rows = read_csv_rows(OBJECTIVE_MAPPING)
    if len(objective_rows) != 53:
        result.errors.append(
            f"normalizacion_objetivos.csv: esperadas 53 filas, hay {len(objective_rows)}"
        )
    for row in objective_rows:
        source_id = int(row["original_id"])
        canonical_id = int(row["canonical_id"])
        if connection.execute(
            "SELECT 1 FROM objetivos WHERE id=?", (source_id,)
        ).fetchone():
            result.errors.append(f"Objetivo retirado aún existe: {source_id}")
        if not connection.execute(
            "SELECT 1 FROM objetivos WHERE id=?", (canonical_id,)
        ).fetchone():
            result.errors.append(f"Objetivo canónico ausente: {canonical_id}")

    catalog_rows = read_csv_rows(CATALOG_MAPPING)
    if len(catalog_rows) != 21:
        result.errors.append(
            f"normalizacion_catalogos.csv: esperadas 21 filas, hay {len(catalog_rows)}"
        )
    for row in catalog_rows:
        table = row["catalogo"]
        source_id = int(row["original_id"])
        canonical_id = int(row["canonical_id"])
        if connection.execute(
            f"SELECT 1 FROM {sqlite_identifier(table)} WHERE id=?", (source_id,)
        ).fetchone():
            result.errors.append(f"{table}: ID retirado aún existe: {source_id}")
        if not connection.execute(
            f"SELECT 1 FROM {sqlite_identifier(table)} WHERE id=?", (canonical_id,)
        ).fetchone():
            result.errors.append(f"{table}: ID canónico ausente: {canonical_id}")

    unused_objectives = connection.execute(
        "SELECT COUNT(*) FROM objetivos AS objective "
        "LEFT JOIN ejercicio_objetivo AS relation "
        "ON relation.objetivo_id=objective.id "
        "WHERE relation.objetivo_id IS NULL"
    ).fetchone()[0]
    if unused_objectives:
        result.errors.append(f"Hay {unused_objectives} objetivos sin relaciones")

    mismatches = connection.execute(
        "SELECT COUNT(*) FROM ejercicios AS exercise WHERE "
        "COALESCE(exercise.objetivo_1_normalizado, '') <> COALESCE(("
        "SELECT objective.nombre_normalizado FROM ejercicio_objetivo AS relation "
        "JOIN objetivos AS objective ON objective.id=relation.objetivo_id "
        "WHERE relation.ejercicio_id=exercise.id "
        "AND relation.tipo_objetivo='principal'), '') OR "
        "COALESCE(exercise.objetivo_2_normalizado, '') <> COALESCE(("
        "SELECT objective.nombre_normalizado FROM ejercicio_objetivo AS relation "
        "JOIN objetivos AS objective ON objective.id=relation.objetivo_id "
        "WHERE relation.ejercicio_id=exercise.id "
        "AND relation.tipo_objetivo='secundario'), '')"
    ).fetchone()[0]
    if mismatches:
        result.errors.append(
            f"Hay {mismatches} ejercicios con objetivos desnormalizados divergentes"
        )


def audit_image_manifest(
    connection: sqlite3.Connection, result: AuditResult
) -> None:
    """Comprueba los binarios referenciados, sin incluirlos en la migración SQL."""
    import hashlib

    if not IMAGE_DIRECTORY.is_dir():
        result.errors.append(f"Falta el directorio de imágenes: {IMAGE_DIRECTORY}")
        return
    for row in connection.execute(
        "SELECT id, archivo, sha256 FROM imagenes ORDER BY id"
    ):
        image_path = IMAGE_DIRECTORY / row["archivo"]
        try:
            image_path.resolve().relative_to(IMAGE_DIRECTORY.resolve())
        except ValueError:
            result.errors.append(
                f"imagenes.id={row['id']}: ruta fuera del directorio permitido"
            )
            continue
        if not image_path.is_file():
            result.errors.append(
                f"imagenes.id={row['id']}: falta el archivo {row['archivo']}"
            )
            continue
        digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
        if digest != row["sha256"]:
            result.errors.append(
                f"imagenes.id={row['id']}: SHA-256 no coincide para {row['archivo']}"
            )
            continue
        result.image_files_checked += 1

    result.warnings.append(
        "Se migrarán las filas y rutas de imagen, pero no los 122 PNG del filesystem; "
        "su subida a almacenamiento remoto queda fuera de este paso."
    )
    result.warnings.append(
        "Los documentos y animaciones almacenados como archivos tampoco forman parte "
        "de la migración SQL."
    )


def audit_source(database: Path, schema_name: str = "public") -> AuditResult:
    connection = connect_sqlite_read_only(database)
    try:
        tables = inspect_schema(connection)
        result = AuditResult(
            database=database.resolve(),
            tables=tables,
            migration_order=[],
            table_ddl=[],
            index_ddl=[],
        )
        try:
            result.migration_order = topological_order(tables)
            result.table_ddl, result.index_ddl = build_postgres_ddl(
                tables, schema_name
            )
        except ValueError as error:
            result.errors.append(str(error))
        audit_columns_and_keys(connection, result)
        audit_foreign_keys(connection, result)
        audit_normalization(connection, result)
        audit_image_manifest(connection, result)
        result.check_constraints = sum(
            len(table.check_expressions) for table in tables
        )
        return result
    finally:
        connection.close()


def convert_value(value: Any, column: ColumnInfo) -> Any:
    if value is None:
        return None
    family = type_family(column.declared_type)
    if family == "boolean":
        return bool(value)
    if family == "date":
        return date.fromisoformat(value)
    if family == "time":
        return time.fromisoformat(value)
    if family == "datetime":
        return datetime.fromisoformat(value)
    return value


def source_rows(
    connection: sqlite3.Connection, table: TableInfo
) -> list[tuple[Any, ...]]:
    column_names = ", ".join(
        sqlite_identifier(column.name) for column in table.columns
    )
    order_columns = table.primary_key
    order = ""
    if order_columns:
        order = " ORDER BY " + ", ".join(
            sqlite_identifier(column.name) for column in order_columns
        )
    rows = connection.execute(
        f"SELECT {column_names} FROM {sqlite_identifier(table.name)}{order}"
    ).fetchall()
    return [
        tuple(convert_value(row[column.name], column) for column in table.columns)
        for row in rows
    ]


def postgres_connection_parameters() -> dict[str, Any]:
    variable_names = (
        "SUPABASE_DB_HOST",
        "SUPABASE_DB_PORT",
        "SUPABASE_DB_NAME",
        "SUPABASE_DB_USER",
        "SUPABASE_DB_PASSWORD",
    )
    missing = [name for name in variable_names if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Faltan variables de entorno: " + ", ".join(missing)
        )
    try:
        port = int(os.environ["SUPABASE_DB_PORT"])
    except ValueError as error:
        raise RuntimeError("SUPABASE_DB_PORT debe ser un entero") from error
    return {
        "host": os.environ["SUPABASE_DB_HOST"],
        "port": port,
        "dbname": os.environ["SUPABASE_DB_NAME"],
        "user": os.environ["SUPABASE_DB_USER"],
        "password": os.environ["SUPABASE_DB_PASSWORD"],
        "sslmode": os.getenv("SUPABASE_DB_SSLMODE", "require"),
        "connect_timeout": 15,
    }


def migrate_to_postgres(result: AuditResult, schema_name: str) -> None:
    if not result.ok:
        raise RuntimeError("No se puede migrar: el dry-run contiene errores")
    schema_name = validate_schema_name(schema_name)
    try:
        import psycopg2
        from psycopg2.extras import execute_values
    except ImportError as error:
        raise RuntimeError(
            "psycopg2 no está instalado; instale psycopg2-binary"
        ) from error

    connection = psycopg2.connect(**postgres_connection_parameters())
    source = connect_sqlite_read_only(result.database)
    table_by_name = {table.name: table for table in result.tables}
    schema = postgres_identifier(schema_name)
    try:
        connection.autocommit = False
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema=%s AND table_name=ANY(%s) ORDER BY table_name",
                (schema_name, [table.name for table in result.tables]),
            )
            existing = [row[0] for row in cursor.fetchall()]
            if existing:
                raise RuntimeError(
                    "Migración cancelada: ya existen tablas destino: "
                    + ", ".join(existing)
                )

            LOGGER.info("Creando %s tablas dentro de una transacción", len(result.tables))
            for statement in result.table_ddl:
                cursor.execute(statement)

            for table_name in result.migration_order:
                table = table_by_name[table_name]
                rows = source_rows(source, table)
                if rows:
                    columns = ", ".join(
                        postgres_identifier(column.name) for column in table.columns
                    )
                    insert_sql = (
                        f"INSERT INTO {schema}.{postgres_identifier(table.name)} "
                        f"({columns}) VALUES %s"
                    )
                    execute_values(cursor, insert_sql, rows, page_size=1000)
                LOGGER.info("%s: %s filas insertadas", table.name, len(rows))

            for statement in result.index_ddl:
                cursor.execute(statement)

            for table in result.tables:
                identity = table.identity_column
                if not identity:
                    continue
                sequence_value = table.sequence_value
                if sequence_value is None:
                    source_max = source.execute(
                        f"SELECT MAX({sqlite_identifier(identity.name)}) "
                        f"FROM {sqlite_identifier(table.name)}"
                    ).fetchone()[0]
                    sequence_value = source_max
                qualified_table = f"{schema_name}.{table.name}"
                cursor.execute(
                    "SELECT pg_get_serial_sequence(%s, %s)",
                    (qualified_table, identity.name),
                )
                sequence_name = cursor.fetchone()[0]
                if sequence_name is None:
                    raise RuntimeError(
                        f"No se encontró la identidad de {table.name}.{identity.name}"
                    )
                if sequence_value is None:
                    cursor.execute("SELECT setval(%s, 1, false)", (sequence_name,))
                else:
                    cursor.execute(
                        "SELECT setval(%s, %s, true)",
                        (sequence_name, int(sequence_value)),
                    )

            for table in result.tables:
                cursor.execute(
                    f"SELECT COUNT(*) FROM {schema}.{postgres_identifier(table.name)}"
                )
                target_count = cursor.fetchone()[0]
                if target_count != table.row_count:
                    raise RuntimeError(
                        f"Conteo divergente en {table.name}: "
                        f"SQLite={table.row_count}, PostgreSQL={target_count}"
                    )
        connection.commit()
        LOGGER.info("Migración confirmada correctamente")
    except Exception:
        connection.rollback()
        LOGGER.exception("Migración revertida; PostgreSQL no fue confirmado")
        raise
    finally:
        source.close()
        connection.close()


def print_dry_run(result: AuditResult) -> None:
    print("DRY RUN OK" if result.ok else "DRY RUN FAILED")
    print()
    print(f"ORIGEN: {result.database}")
    print("SUPABASE CONNECTION: NO SOLICITADA")
    print()
    print(f"TABLAS ({len(result.tables)}):")
    for table in result.tables:
        primary_key = ",".join(column.name for column in table.primary_key)
        identity = table.identity_column.name if table.identity_column else "-"
        sequence = table.sequence_value if table.sequence_value is not None else "-"
        print(
            f"  {table.name}: {table.row_count} filas | PK={primary_key} "
            f"| identity={identity} | sqlite_sequence={sequence}"
        )
    print()
    print(f"REGISTROS TOTALES: {result.total_rows}")
    print("ORDEN DE MIGRACIÓN:")
    print("  " + " -> ".join(result.migration_order))
    print()
    print("MAPEO DE TIPOS:")
    for source_type, target_type in sorted(result.type_mappings):
        print(f"  {source_type} -> {target_type}")
    print()
    print("VALIDACIONES:")
    print(f"  PK/UNIQUE: {'OK' if result.ok else 'REVISAR'} ({result.unique_keys_checked} claves)")
    print(f"  FK: {'OK' if result.ok else 'REVISAR'} ({result.foreign_keys_checked} relaciones)")
    print(f"  NULLS: {'OK' if result.ok else 'REVISAR'}")
    print(f"  TIPOS: {'OK' if result.ok else 'REVISAR'}")
    print(f"  NORMALIZACION: {'OK' if result.ok else 'REVISAR'}")
    print(f"  RELACIONES: {'OK' if result.ok else 'REVISAR'}")
    print(f"  CHECKS: {'OK' if result.ok else 'REVISAR'} ({result.check_constraints})")
    print(
        f"  ARCHIVOS DE IMAGEN: {'OK' if result.ok else 'REVISAR'} "
        f"({result.image_files_checked})"
    )
    if result.allowed_nulls:
        print("  NULLS PERMITIDOS:")
        for table, values in sorted(result.allowed_nulls.items()):
            summary = ", ".join(f"{column}={amount}" for column, amount in values.items())
            print(f"    {table}: {summary}")
    if result.warnings:
        print()
        print("ADVERTENCIAS:")
        for warning in result.warnings:
            print(f"  - {warning}")
    if result.errors:
        print()
        print("ERRORES:")
        for error in result.errors:
            print(f"  - {error}")
    print()
    print("SUPABASE WRITE: 0")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--target-schema", default="public")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dry-run", action="store_true",
        help="auditar SQLite localmente sin conectar a Supabase",
    )
    mode.add_argument(
        "--apply", action="store_true",
        help="migrar en una transacción (reservado para una fase posterior)",
    )
    parser.add_argument(
        "--confirm",
        help=f"para --apply debe ser exactamente {CONFIRMATION}",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if arguments.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    try:
        result = audit_source(
            arguments.database.resolve(), arguments.target_schema
        )
        if arguments.dry_run:
            print_dry_run(result)
            return 0 if result.ok else 1
        if arguments.confirm != CONFIRMATION:
            raise RuntimeError(
                f"--apply requiere --confirm {CONFIRMATION}"
            )
        migrate_to_postgres(result, arguments.target_schema)
        return 0
    except Exception as error:
        LOGGER.error("%s", error)
        if arguments.dry_run:
            print()
            print("SUPABASE WRITE: 0")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
