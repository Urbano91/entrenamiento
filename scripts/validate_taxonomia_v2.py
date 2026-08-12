#!/usr/bin/env python3
"""Valida en modo de solo lectura la capa de taxonomía de objetivos V2."""

from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from typing import Any

from migrate_taxonomia_v2 import (
    CATALOG_PATH,
    CATALOG_SHA256,
    DB_PATH,
    EXPECTED_HISTORICAL,
    MANIFEST_PATH,
    MANIFEST_SHA256,
    TARGET_TABLES,
    ValidationError,
    actual_provenance,
    connect_read_only,
    existing_target_tables,
    logical_hashes,
    physical_hash,
    require,
    sha256_file,
    validate_historical,
    validate_input_files,
    validate_loaded,
)


def validate_traceability(conn: sqlite3.Connection, prepared: Any) -> dict[str, int]:
    source_ids = {int(row["objetivo_origen_id"]) for row in prepared.manifest}
    mapped_ids = {
        int(row[0])
        for row in conn.execute(
            "SELECT objetivo_origen_id FROM mapeos_objetivo WHERE version_id = 1"
        )
    }
    require(source_ids == mapped_ids, "La trazabilidad objetivo histórico -> mapeo V2 no es completa")

    targets_from_catalog = set(prepared.category_by_target)
    targets_loaded = {
        str(row[0])
        for row in conn.execute(
            "SELECT nombre FROM objetivos_normalizados_v2 WHERE version_id = 1"
        )
    }
    require(targets_from_catalog == targets_loaded, "La trazabilidad catálogo -> objetivo V2 no es completa")

    targets_with_source = {
        str(row[0])
        for row in conn.execute(
            "SELECT DISTINCT onv.nombre FROM objetivos_normalizados_v2 onv "
            "LEFT JOIN mapeo_objetivo_destinos md ON md.objetivo_normalizado_id = onv.id "
            "LEFT JOIN mapeo_excepcion_destinos med ON med.objetivo_normalizado_id = onv.id "
            "WHERE md.id IS NOT NULL OR med.id IS NOT NULL"
        )
    }
    require(targets_with_source == targets_loaded, "Hay objetivos V2 sin una fuente trazable")

    uncovered_exceptions = conn.execute(
        "SELECT COUNT(*) FROM mapeos_objetivo mo "
        "JOIN ejercicio_objetivo eo ON eo.objetivo_id = mo.objetivo_origen_id "
        "LEFT JOIN mapeos_objetivo_excepciones me "
        "ON me.version_id = mo.version_id AND me.mapeo_id = mo.id "
        "AND me.ejercicio_id = eo.ejercicio_id AND me.objetivo_origen_id = eo.objetivo_id "
        "AND me.tipo_objetivo = eo.tipo_objetivo "
        "WHERE mo.estado_decision = 'EXCEPCION' AND me.id IS NULL"
    ).fetchone()[0]
    require(uncovered_exceptions == 0, "Hay relaciones de fuentes EXCEPCION sin cobertura")

    rows_without_destination_or_term = conn.execute(
        "SELECT COUNT(*) FROM mapeos_objetivo mo "
        "LEFT JOIN mapeo_objetivo_destinos md ON md.mapeo_id = mo.id "
        "LEFT JOIN mapeo_objetivo_terminos mt ON mt.mapeo_id = mo.id "
        "LEFT JOIN mapeos_objetivo_excepciones me ON me.mapeo_id = mo.id "
        "WHERE md.id IS NULL AND mt.id IS NULL AND me.id IS NULL"
    ).fetchone()[0]
    require(rows_without_destination_or_term == 0, "Hay mapeos sin destino, término ni excepción")

    recovered_original_relations = conn.execute(
        "SELECT COUNT(*) FROM ejercicio_objetivo eo "
        "JOIN mapeos_objetivo mo ON mo.version_id = 1 AND mo.objetivo_origen_id = eo.objetivo_id"
    ).fetchone()[0]
    require(recovered_original_relations == 709, "No son recuperables las 709 relaciones históricas")

    return {
        "fuentes_historicas_trazables": len(mapped_ids),
        "destinos_con_fuente": len(targets_with_source),
        "relaciones_originales_recuperables": recovered_original_relations,
        "excepciones_sin_cobertura": uncovered_exceptions,
        "mapeos_sin_salida": rows_without_destination_or_term,
    }


