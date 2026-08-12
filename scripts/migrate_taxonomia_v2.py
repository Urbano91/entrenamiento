#!/usr/bin/env python3
"""Crea la capa aditiva de taxonomía V2 en la SQLite local.

La migración es deliberadamente independiente de la configuración del backend.
Valida los CSV definitivos, protege mediante hashes lógicos las cuatro tablas
históricas y ejecuta todo el DDL/DML V2 en una única transacción.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "futbol_entrenamiento.sqlite"
MANIFEST_PATH = ROOT / "docs" / "taxonomia_objetivos_v2_manifest_final.csv"
CATALOG_PATH = ROOT / "docs" / "taxonomia_objetivos_v2_catalogo_final.csv"

MANIFEST_SHA256 = "ae7b65c48415fa343ff7c574390fb977e0bdd9ff2738bacc07574a7bd399e80f"
CATALOG_SHA256 = "253715f2aaa5b91469b47b658df78def9058f6e137e91afba979e9effe07a43e"

CATEGORY_NAMES = {
    "TEC": "Técnica",
    "TO": "Principios tácticos ofensivos",
    "TD": "Principios tácticos defensivos",
    "TRA": "Transiciones",
    "MOD": "Modelo y organización colectiva",
    "FIS": "Capacidades físicas",
    "CP": "Coordinación y prevención",
    "COG": "Cognitivo y comunicativo",
}
CATEGORY_ORDER = tuple(CATEGORY_NAMES)

TARGET_TABLES = (
    "taxonomia_objetivo_versiones",
    "categorias_objetivo",
    "objetivos_normalizados_v2",
    "mapeos_objetivo",
    "mapeo_objetivo_destinos",
    "terminos_clasificacion",
    "mapeo_objetivo_terminos",
    "mapeos_objetivo_excepciones",
    "mapeo_excepcion_destinos",
)

LOGICAL_QUERIES = {
    "ejercicios": (
        "SELECT id, numero, codigo, nombre, nombre_original, tipo_tarea_id, "
        "jugadores, espacio_id, tiempo_id, desarrollo, objetivo_1_original, "
        "objetivo_1_normalizado, objetivo_2_original, objetivo_2_normalizado "
        "FROM ejercicios ORDER BY id"
    ),
    "objetivos": "SELECT id, nombre_normalizado FROM objetivos ORDER BY id",
    "ejercicio_objetivo": (
        "SELECT ejercicio_id, objetivo_id, tipo_objetivo, objetivo_original "
        "FROM ejercicio_objetivo "
        "ORDER BY ejercicio_id, objetivo_id, tipo_objetivo"
    ),
    "texto_original": (
        "SELECT id, ejercicio_id, categoria, texto, fila_origen, columna_origen, orden "
        "FROM texto_original ORDER BY id"
    ),
}

PRECHECK_LOGICAL_HASHES = {
    "ejercicios": "6c3aca23e15b3c208f35a67e1e3165a5fe5412a0150bf65f5c200473a07b9955",
    "objetivos": "7e1993a3e361d6e99bc38b02e0008c27796ab6d6458401e6e46e4600e0e653e3",
    "ejercicio_objetivo": "dd285267c2ecfdcca896bceb144cdf9b42bcc146833477b4a64bee367792e154",
    "texto_original": "1fc052307b8edcaba023563d8c33b4137bc6752adb79488ffd9c152d89c46d52",
}

EXPECTED_HISTORICAL = {
    "ejercicios": 114,
    "objetivos": 129,
    "relaciones": 709,
    "pares_originales": 577,
    "valores_originales": 191,
    "huerfanos": 0,
    "duplicados_pk": 0,
    "sin_objetivo_original": 0,
}

EXPECTED_V2 = {
    "mapeos": 129,
    "objetivos_normalizados": 94,
    "categorias": 8,
    "relaciones_procedencia": 747,
    "pares_semanticos": 585,
    "ejercicios_representados": 114,
    "grupos_procedencia_multiple": 161,
    "excepciones": 13,
}

MANIFEST_FIELDS = (
    "version",
    "objetivo_origen_id",
    "objetivo_origen",
    "frecuencia_ejercicios",
    "frecuencia_relaciones",
    "accion",
    "categoria_destino",
    "objetivo_destino_1",
    "objetivo_destino_2",
    "objetivo_destino_3",
    "contexto",
    "formato",
    "confianza",
    "estado_revision",
    "motivo",
    "ejercicio_excepcion",
    "decision_entrenador",
)
CATALOG_FIELDS = (
    "version",
    "objetivo_destino",
    "categoria",
    "objetivos_origen",
    "relaciones_procedencia",
    "ejercicios_distintos",
)


class ValidationError(RuntimeError):
    """Una precondición o una validación de integridad no se cumple."""


@dataclass(frozen=True)
class SourceRelation:
    ejercicio_id: int
    objetivo_id: int
    tipo_objetivo: str
    objetivo_original: str


@dataclass
class PreparedInputs:
    manifest: list[dict[str, str]]
    catalog: list[dict[str, str]]
    exceptions: dict[int, list[dict[str, Any]]]
    targets_by_source: dict[int, tuple[str, ...]]
    category_by_target: dict[str, str]
    relations: list[SourceRelation]
    expected_provenance: list[tuple[int, int, str, str, str]]
    expected_context_only_relations: int


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def logical_hash(conn: sqlite3.Connection, query: str) -> str:
    digest = hashlib.sha256()
    for row in conn.execute(query):
        encoded = json.dumps(
            list(row), ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        digest.update(encoded)
        digest.update(b"\n")
    return digest.hexdigest()


def logical_hashes(conn: sqlite3.Connection) -> dict[str, str]:
    return {name: logical_hash(conn, query) for name, query in LOGICAL_QUERIES.items()}


def physical_hash() -> str:
    return sha256_file(DB_PATH)


def read_csv(path: Path, expected_fields: Sequence[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        require(tuple(reader.fieldnames or ()) == tuple(expected_fields), f"Cabecera inesperada en {path}")
        return list(reader)


def historical_metrics(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        "ejercicios": conn.execute("SELECT COUNT(*) FROM ejercicios").fetchone()[0],
        "objetivos": conn.execute("SELECT COUNT(*) FROM objetivos").fetchone()[0],
        "relaciones": conn.execute("SELECT COUNT(*) FROM ejercicio_objetivo").fetchone()[0],
        "pares_originales": conn.execute(
            "SELECT COUNT(*) FROM (SELECT DISTINCT ejercicio_id, objetivo_id FROM ejercicio_objetivo)"
        ).fetchone()[0],
        "valores_originales": conn.execute(
            "SELECT COUNT(DISTINCT objetivo_original) FROM ejercicio_objetivo"
        ).fetchone()[0],
        "huerfanos": conn.execute(
            "SELECT COUNT(*) FROM objetivos o LEFT JOIN ejercicio_objetivo eo "
            "ON eo.objetivo_id = o.id WHERE eo.objetivo_id IS NULL"
        ).fetchone()[0],
        "duplicados_pk": conn.execute(
            "SELECT COUNT(*) FROM (SELECT ejercicio_id, objetivo_id, tipo_objetivo, COUNT(*) AS n "
            "FROM ejercicio_objetivo GROUP BY ejercicio_id, objetivo_id, tipo_objetivo HAVING n > 1)"
        ).fetchone()[0],
        "sin_objetivo_original": conn.execute(
            "SELECT COUNT(*) FROM ejercicio_objetivo "
            "WHERE objetivo_original IS NULL OR TRIM(objetivo_original) = ''"
        ).fetchone()[0],
    }


def validate_historical(conn: sqlite3.Connection, require_precheck_hashes: bool = True) -> dict[str, Any]:
    metrics = historical_metrics(conn)
    require(metrics == EXPECTED_HISTORICAL, f"Métricas históricas discrepantes: {metrics}")
    integrity = conn.execute("PRAGMA integrity_check").fetchall()
    require(integrity == [("ok",)], f"PRAGMA integrity_check falló: {integrity}")
    foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
    require(not foreign_keys, f"PRAGMA foreign_key_check encontró {len(foreign_keys)} errores")
    hashes = logical_hashes(conn)
    if require_precheck_hashes:
        require(
            hashes == PRECHECK_LOGICAL_HASHES,
            f"Las firmas históricas ya no coinciden con el precheck: {hashes}",
        )
    return {"metrics": metrics, "logical_hashes": hashes}


def source_relations(conn: sqlite3.Connection) -> list[SourceRelation]:
    return [
        SourceRelation(int(row[0]), int(row[1]), str(row[2]), str(row[3]))
        for row in conn.execute(
            "SELECT ejercicio_id, objetivo_id, tipo_objetivo, objetivo_original "
            "FROM ejercicio_objetivo ORDER BY ejercicio_id, objetivo_id, tipo_objetivo"
        )
    ]


def manifest_targets(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(
        value.strip()
        for value in (
            row["objetivo_destino_1"],
            row["objetivo_destino_2"],
            row["objetivo_destino_3"],
        )
        if value.strip()
    )


def parse_exceptions(row: dict[str, str]) -> list[dict[str, Any]]:
    raw = row["ejercicio_excepcion"].strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"JSON de excepciones inválido para {row['objetivo_origen']}: {exc}"
        ) from exc
    require(isinstance(parsed, list), f"Las excepciones de {row['objetivo_origen']} no son una lista")
    return parsed


def validate_input_files(conn: sqlite3.Connection) -> PreparedInputs:
    require(sha256_file(MANIFEST_PATH) == MANIFEST_SHA256, "El SHA-256 del manifiesto final no coincide")
    require(sha256_file(CATALOG_PATH) == CATALOG_SHA256, "El SHA-256 del catálogo final no coincide")

    manifest = read_csv(MANIFEST_PATH, MANIFEST_FIELDS)
    catalog = read_csv(CATALOG_PATH, CATALOG_FIELDS)
    require(len(manifest) == 129, f"El manifiesto contiene {len(manifest)} filas, no 129")
    require(len(catalog) == 94, f"El catálogo contiene {len(catalog)} filas, no 94")
    require(all(row["version"] == "v2-final" for row in manifest + catalog), "Versión de CSV inesperada")

    source_names = {int(row[0]): str(row[1]) for row in conn.execute("SELECT id, nombre_normalizado FROM objetivos")}
    relation_rows = source_relations(conn)
    relations_by_source: dict[int, list[SourceRelation]] = defaultdict(list)
    for relation in relation_rows:
        relations_by_source[relation.objetivo_id].append(relation)

    manifest_ids = [int(row["objetivo_origen_id"]) for row in manifest]
    require(len(set(manifest_ids)) == 129, "Hay IDs de origen repetidos en el manifiesto")
    require(set(manifest_ids) == set(source_names), "La cobertura de objetivos históricos no es exacta")
    require(len({row["objetivo_origen"] for row in manifest}) == 129, "Hay nombres fuente repetidos")

    actions = Counter(row["accion"] for row in manifest)
    require(
        actions == Counter({"UNIFICAR": 69, "MANTENER": 39, "DIVIDIR": 12, "REUBICAR": 9}),
        f"Distribución de acciones inesperada: {dict(actions)}",
    )
    require(all(row["accion"] != "REVISAR" for row in manifest), "Quedan acciones REVISAR")
    require(all(row["estado_revision"] != "PENDIENTE" for row in manifest), "Quedan estados PENDIENTE")
    require(
        all(row["confianza"] in {"ALTA", "MEDIA", "BAJA"} for row in manifest),
        "Confianza desconocida",
    )
    require(
        all(row["estado_revision"] in {"APROBADO", "CONTEXTO", "FORMATO", "EXCEPCION"} for row in manifest),
        "Estado de revisión desconocido",
    )

    category_by_target: dict[str, str] = {}
    catalog_source_sets: dict[str, set[tuple[int, str, str, str]]] = {}
    for row in catalog:
        target = row["objetivo_destino"].strip()
        category = row["categoria"].strip()
        require(target and target not in category_by_target, f"Destino vacío o duplicado: {target!r}")
        require(category in CATEGORY_NAMES, f"Categoría desconocida en catálogo: {category}")
        category_by_target[target] = category
        try:
            sources = json.loads(row["objetivos_origen"])
        except json.JSONDecodeError as exc:
            raise ValidationError(f"JSON de fuentes inválido para {target}: {exc}") from exc
        require(isinstance(sources, list) and sources, f"Sin fuentes en el catálogo para {target}")
        parsed_sources: set[tuple[int, str, str, str]] = set()
        for source in sources:
            parsed_sources.add(
                (
                    int(source["objetivo_origen_id"]),
                    str(source["objetivo_origen"]),
                    str(source["accion"]),
                    str(source["alcance"]),
                )
            )
        require(len(parsed_sources) == len(sources), f"Fuentes duplicadas en catálogo para {target}")
        catalog_source_sets[target] = parsed_sources

    require(set(category_by_target.values()) == set(CATEGORY_NAMES), "No están presentes las ocho categorías")
    distribution = Counter(category_by_target.values())
    require(
        distribution == Counter({"TEC": 16, "TO": 27, "TD": 16, "TRA": 12, "MOD": 7, "FIS": 9, "CP": 5, "COG": 2}),
        f"Distribución de categorías inesperada: {dict(distribution)}",
    )

    exceptions_by_source: dict[int, list[dict[str, Any]]] = {}
    targets_by_source: dict[int, tuple[str, ...]] = {}
    expected_catalog_sources: dict[str, set[tuple[int, str, str, str]]] = defaultdict(set)
    exception_count = 0

    for row in manifest:
        source_id = int(row["objetivo_origen_id"])
        source_name = row["objetivo_origen"]
        require(source_names[source_id] == source_name, f"Nombre fuente discrepante para ID {source_id}")
        source_items = relations_by_source[source_id]
        require(int(row["frecuencia_relaciones"]) == len(source_items), f"Frecuencia de relaciones incorrecta para {source_name}")
        require(
            int(row["frecuencia_ejercicios"]) == len({item.ejercicio_id for item in source_items}),
            f"Frecuencia de ejercicios incorrecta para {source_name}",
        )

        targets = manifest_targets(row)
        require(len(targets) == len(set(targets)), f"Destinos globales repetidos para {source_name}")
        for target in targets:
            require(target in category_by_target, f"Destino ausente del catálogo: {target}")
            require(
                category_by_target[target] == row["categoria_destino"],
                f"Categoría global discrepante para {source_name} -> {target}",
            )
            expected_catalog_sources[target].add((source_id, source_name, row["accion"], "global"))
        if targets:
            require(row["categoria_destino"] in CATEGORY_NAMES, f"Categoría vacía para {source_name}")
        else:
            require(not row["categoria_destino"], f"Categoría sin destino para {source_name}")
        targets_by_source[source_id] = targets

        exceptions = parse_exceptions(row)
        require(not (targets and exceptions), f"{source_name} mezcla mapeo global y excepciones")
        if exceptions:
            require(row["estado_revision"] == "EXCEPCION", f"Excepciones sin estado EXCEPCION: {source_name}")
            actual_keys = {(item.ejercicio_id, item.tipo_objetivo) for item in source_items}
            exception_keys: set[tuple[int, str]] = set()
            for exception in exceptions:
                exercise_id = int(exception["ejercicio_id"])
                role = str(exception["tipo_objetivo"])
                key = (exercise_id, role)
                require(key in actual_keys, f"Excepción inexistente para {source_name}: {key}")
                require(key not in exception_keys, f"Excepción duplicada para {source_name}: {key}")
                exception_keys.add(key)
                destinations = exception.get("destinos")
                require(isinstance(destinations, list) and destinations, f"Excepción sin destino para {source_name}: {key}")
                destination_names: set[str] = set()
                for destination in destinations:
                    target = str(destination["objetivo"])
                    category = str(destination["categoria"])
                    require(target not in destination_names, f"Destino de excepción duplicado para {source_name}: {key}")
                    destination_names.add(target)
                    require(target in category_by_target, f"Destino de excepción ausente del catálogo: {target}")
                    require(category_by_target[target] == category, f"Categoría de excepción discrepante: {target}")
                    expected_catalog_sources[target].add((source_id, source_name, row["accion"], "excepcion"))
                require(str(exception.get("motivo", "")).strip(), f"Excepción sin motivo para {source_name}: {key}")
            require(exception_keys == actual_keys, f"Cobertura de excepciones incompleta para {source_name}")
            exceptions_by_source[source_id] = exceptions
            exception_count += len(exceptions)
        else:
            require(row["estado_revision"] != "EXCEPCION", f"Estado EXCEPCION sin decisiones: {source_name}")

        if not targets and not exceptions:
            require(row["accion"] == "REUBICAR", f"Fuente sin destino que no es REUBICAR: {source_name}")
            require(row["contexto"] or row["formato"], f"REUBICAR sin contexto/formato: {source_name}")

    require(exception_count == EXPECTED_V2["excepciones"], f"Se esperaban 13 excepciones y hay {exception_count}")

    provenance: list[tuple[int, int, str, str, str]] = []
    context_only = 0
    for relation in relation_rows:
        targets = targets_by_source[relation.objetivo_id]
        if relation.objetivo_id in exceptions_by_source:
            exception = next(
                item
                for item in exceptions_by_source[relation.objetivo_id]
                if int(item["ejercicio_id"]) == relation.ejercicio_id
                and str(item["tipo_objetivo"]) == relation.tipo_objetivo
            )
            targets = tuple(str(item["objetivo"]) for item in exception["destinos"])
        if not targets:
            context_only += 1
        for target in targets:
            provenance.append(
                (
                    relation.ejercicio_id,
                    relation.objetivo_id,
                    relation.tipo_objetivo,
                    relation.objetivo_original,
                    target,
                )
            )

    semantic_counts = Counter((item[0], item[4]) for item in provenance)
    projection_metrics = {
        "relaciones_procedencia": len(provenance),
        "pares_semanticos": len(semantic_counts),
        "ejercicios_representados": len({item[0] for item in provenance}),
        "grupos_procedencia_multiple": sum(count > 1 for count in semantic_counts.values()),
    }
    require(
        projection_metrics == {key: EXPECTED_V2[key] for key in projection_metrics},
        f"Proyección del manifiesto discrepante: {projection_metrics}",
    )

    provenance_by_target: dict[str, list[tuple[int, int, str, str, str]]] = defaultdict(list)
    for item in provenance:
        provenance_by_target[item[4]].append(item)
    catalog_by_target = {row["objetivo_destino"]: row for row in catalog}
    require(set(catalog_by_target) == set(provenance_by_target), "Catálogo y proyección no tienen los mismos destinos")
    for target, items in provenance_by_target.items():
        row = catalog_by_target[target]
        require(int(row["relaciones_procedencia"]) == len(items), f"Procedencia discrepante para {target}")
        require(int(row["ejercicios_distintos"]) == len({item[0] for item in items}), f"Ejercicios discrepantes para {target}")
        require(catalog_source_sets[target] == expected_catalog_sources[target], f"Fuentes de catálogo discrepantes para {target}")

    return PreparedInputs(
        manifest=manifest,
        catalog=catalog,
        exceptions=exceptions_by_source,
        targets_by_source=targets_by_source,
        category_by_target=category_by_target,
        relations=relation_rows,
        expected_provenance=provenance,
        expected_context_only_relations=context_only,
    )


DDL_STATEMENTS = (
    """
    CREATE TABLE taxonomia_objetivo_versiones (
        id INTEGER PRIMARY KEY,
        codigo_version TEXT NOT NULL UNIQUE,
        estado TEXT NOT NULL CHECK (estado IN ('BORRADOR', 'APROBADA', 'ACTIVA', 'RETIRADA')),
        fecha_creacion TEXT NOT NULL,
        fecha_activacion TEXT,
        motivo TEXT NOT NULL,
        manifiesto_sha256 TEXT NOT NULL,
        catalogo_sha256 TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (estado != 'ACTIVA' OR fecha_activacion IS NOT NULL)
    )
    """,
    "CREATE UNIQUE INDEX uq_taxonomia_objetivo_version_activa ON taxonomia_objetivo_versiones(estado) WHERE estado = 'ACTIVA'",
    """
    CREATE TABLE categorias_objetivo (
        id INTEGER PRIMARY KEY,
        version_id INTEGER NOT NULL,
        codigo TEXT NOT NULL,
        nombre TEXT NOT NULL,
        orden INTEGER NOT NULL CHECK (orden > 0),
        UNIQUE (version_id, codigo),
        UNIQUE (version_id, nombre),
        UNIQUE (version_id, orden),
        FOREIGN KEY (version_id) REFERENCES taxonomia_objetivo_versiones(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE objetivos_normalizados_v2 (
        id INTEGER PRIMARY KEY,
        version_id INTEGER NOT NULL,
        categoria_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        orden INTEGER NOT NULL CHECK (orden > 0),
        activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
        UNIQUE (version_id, nombre),
        UNIQUE (version_id, categoria_id, orden),
        FOREIGN KEY (version_id) REFERENCES taxonomia_objetivo_versiones(id) ON DELETE CASCADE,
        FOREIGN KEY (categoria_id) REFERENCES categorias_objetivo(id)
    )
    """,
    """
    CREATE TABLE mapeos_objetivo (
        id INTEGER PRIMARY KEY,
        version_id INTEGER NOT NULL,
        objetivo_origen_id INTEGER NOT NULL,
        objetivo_origen_snapshot TEXT NOT NULL,
        frecuencia_ejercicios INTEGER NOT NULL CHECK (frecuencia_ejercicios >= 0),
        frecuencia_relaciones INTEGER NOT NULL CHECK (frecuencia_relaciones >= 0),
        accion TEXT NOT NULL CHECK (accion IN ('MANTENER', 'UNIFICAR', 'DIVIDIR', 'REUBICAR')),
        confianza TEXT NOT NULL CHECK (confianza IN ('ALTA', 'MEDIA', 'BAJA')),
        estado_decision TEXT NOT NULL CHECK (estado_decision IN ('APROBADO', 'CONTEXTO', 'FORMATO', 'EXCEPCION')),
        decision_entrenador TEXT NOT NULL,
        motivo TEXT NOT NULL,
        UNIQUE (version_id, objetivo_origen_id),
        UNIQUE (id, version_id, objetivo_origen_id),
        FOREIGN KEY (version_id) REFERENCES taxonomia_objetivo_versiones(id) ON DELETE CASCADE,
        FOREIGN KEY (objetivo_origen_id) REFERENCES objetivos(id)
    )
    """,
    """
    CREATE TABLE mapeo_objetivo_destinos (
        id INTEGER PRIMARY KEY,
        mapeo_id INTEGER NOT NULL,
        objetivo_normalizado_id INTEGER NOT NULL,
        orden INTEGER NOT NULL CHECK (orden > 0),
        UNIQUE (mapeo_id, objetivo_normalizado_id),
        UNIQUE (mapeo_id, orden),
        FOREIGN KEY (mapeo_id) REFERENCES mapeos_objetivo(id) ON DELETE CASCADE,
        FOREIGN KEY (objetivo_normalizado_id) REFERENCES objetivos_normalizados_v2(id)
    )
    """,
    """
    CREATE TABLE terminos_clasificacion (
        id INTEGER PRIMARY KEY,
        version_id INTEGER NOT NULL,
        tipo TEXT NOT NULL CHECK (tipo IN ('FASE', 'PRIORIDAD', 'CONTEXTO', 'FORMATO')),
        nombre TEXT NOT NULL,
        descripcion TEXT,
        UNIQUE (version_id, tipo, nombre),
        FOREIGN KEY (version_id) REFERENCES taxonomia_objetivo_versiones(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE mapeo_objetivo_terminos (
        id INTEGER PRIMARY KEY,
        mapeo_id INTEGER NOT NULL,
        termino_id INTEGER NOT NULL,
        orden INTEGER NOT NULL CHECK (orden > 0),
        UNIQUE (mapeo_id, termino_id),
        UNIQUE (mapeo_id, orden),
        FOREIGN KEY (mapeo_id) REFERENCES mapeos_objetivo(id) ON DELETE CASCADE,
        FOREIGN KEY (termino_id) REFERENCES terminos_clasificacion(id)
    )
    """,
    """
    CREATE TABLE mapeos_objetivo_excepciones (
        id INTEGER PRIMARY KEY,
        version_id INTEGER NOT NULL,
        mapeo_id INTEGER NOT NULL,
        ejercicio_id INTEGER NOT NULL,
        objetivo_origen_id INTEGER NOT NULL,
        tipo_objetivo TEXT NOT NULL,
        objetivo_original_snapshot TEXT NOT NULL,
        contexto TEXT,
        formato TEXT,
        motivo TEXT NOT NULL,
        UNIQUE (version_id, ejercicio_id, objetivo_origen_id, tipo_objetivo),
        FOREIGN KEY (version_id) REFERENCES taxonomia_objetivo_versiones(id) ON DELETE CASCADE,
        FOREIGN KEY (mapeo_id, version_id, objetivo_origen_id)
            REFERENCES mapeos_objetivo(id, version_id, objetivo_origen_id) ON DELETE CASCADE,
        FOREIGN KEY (ejercicio_id, objetivo_origen_id, tipo_objetivo)
            REFERENCES ejercicio_objetivo(ejercicio_id, objetivo_id, tipo_objetivo)
    )
    """,
    """
    CREATE TABLE mapeo_excepcion_destinos (
        id INTEGER PRIMARY KEY,
        excepcion_id INTEGER NOT NULL,
        objetivo_normalizado_id INTEGER NOT NULL,
        orden INTEGER NOT NULL CHECK (orden > 0),
        UNIQUE (excepcion_id, objetivo_normalizado_id),
        UNIQUE (excepcion_id, orden),
        FOREIGN KEY (excepcion_id) REFERENCES mapeos_objetivo_excepciones(id) ON DELETE CASCADE,
        FOREIGN KEY (objetivo_normalizado_id) REFERENCES objetivos_normalizados_v2(id)
    )
    """,
)


def existing_target_tables(conn: sqlite3.Connection) -> set[str]:
    existing = {str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    return existing.intersection(TARGET_TABLES)


def create_schema(conn: sqlite3.Connection) -> None:
    for statement in DDL_STATEMENTS:
        conn.execute(statement)


def load_v2(conn: sqlite3.Connection, prepared: PreparedInputs) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO taxonomia_objetivo_versiones "
        "(id, codigo_version, estado, fecha_creacion, fecha_activacion, motivo, manifiesto_sha256, catalogo_sha256) "
        "VALUES (1, 'V2', 'BORRADOR', ?, NULL, ?, ?, ?)",
        (
            now,
            "Taxonomía V2 auditada; capa aditiva pendiente de activación funcional.",
            MANIFEST_SHA256,
            CATALOG_SHA256,
        ),
    )

    category_ids: dict[str, int] = {}
    for order, code in enumerate(CATEGORY_ORDER, 1):
        category_ids[code] = order
        conn.execute(
            "INSERT INTO categorias_objetivo (id, version_id, codigo, nombre, orden) VALUES (?, 1, ?, ?, ?)",
            (order, code, CATEGORY_NAMES[code], order),
        )

    target_ids: dict[str, int] = {}
    per_category_order: Counter[str] = Counter()
    for target_id, row in enumerate(prepared.catalog, 1):
        target = row["objetivo_destino"]
        category = row["categoria"]
        per_category_order[category] += 1
        target_ids[target] = target_id
        conn.execute(
            "INSERT INTO objetivos_normalizados_v2 "
            "(id, version_id, categoria_id, nombre, orden, activo) VALUES (?, 1, ?, ?, ?, 1)",
            (target_id, category_ids[category], target, per_category_order[category]),
        )

    term_ids: dict[tuple[str, str], int] = {}
    next_term_id = 1
    next_destination_id = 1
    next_mapping_term_id = 1
    next_exception_id = 1
    next_exception_destination_id = 1
    relation_lookup = {
        (item.ejercicio_id, item.objetivo_id, item.tipo_objetivo): item
        for item in prepared.relations
    }

    for row in prepared.manifest:
        source_id = int(row["objetivo_origen_id"])
        conn.execute(
            "INSERT INTO mapeos_objetivo "
            "(id, version_id, objetivo_origen_id, objetivo_origen_snapshot, frecuencia_ejercicios, "
            "frecuencia_relaciones, accion, confianza, estado_decision, decision_entrenador, motivo) "
            "VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                source_id,
                source_id,
                row["objetivo_origen"],
                int(row["frecuencia_ejercicios"]),
                int(row["frecuencia_relaciones"]),
                row["accion"],
                row["confianza"],
                row["estado_revision"],
                row["decision_entrenador"],
                row["motivo"],
            ),
        )

        for order, target in enumerate(prepared.targets_by_source[source_id], 1):
            conn.execute(
                "INSERT INTO mapeo_objetivo_destinos "
                "(id, mapeo_id, objetivo_normalizado_id, orden) VALUES (?, ?, ?, ?)",
                (next_destination_id, source_id, target_ids[target], order),
            )
            next_destination_id += 1

        term_order = 1
        for term_type, field in (("CONTEXTO", "contexto"), ("FORMATO", "formato")):
            term_name = row[field].strip()
            if not term_name:
                continue
            term_key = (term_type, term_name)
            if term_key not in term_ids:
                term_ids[term_key] = next_term_id
                conn.execute(
                    "INSERT INTO terminos_clasificacion "
                    "(id, version_id, tipo, nombre, descripcion) VALUES (?, 1, ?, ?, NULL)",
                    (next_term_id, term_type, term_name),
                )
                next_term_id += 1
            conn.execute(
                "INSERT INTO mapeo_objetivo_terminos (id, mapeo_id, termino_id, orden) VALUES (?, ?, ?, ?)",
                (next_mapping_term_id, source_id, term_ids[term_key], term_order),
            )
            next_mapping_term_id += 1
            term_order += 1

        for exception in prepared.exceptions.get(source_id, []):
            exercise_id = int(exception["ejercicio_id"])
            role = str(exception["tipo_objetivo"])
            relation = relation_lookup[(exercise_id, source_id, role)]
            conn.execute(
                "INSERT INTO mapeos_objetivo_excepciones "
                "(id, version_id, mapeo_id, ejercicio_id, objetivo_origen_id, tipo_objetivo, "
                "objetivo_original_snapshot, contexto, formato, motivo) "
                "VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    next_exception_id,
                    source_id,
                    exercise_id,
                    source_id,
                    role,
                    relation.objetivo_original,
                    str(exception.get("contexto", "")).strip() or None,
                    str(exception.get("formato", "")).strip() or None,
                    str(exception["motivo"]).strip(),
                ),
            )
            for order, destination in enumerate(exception["destinos"], 1):
                target = str(destination["objetivo"])
                conn.execute(
                    "INSERT INTO mapeo_excepcion_destinos "
                    "(id, excepcion_id, objetivo_normalizado_id, orden) VALUES (?, ?, ?, ?)",
                    (next_exception_destination_id, next_exception_id, target_ids[target], order),
                )
                next_exception_destination_id += 1
            next_exception_id += 1


def actual_provenance(conn: sqlite3.Connection) -> list[tuple[int, int, str, str, str]]:
    global_rows = conn.execute(
        "SELECT eo.ejercicio_id, eo.objetivo_id, eo.tipo_objetivo, eo.objetivo_original, onv.nombre "
        "FROM ejercicio_objetivo eo "
        "JOIN mapeos_objetivo mo ON mo.version_id = 1 AND mo.objetivo_origen_id = eo.objetivo_id "
        "JOIN mapeo_objetivo_destinos md ON md.mapeo_id = mo.id "
        "JOIN objetivos_normalizados_v2 onv ON onv.id = md.objetivo_normalizado_id "
        "ORDER BY eo.ejercicio_id, eo.objetivo_id, eo.tipo_objetivo, md.orden"
    ).fetchall()
    exception_rows = conn.execute(
        "SELECT eo.ejercicio_id, eo.objetivo_id, eo.tipo_objetivo, eo.objetivo_original, onv.nombre "
        "FROM ejercicio_objetivo eo "
        "JOIN mapeos_objetivo_excepciones me "
        "ON me.version_id = 1 AND me.ejercicio_id = eo.ejercicio_id "
        "AND me.objetivo_origen_id = eo.objetivo_id AND me.tipo_objetivo = eo.tipo_objetivo "
        "JOIN mapeo_excepcion_destinos med ON med.excepcion_id = me.id "
        "JOIN objetivos_normalizados_v2 onv ON onv.id = med.objetivo_normalizado_id "
        "ORDER BY eo.ejercicio_id, eo.objetivo_id, eo.tipo_objetivo, med.orden"
    ).fetchall()
    return [tuple(row) for row in global_rows + exception_rows]


def validate_loaded(conn: sqlite3.Connection, prepared: PreparedInputs) -> dict[str, Any]:
    version = conn.execute(
        "SELECT codigo_version, estado, fecha_activacion, manifiesto_sha256, catalogo_sha256 "
        "FROM taxonomia_objetivo_versiones"
    ).fetchall()
    require(
        version == [("V2", "BORRADOR", None, MANIFEST_SHA256, CATALOG_SHA256)],
        f"Estado de versión inesperado: {version}",
    )

    counts = {
        "versiones": conn.execute("SELECT COUNT(*) FROM taxonomia_objetivo_versiones").fetchone()[0],
        "categorias": conn.execute("SELECT COUNT(*) FROM categorias_objetivo").fetchone()[0],
        "objetivos_normalizados": conn.execute("SELECT COUNT(*) FROM objetivos_normalizados_v2").fetchone()[0],
        "mapeos": conn.execute("SELECT COUNT(*) FROM mapeos_objetivo").fetchone()[0],
        "destinos_globales": conn.execute("SELECT COUNT(*) FROM mapeo_objetivo_destinos").fetchone()[0],
        "terminos": conn.execute("SELECT COUNT(*) FROM terminos_clasificacion").fetchone()[0],
        "mapeo_terminos": conn.execute("SELECT COUNT(*) FROM mapeo_objetivo_terminos").fetchone()[0],
        "excepciones": conn.execute("SELECT COUNT(*) FROM mapeos_objetivo_excepciones").fetchone()[0],
        "destinos_excepcion": conn.execute("SELECT COUNT(*) FROM mapeo_excepcion_destinos").fetchone()[0],
    }
    require(counts["versiones"] == 1, f"Versiones V2 inesperadas: {counts['versiones']}")
    require(counts["categorias"] == EXPECTED_V2["categorias"], f"Categorías inesperadas: {counts['categorias']}")
    require(counts["objetivos_normalizados"] == EXPECTED_V2["objetivos_normalizados"], "Conteo de objetivos V2 incorrecto")
    require(counts["mapeos"] == EXPECTED_V2["mapeos"], "Conteo de mapeos incorrecto")
    require(counts["excepciones"] == EXPECTED_V2["excepciones"], "Conteo de excepciones incorrecto")

    target_categories = {
        str(row[0]): str(row[1])
        for row in conn.execute(
            "SELECT onv.nombre, c.codigo FROM objetivos_normalizados_v2 onv "
            "JOIN categorias_objetivo c ON c.id = onv.categoria_id"
        )
    }
    require(target_categories == prepared.category_by_target, "El catálogo cargado no coincide con el CSV")

    loaded_mappings = {
        int(row[0]): tuple(row[1:])
        for row in conn.execute(
            "SELECT objetivo_origen_id, objetivo_origen_snapshot, frecuencia_ejercicios, "
            "frecuencia_relaciones, accion, confianza, estado_decision, decision_entrenador, motivo "
            "FROM mapeos_objetivo WHERE version_id = 1"
        )
    }
    expected_mappings = {
        int(row["objetivo_origen_id"]): (
            row["objetivo_origen"],
            int(row["frecuencia_ejercicios"]),
            int(row["frecuencia_relaciones"]),
            row["accion"],
            row["confianza"],
            row["estado_revision"],
            row["decision_entrenador"],
            row["motivo"],
        )
        for row in prepared.manifest
    }
    require(loaded_mappings == expected_mappings, "Los mapeos cargados no reproducen el manifiesto")

    loaded_global_targets: dict[int, tuple[str, ...]] = {}
    for source_id in expected_mappings:
        loaded_global_targets[source_id] = tuple(
            str(row[0])
            for row in conn.execute(
                "SELECT onv.nombre FROM mapeo_objetivo_destinos md "
                "JOIN objetivos_normalizados_v2 onv ON onv.id = md.objetivo_normalizado_id "
                "WHERE md.mapeo_id = ? ORDER BY md.orden",
                (source_id,),
            )
        )
    require(loaded_global_targets == prepared.targets_by_source, "Los destinos globales cargados no coinciden")

    loaded_exception_keys = {
        (int(row[0]), int(row[1]), str(row[2]))
        for row in conn.execute(
            "SELECT objetivo_origen_id, ejercicio_id, tipo_objetivo FROM mapeos_objetivo_excepciones"
        )
    }
    expected_exception_keys = {
        (source_id, int(item["ejercicio_id"]), str(item["tipo_objetivo"]))
        for source_id, items in prepared.exceptions.items()
        for item in items
    }
    require(loaded_exception_keys == expected_exception_keys, "Las excepciones cargadas no coinciden")

    actual = actual_provenance(conn)
    require(Counter(actual) == Counter(prepared.expected_provenance), "La proyección V2 cargada difiere del manifiesto")
    require(len(actual) == len(set(actual)), "Hay destinos duplicados dentro de una misma procedencia")
    semantic_counts = Counter((item[0], item[4]) for item in actual)
    projection = {
        "relaciones_originales_recuperables": conn.execute("SELECT COUNT(*) FROM ejercicio_objetivo").fetchone()[0],
        "relaciones_procedencia": len(actual),
        "pares_semanticos": len(semantic_counts),
        "ejercicios_representados": len({item[0] for item in actual}),
        "grupos_procedencia_multiple": sum(value > 1 for value in semantic_counts.values()),
        "procedencias_adicionales": sum(value - 1 for value in semantic_counts.values()),
        "duplicados_semanticos_internos": len(semantic_counts) - len(set(semantic_counts)),
        "relaciones_solo_contexto_formato": prepared.expected_context_only_relations,
    }
    require(projection["relaciones_originales_recuperables"] == 709, "No se recuperan las 709 relaciones originales")
    require(projection["relaciones_procedencia"] == 747, "La proyección no contiene 747 procedencias")
    require(projection["pares_semanticos"] == 585, "La proyección no contiene 585 pares semánticos")
    require(projection["ejercicios_representados"] == 114, "La proyección no representa 114 ejercicios")
    require(projection["grupos_procedencia_multiple"] == 161, "Grupos de procedencia múltiple inesperados")
    require(projection["duplicados_semanticos_internos"] == 0, "Hay duplicados semánticos internos")

    no_destination_category = conn.execute(
        "SELECT COUNT(*) FROM ("
        "SELECT objetivo_normalizado_id FROM mapeo_objetivo_destinos "
        "UNION ALL SELECT objetivo_normalizado_id FROM mapeo_excepcion_destinos"
        ") d LEFT JOIN objetivos_normalizados_v2 o ON o.id = d.objetivo_normalizado_id "
        "LEFT JOIN categorias_objetivo c ON c.id = o.categoria_id WHERE c.id IS NULL"
    ).fetchone()[0]
    require(no_destination_category == 0, "Hay destinos sin categoría")
    require(not conn.execute("PRAGMA foreign_key_check").fetchall(), "Hay errores de claves foráneas V2")

    return {"counts": counts, "projection": projection, "destinos_sin_categoria": no_destination_category}


def connect_read_only() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH.resolve()}?mode=ro", uri=True)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def precheck() -> dict[str, Any]:
    with connect_read_only() as conn:
        historical = validate_historical(conn)
        prepared = validate_input_files(conn)
        existing = existing_target_tables(conn)
        require(not existing, f"Ya existen tablas V2: {sorted(existing)}")
    return {
        "status": "PRECHECK_OK",
        "sqlite_sha256": physical_hash(),
        "manifest_sha256": sha256_file(MANIFEST_PATH),
        "catalog_sha256": sha256_file(CATALOG_PATH),
        "historical": historical,
        "manifest_rows": len(prepared.manifest),
        "catalog_rows": len(prepared.catalog),
        "expected_provenance": len(prepared.expected_provenance),
        "expected_semantic_pairs": len({(item[0], item[4]) for item in prepared.expected_provenance}),
    }


def migrate() -> dict[str, Any]:
    before_physical = physical_hash()
    conn = sqlite3.connect(DB_PATH)
    conn.isolation_level = None
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    transaction_open = False
    try:
        historical_before = validate_historical(conn)
        prepared = validate_input_files(conn)
        existing = existing_target_tables(conn)
        require(not existing, f"Ya existen tablas V2: {sorted(existing)}")

        conn.execute("BEGIN IMMEDIATE")
        transaction_open = True
        create_schema(conn)
        load_v2(conn, prepared)

        loaded = validate_loaded(conn, prepared)
        historical_inside = validate_historical(conn)
        require(
            historical_inside["logical_hashes"] == historical_before["logical_hashes"],
            "Cambió una firma lógica histórica dentro de la transacción",
        )
        conn.execute("COMMIT")
        transaction_open = False
    except Exception:
        if transaction_open:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()

    with connect_read_only() as check_conn:
        historical_after = validate_historical(check_conn)
        require(
            historical_after["logical_hashes"] == historical_before["logical_hashes"],
            "Cambió una firma lógica histórica después del commit",
        )
        prepared_after = validate_input_files(check_conn)
        loaded_after = validate_loaded(check_conn, prepared_after)

    return {
        "status": "MIGRATION_OK",
        "sqlite_sha256_before": before_physical,
        "sqlite_sha256_after": physical_hash(),
        "manifest_sha256": MANIFEST_SHA256,
        "catalog_sha256": CATALOG_SHA256,
        "logical_hashes_before": historical_before["logical_hashes"],
        "logical_hashes_after": historical_after["logical_hashes"],
        "historical_metrics": historical_after["metrics"],
        "v2": loaded_after,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Valida entradas y estado sin escribir")
    group.add_argument("--apply", action="store_true", help="Crea y carga la capa V2 transaccional")
    args = parser.parse_args(argv)
    try:
        result = precheck() if args.check else migrate()
    except (OSError, sqlite3.Error, ValidationError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "ABORTED", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