def validate_schema_scope(conn: sqlite3.Connection) -> dict[str, Any]:
    present = existing_target_tables(conn)
    require(present == set(TARGET_TABLES), f"Tablas V2 ausentes: {sorted(set(TARGET_TABLES) - present)}")

    version_columns = {
        str(row[1]) for row in conn.execute("PRAGMA table_info(taxonomia_objetivo_versiones)")
    }
    require(
        {"codigo_version", "estado", "fecha_activacion", "manifiesto_sha256", "catalogo_sha256"}.issubset(version_columns),
        "La tabla de versiones no contiene los campos de control esperados",
    )

    integrity = [str(row[0]) for row in conn.execute("PRAGMA integrity_check")]
    foreign_key_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
    require(integrity == ["ok"], f"PRAGMA integrity_check falló: {integrity}")
    require(not foreign_key_issues, f"Hay {len(foreign_key_issues)} errores de claves foráneas")
    return {
        "tablas_v2": len(present),
        "integrity_check": integrity[0],
        "foreign_key_issues": len(foreign_key_issues),
    }


def validate_taxonomy() -> dict[str, Any]:
    require(sha256_file(MANIFEST_PATH) == MANIFEST_SHA256, "El manifiesto final cambió")
    require(sha256_file(CATALOG_PATH) == CATALOG_SHA256, "El catálogo final cambió")

    with connect_read_only() as conn:
        schema = validate_schema_scope(conn)
        historical = validate_historical(conn)
        prepared = validate_input_files(conn)
        loaded = validate_loaded(conn, prepared)
        traceability = validate_traceability(conn, prepared)

        actions = dict(
            Counter(str(row[0]) for row in conn.execute("SELECT accion FROM mapeos_objetivo"))
        )
        states = dict(
            Counter(str(row[0]) for row in conn.execute("SELECT estado_decision FROM mapeos_objetivo"))
        )
        pending = conn.execute(
            "SELECT COUNT(*) FROM mapeos_objetivo WHERE accion = 'REVISAR' OR estado_decision = 'PENDIENTE'"
        ).fetchone()[0]
        require(pending == 0, "Quedan decisiones REVISAR o PENDIENTE")

        provenance = actual_provenance(conn)
        semantic = {(row[0], row[4]) for row in provenance}
        require(len(semantic) == 585, "La deduplicación semántica no produce 585 pares")
        require(len({row[0] for row in provenance}) == 114, "No están representados los 114 ejercicios")

        final_hashes = logical_hashes(conn)
        require(final_hashes == historical["logical_hashes"], "Las firmas cambiaron durante la validación")

    return {
        "status": "VALIDATION_OK",
        "sqlite": {
            "path": str(DB_PATH.relative_to(DB_PATH.parents[1])),
            "sha256": physical_hash(),
            **schema,
        },
        "inputs": {
            "manifest_sha256": sha256_file(MANIFEST_PATH),
            "catalog_sha256": sha256_file(CATALOG_PATH),
        },
        "historical": {
            **historical["metrics"],
            "logical_hashes": historical["logical_hashes"],
            "expected": EXPECTED_HISTORICAL,
        },
        "v2": loaded,
        "traceability": traceability,
        "actions": actions,
        "states": states,
        "revisar_o_pendiente": pending,
    }


def main() -> int:
    try:
        result = validate_taxonomy()
    except (OSError, sqlite3.Error, ValidationError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "VALIDATION_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

