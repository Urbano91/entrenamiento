#!/usr/bin/env python3
"""Audita y normaliza de forma conservadora la base SQLite de futbol-db.

Por defecto solo genera un informe previo (dry-run). Para aplicar la migración:

    python scripts/normalize_database.py --apply

La ejecución con ``--apply`` crea primero un backup consistente, conserva los
textos originales y valida la integridad antes de confirmar la transacción.
Una segunda ejecución no vuelve a modificar una base ya normalizada.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sqlite3
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "database" / "futbol_entrenamiento.sqlite"
DEFAULT_REPORT = ROOT / "docs" / "database_normalization_report.md"
DEFAULT_OBJECTIVE_CSV = ROOT / "docs" / "normalizacion_objetivos.csv"
DEFAULT_CATALOG_CSV = ROOT / "docs" / "normalizacion_catalogos.csv"


@dataclass(frozen=True)
class Merge:
    source_id: int
    canonical_id: int
    reason: str
    category: str


# Cada equivalencia fue revisada junto con los ejercicios asociados. No se
# incluyen aquí conceptos próximos pero potencialmente distintos.
OBJECTIVE_MERGES = (
    Merge(15, 3, "variante de puntuación", "formato"),
    Merge(20, 4, "variante de puntuación", "formato"),
    Merge(129, 4, "variante de mayúsculas y tilde", "ortografia"),
    Merge(10, 7, "variante de mayúsculas", "formato"),
    Merge(21, 7, "variante de puntuación", "formato"),
    Merge(17, 7, "errata: lines", "ortografia"),
    Merge(137, 7, "errata: cerrrar", "ortografia"),
    Merge(9, 5, "variante ortográfica equivalente", "ortografia"),
    Merge(29, 5, "variante con artículo equivalente", "equivalencia"),
    Merge(34, 5, "variante de puntuación", "formato"),
    Merge(37, 5, "carácter espurio al final", "ortografia"),
    Merge(59, 5, "orden equivalente de control y pase", "equivalencia"),
    Merge(44, 6, "errata: conversación", "ortografia"),
    Merge(47, 6, "errata: convervación", "ortografia"),
    Merge(77, 22, "variante de tilde", "ortografia"),
    Merge(18, 22, "variante sin artículo", "equivalencia"),
    Merge(43, 30, "variante singular/plural", "equivalencia"),
    Merge(83, 39, "variante sin preposición", "equivalencia"),
    Merge(48, 46, "variante singular/plural", "equivalencia"),
    Merge(89, 45, "variante sin tilde", "ortografia"),
    Merge(133, 45, "errata: intercepttación", "ortografia"),
    Merge(139, 58, "variante de mayúsculas", "formato"),
    Merge(103, 61, "variante de mayúsculas", "formato"),
    Merge(121, 61, "variante de puntuación", "formato"),
    Merge(70, 61, "errata: cordinativo", "ortografia"),
    Merge(64, 62, "variante con preposición", "equivalencia"),
    Merge(75, 62, "variante sin preposición", "equivalencia"),
    Merge(156, 82, "variante de mayúsculas", "formato"),
    Merge(118, 91, "puntuación inicial y mayúsculas", "formato"),
    Merge(108, 92, "variante de puntuación", "formato"),
    Merge(100, 93, "variante sin tilde", "ortografia"),
    Merge(104, 93, "variante de mayúsculas", "formato"),
    Merge(112, 93, "variante con preposición", "equivalencia"),
    Merge(117, 93, "errata: trabjo", "ortografia"),
    Merge(102, 95, "variante de mayúsculas", "formato"),
    Merge(107, 97, "variante de mayúsculas", "formato"),
    Merge(106, 99, "variante de mayúsculas", "formato"),
    Merge(120, 109, "variante de puntuación", "formato"),
    Merge(114, 111, "variante sin tilde", "ortografia"),
    Merge(161, 122, "errata en tilde de aéreo", "ortografia"),
    Merge(125, 124, "variante de mayúsculas", "formato"),
    Merge(127, 72, "errata: ampitud", "ortografia"),
    Merge(126, 80, "errata: finañización", "ortografia"),
    Merge(143, 53, "variante singular/plural y tilde", "equivalencia"),
    Merge(158, 162, "errata: basulaciones", "ortografia"),
    Merge(147, 145, "variante de mayúsculas", "formato"),
    Merge(149, 148, "variante de mayúsculas", "formato"),
    Merge(180, 164, "variante de mayúsculas", "formato"),
    Merge(168, 165, "variante de mayúsculas", "formato"),
    Merge(170, 169, "variante de mayúsculas", "formato"),
    Merge(182, 176, "variante de mayúsculas", "formato"),
    Merge(171, 84, "variante singular/plural", "equivalencia"),
    Merge(178, 36, "puntuación inicial redundante", "formato"),
)

SPACE_MERGES = (
    Merge(24, 4, "punto final redundante", "formato"),
    Merge(8, 16, "punto final redundante", "formato"),
    Merge(25, 21, "punto final redundante", "formato"),
    Merge(26, 22, "punto final redundante", "formato"),
    Merge(28, 31, "punto final redundante", "formato"),
)

TIME_MERGES = (
    Merge(9, 1, "variante de mayúsculas", "formato"),
    Merge(3, 2, "variante de mayúsculas", "formato"),
    Merge(8, 4, "variante de mayúsculas", "formato"),
    Merge(25, 17, "variante de mayúsculas", "formato"),
    Merge(23, 20, "variante de mayúsculas", "formato"),
    Merge(27, 24, "variante de mayúsculas", "formato"),
)

MATERIAL_MERGES = (
    Merge(7, 3, "guion inicial redundante", "formato"),
    Merge(4, 5, "punto final redundante", "formato"),
    Merge(8, 6, "variante de mayúsculas", "formato"),
    Merge(20, 16, "errata de mayúsculas en miniporterías", "ortografia"),
    Merge(18, 17, "variante de mayúsculas", "formato"),
    Merge(42, 17, "variante de mayúsculas", "formato"),
    Merge(29, 27, "guion inicial redundante", "formato"),
    Merge(44, 41, "variante de mayúsculas", "formato"),
    Merge(47, 46, "variante de mayúsculas", "formato"),
    Merge(49, 48, "variante de mayúsculas", "formato"),
)


# Representación profesional de los 130 conceptos que quedan. Son cambios de
# presentación/ortografía; no alteran el significado ni los textos originales.
OBJECTIVE_NAMES = {
    1: "Apoyos", 2: "Líneas de pase", 3: "Movilidad sin balón",
    4: "Crear líneas de pase", 5: "Mejora técnica del control y el pase",
    6: "Conservación de balón", 7: "Cerrar líneas de pase",
    8: "Buscar líneas de pase",
    11: "En caso de robo, generar un 3 vs 2 contra miniporterías",
    12: "Progresión", 13: "Si hay robo, juego al lado contrario",
    14: "Pressing", 16: "Robar y progresar", 19: "Sacar de zona",
    22: "Orientación de la presión", 23: "Pases interiores",
    24: "Buscar líneas de pase (sobre todo interiores)",
    25: "Lograr llevar el balón de extremo a extremo",
    26: "Cerrar líneas de pase interiores", 27: "Presión alta",
    28: "Recuperación de balón y juego al más alejado",
    30: "Evitar pases interiores", 31: "Apoyos constantes",
    32: "Robo y juego", 33: "Buscar pases interiores",
    35: "Si robo, juego al triángulo contrario",
    36: "Toma de decisiones",
    38: "Si hay robo, juego a una pareja de fuera", 39: "Cambio de chip",
    40: "Cambio de chip y desplazamiento", 41: "Líneas de pases interiores",
    42: "Robo y juego fuera", 45: "Interceptación",
    46: "Cambio de orientación", 49: "Ocupación racional",
    50: "Pressing tras pérdida", 51: "Sacar de zona tras robo",
    52: "Movilidad", 53: "Basculaciones", 54: "Tercer hombre",
    55: "Técnica", 56: "Comunicación", 57: "Balón de cara",
    58: "Dejar de cara", 60: "Coordinación", 61: "Trabajo coordinativo",
    62: "Inicio de juego", 63: "Colocación", 65: "Pared",
    66: "Mejora técnica del control, el pase y la conducción",
    67: "Control orientado", 68: "Inicio", 69: "Juego",
    71: "Puntería", 72: "Amplitud",
    73: "Aplicación de los movimientos del sistema (1-4-2-3-1)",
    74: "Marcas y coberturas", 76: "Salir jugando", 78: "Ayudas",
    79: "Ocupación de los carriles exteriores", 80: "Finalización",
    81: "Aplicación de la ocupación de los carriles exteriores",
    82: "Juego directo", 84: "Despeje", 85: "Temporización",
    86: "Repliegue", 87: "Dividir", 88: "Desmarques",
    90: "Fuerza preventiva", 91: "Trabajo preventivo",
    92: "Mejora técnica del pase", 93: "Trabajo de propiocepción",
    94: "Fuerza", 95: "Fuerza del tren superior", 96: "Core",
    97: "Trabajo de tren superior", 98: "Fuerza explosiva",
    99: "Trabajo de fuerza explosiva", 101: "Fuerza resistencia",
    105: "Trabajo de fuerza resistencia", 109: "Resistencia aeróbica",
    110: "Posesión", 111: "Trabajo de resistencia aeróbica",
    113: "Trabajo de coordinación", 115: "Velocidad",
    116: "Trabajo de velocidad",
    119: "Mejora técnica del control y el tiro", 122: "Juego aéreo",
    123: "Marcajes", 124: "Balón aéreo", 128: "Desmarque de ruptura",
    130: "Presión", 131: "Cambio de dirección",
    132: "Presión en campo contrario", 134: "Robo y cambio de zona",
    135: "Superar línea defensiva", 136: "Tapar pases interiores",
    138: "Aplicación del sistema 1-4-4-2", 140: "Asignación de marcas",
    141: "Agrupar gente", 142: "Acumulación de gente",
    144: "Escalonamiento", 145: "Organización ofensiva",
    146: "Transiciones", 148: "Organización defensiva",
    150: "Buscar balón a la espalda de la defensa",
    151: "Ayudas defensivas", 152: "Defensa de centro", 153: "1 vs 1",
    154: "Disputa", 155: "Juego real", 157: "Jugar por fuera",
    159: "Regate", 160: "Ataque por centro lateral",
    162: "Marcajes y basculaciones", 163: "Vigilancias",
    164: "Remate de cabeza", 165: "Despeje orientado",
    166: "Anticipación", 167: "Marcas", 169: "Defensa en zona",
    172: "Defensa combinada", 173: "Activación",
    174: "Asignación de tareas", 175: "Velocidad de reacción",
    176: "Trabajo de velocidad de reacción",
    177: "Trabajo de velocidad de desplazamiento",
    179: "Trabajo técnico", 181: "Equilibrio",
}

AMBIGUOUS_CASES = (
    "Pressing ↔ Presión",
    "Pressing tras pérdida ↔ Presión / Presión alta",
    "Conservación de balón ↔ Posesión",
    "Marcajes ↔ Marcas",
    "Crear / Buscar / Cerrar líneas de pase",
    "Cerrar líneas de pase interiores ↔ Tapar / Evitar pases interiores",
    "Coordinación ↔ Trabajo coordinativo ↔ Trabajo de coordinación",
    "Fuerza explosiva ↔ Trabajo de fuerza explosiva",
    "Fuerza resistencia ↔ Trabajo de fuerza resistencia",
    "Fuerza preventiva ↔ Trabajo preventivo",
    "Velocidad de reacción ↔ Trabajo de velocidad de reacción",
    "Técnica ↔ Trabajo técnico",
    "Juego aéreo ↔ Balón aéreo ↔ Remate de cabeza",
    "Inicio ↔ Inicio de juego",
    "Marcajes y basculaciones ↔ Marcajes / Basculaciones por separado",
    "Materiales con las mismas palabras pero distinto orden o conjunción",
    "Ejercicio ABP3: nombre normalizado ofensivo y nombre original defensivo",
)


def comparison_key(value: str) -> str:
    """Clave estricta para detectar duplicados ortográficos/formales."""
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def table_count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def image_manifest(conn: sqlite3.Connection) -> str:
    digest = hashlib.sha256()
    for row in conn.execute(
        "SELECT id, archivo, sha256, width, height FROM imagenes ORDER BY id"
    ):
        digest.update("\x1f".join("" if v is None else str(v) for v in row).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def snapshot(conn: sqlite3.Connection) -> dict[str, int | str]:
    return {
        "ejercicios": table_count(conn, "ejercicios"),
        "objetivos": table_count(conn, "objetivos"),
        "relaciones_objetivo": table_count(conn, "ejercicio_objetivo"),
        "tipos_tarea": table_count(conn, "tipos_tarea"),
        "espacios": table_count(conn, "espacios"),
        "tiempos": table_count(conn, "tiempos"),
        "materiales": table_count(conn, "materiales"),
        "imagenes": table_count(conn, "imagenes"),
        "texto_original": table_count(conn, "texto_original"),
        "manifest_imagenes": image_manifest(conn),
    }


def names_by_id(conn: sqlite3.Connection, table: str, column: str) -> dict[int, str]:
    return dict(conn.execute(f"SELECT id, {column} FROM {table}"))


def source_relation_counts(
    conn: sqlite3.Connection, relation_table: str, foreign_column: str,
    merges: Iterable[Merge],
) -> dict[int, int]:
    result: dict[int, int] = {}
    for merge in merges:
        result[merge.source_id] = conn.execute(
            f"SELECT COUNT(DISTINCT ejercicio_id) FROM {relation_table} "
            f"WHERE {foreign_column} = ?", (merge.source_id,),
        ).fetchone()[0]
    return result


def pending_changes(conn: sqlite3.Connection) -> bool:
    specs = (
        ("objetivos", OBJECTIVE_MERGES), ("espacios", SPACE_MERGES),
        ("tiempos", TIME_MERGES), ("materiales", MATERIAL_MERGES),
    )
    catalogs_pending = any(
        conn.execute(
            f"SELECT EXISTS(SELECT 1 FROM {table} WHERE id=?)", (merge.source_id,)
        ).fetchone()[0]
        for table, merges in specs for merge in merges
    )
    names_pending = any(
        conn.execute(
            "SELECT EXISTS(SELECT 1 FROM objetivos WHERE id=? AND nombre_normalizado<>?)",
            item,
        ).fetchone()[0]
        for item in OBJECTIVE_NAMES.items()
    )
    material_names_pending = any(
        normalize_material_name(name) != name
        for name, in conn.execute("SELECT nombre_normalizado FROM materiales")
    )
    exercise_names_pending = any(
        normalize_exercise_name(name) != name
        for name, in conn.execute("SELECT nombre FROM ejercicios")
    )
    return (
        catalogs_pending or names_pending or material_names_pending
        or exercise_names_pending
    )


def validate_preconditions(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise RuntimeError("SQLite foreign_keys no está activado")
    if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise RuntimeError("La base de datos no supera PRAGMA integrity_check")
    expected = {m.canonical_id for m in OBJECTIVE_MERGES}
    existing = {row[0] for row in conn.execute("SELECT id FROM objetivos")}
    missing = expected - existing
    if missing:
        raise RuntimeError(f"Faltan objetivos canónicos: {sorted(missing)}")


def assert_no_merge_collisions(conn: sqlite3.Connection) -> None:
    for merge in OBJECTIVE_MERGES:
        collision = conn.execute(
            "SELECT COUNT(*) FROM ejercicio_objetivo src "
            "JOIN ejercicio_objetivo dst "
            "ON dst.ejercicio_id=src.ejercicio_id "
            "AND dst.tipo_objetivo=src.tipo_objetivo "
            "AND dst.objetivo_id=? "
            "WHERE src.objetivo_id=?",
            (merge.canonical_id, merge.source_id),
        ).fetchone()[0]
        if collision:
            raise RuntimeError(
                f"La fusión de objetivo {merge.source_id} en {merge.canonical_id} "
                f"colisionaría en {collision} relaciones"
            )
    for merge in MATERIAL_MERGES:
        collision = conn.execute(
            "SELECT COUNT(*) FROM ejercicio_material src "
            "JOIN ejercicio_material dst ON dst.ejercicio_id=src.ejercicio_id "
            "AND dst.material_id=? WHERE src.material_id=?",
            (merge.canonical_id, merge.source_id),
        ).fetchone()[0]
        if collision:
            raise RuntimeError(
                f"La fusión de material {merge.source_id} en {merge.canonical_id} "
                f"colisionaría en {collision} relaciones"
            )


def merge_objectives(conn: sqlite3.Connection) -> int:
    changed = 0
    for merge in OBJECTIVE_MERGES:
        if not conn.execute(
            "SELECT 1 FROM objetivos WHERE id=?", (merge.source_id,)
        ).fetchone():
            continue
        relations = conn.execute(
            "SELECT ejercicio_id, tipo_objetivo, objetivo_original "
            "FROM ejercicio_objetivo WHERE objetivo_id=?",
            (merge.source_id,),
        ).fetchall()
        for ejercicio_id, tipo, original in relations:
            conn.execute(
                "INSERT INTO ejercicio_objetivo "
                "(ejercicio_id, objetivo_id, tipo_objetivo, objetivo_original) "
                "VALUES (?, ?, ?, ?)",
                (ejercicio_id, merge.canonical_id, tipo, original),
            )
        conn.execute("DELETE FROM ejercicio_objetivo WHERE objetivo_id=?", (merge.source_id,))
        conn.execute("DELETE FROM objetivos WHERE id=?", (merge.source_id,))
        changed += len(relations)
    return changed


def merge_simple_catalog(
    conn: sqlite3.Connection, merges: Iterable[Merge], table: str,
    reference_table: str, foreign_column: str,
) -> int:
    changed = 0
    for merge in merges:
        if not conn.execute(
            f"SELECT 1 FROM {table} WHERE id=?", (merge.source_id,)
        ).fetchone():
            continue
        cursor = conn.execute(
            f"UPDATE {reference_table} SET {foreign_column}=? WHERE {foreign_column}=?",
            (merge.canonical_id, merge.source_id),
        )
        changed += cursor.rowcount
        conn.execute(f"DELETE FROM {table} WHERE id=?", (merge.source_id,))
    return changed


def merge_materials(conn: sqlite3.Connection) -> int:
    changed = 0
    for merge in MATERIAL_MERGES:
        if not conn.execute(
            "SELECT 1 FROM materiales WHERE id=?", (merge.source_id,)
        ).fetchone():
            continue
        rows = conn.execute(
            "SELECT ejercicio_id, material_original FROM ejercicio_material "
            "WHERE material_id=?", (merge.source_id,),
        ).fetchall()
        for ejercicio_id, original in rows:
            conn.execute(
                "INSERT INTO ejercicio_material "
                "(ejercicio_id, material_id, material_original) VALUES (?, ?, ?)",
                (ejercicio_id, merge.canonical_id, original),
            )
        conn.execute("DELETE FROM ejercicio_material WHERE material_id=?", (merge.source_id,))
        conn.execute("DELETE FROM materiales WHERE id=?", (merge.source_id,))
        changed += len(rows)
    return changed


def normalize_exercise_name(name: str) -> str:
    replacements = (
        (r"\bProgresion\b", "Progresión"),
        (r"\bprogresion\b", "progresión"),
        (r"\bTriangulo\b", "Triángulo"),
        (r"\btriangulo\b", "triángulo"),
        (r"\bHexagono\b", "Hexágono"),
        (r"\bhexagono\b", "hexágono"),
        (r"\bTransicion\b", "Transición"),
        (r"\btransicion\b", "transición"),
        (r"\bPorterias\b", "Porterías"),
        (r"\bporterias\b", "porterías"),
        (r"\bPorteria\b", "Portería"),
        (r"\bporteria\b", "portería"),
        (r"\bLinea\b", "Línea"),
        (r"\blinea\b", "línea"),
        (r"\bComodin\b", "Comodín"),
        (r"\bcomodin\b", "comodín"),
        (r"\bDoble Area\b", "Doble área"),
    )
    result = re.sub(r"\s+", " ", name).strip()
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result)
    result = re.sub(r"(?<=\d)\s*vs\s*(?=\d)", " vs ", result, flags=re.IGNORECASE)
    result = re.sub(r"\s*\bvs\b\s*", " vs ", result, flags=re.IGNORECASE)
    result = re.sub(r"\s*\+\s*", " + ", result)
    return re.sub(r"\s+", " ", result).strip()


def normalize_material_name(name: str) -> str:
    """Corrige únicamente forma, tildes y erratas mecánicas de materiales."""
    result = re.sub(r"^\s*-\s*", "", name)
    result = re.sub(r"\s*\.\s*$", "", result)
    result = re.sub(r"(?i)\bmini?pot(?:er)?ias\b", "Miniporterías", result)
    result = re.sub(r"(?i)\bmimiporterias\b", "Miniporterías", result)
    result = re.sub(r"(?i)\bminiporterias\b", "Miniporterías", result)
    result = re.sub(r"(?i)\bporteria\b", "Portería", result)
    result = re.sub(r"(?i)\bporterias\b", "Porterías", result)
    result = re.sub(r"(?i)\bchinos\b", "chinos", result)
    result = re.sub(r"(?i)\bsetas planas\b", "Setas planas", result)
    result = re.sub(r"(?i)\bpetos\b", "Petos", result)
    result = re.sub(r"(?i)\bbalones\b", "Balones", result)
    result = re.sub(r"(?i)\belastica\b", "elástica", result)
    result = re.sub(r"(?i)\bporta auxiliar\b", "Portería auxiliar", result)
    result = re.sub(r"(?i)\bporteria auxiliar\b", "Portería auxiliar", result)
    result = re.sub(r"(?i)\bporteria movil\b", "Portería móvil", result)
    result = re.sub(r"(?i)\bportería auxiliar\b", "Portería auxiliar", result)
    result = re.sub(r"(?i)\bportería movil\b", "Portería móvil", result)
    result = re.sub(r"(?i)\barnes\b", "arnés", result)
    result = re.sub(r"(?i)\bbalon\b", "balón", result)
    result = re.sub(r"(?i)\bbanderin\b", "Banderín", result)
    result = re.sub(r"(?i)\bminiporterías\b", "Miniporterías", result)
    result = re.sub(r"(?i)\bplanas8\b", "planas 8", result)
    return re.sub(r"\s+", " ", result).strip()


def normalize_display_values(conn: sqlite3.Connection) -> tuple[int, int, int]:
    objective_names_changed = 0
    for objective_id, name in OBJECTIVE_NAMES.items():
        cursor = conn.execute(
            "UPDATE objetivos SET nombre_normalizado=? "
            "WHERE id=? AND nombre_normalizado<>?", (name, objective_id, name)
        )
        objective_names_changed += cursor.rowcount
    material_names_changed = 0
    for material_id, name in conn.execute(
        "SELECT id, nombre_normalizado FROM materiales"
    ).fetchall():
        normalized = normalize_material_name(name)
        if normalized != name:
            conn.execute(
                "UPDATE materiales SET nombre_normalizado=? WHERE id=?",
                (normalized, material_id),
            )
            material_names_changed += 1
    exercise_names_changed = 0
    for exercise_id, name in conn.execute("SELECT id, nombre FROM ejercicios").fetchall():
        normalized = normalize_exercise_name(name)
        if normalized != name:
            conn.execute("UPDATE ejercicios SET nombre=? WHERE id=?", (normalized, exercise_id))
            exercise_names_changed += 1
    return objective_names_changed, material_names_changed, exercise_names_changed


def refresh_denormalized_objectives(conn: sqlite3.Connection) -> int:
    changed = 0
    for exercise_id in (row[0] for row in conn.execute("SELECT id FROM ejercicios")):
        values = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT eo.tipo_objetivo, o.nombre_normalizado "
                "FROM ejercicio_objetivo eo JOIN objetivos o ON o.id=eo.objetivo_id "
                "WHERE eo.ejercicio_id=? AND eo.tipo_objetivo IN ('principal','secundario')",
                (exercise_id,),
            )
        }
        principal = values.get("principal")
        secondary = values.get("secundario")
        current = conn.execute(
            "SELECT objetivo_1_normalizado, objetivo_2_normalizado "
            "FROM ejercicios WHERE id=?", (exercise_id,),
        ).fetchone()
        if current != (principal, secondary):
            conn.execute(
                "UPDATE ejercicios SET objetivo_1_normalizado=?, "
                "objetivo_2_normalizado=? WHERE id=?",
                (principal, secondary, exercise_id),
            )
            changed += 1
    return changed


def validate_result(conn: sqlite3.Connection, before: dict[str, int | str]) -> None:
    checks = {
        "integrity_check": conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok",
        "foreign_keys": conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1,
        "foreign_key_check": conn.execute("PRAGMA foreign_key_check").fetchone() is None,
        "ejercicios_114": table_count(conn, "ejercicios") == 114,
        "imagenes_122": table_count(conn, "imagenes") == 122,
        "imagenes_intactas": image_manifest(conn) == before["manifest_imagenes"],
        "sin_relaciones_objetivo_duplicadas": conn.execute(
            "SELECT COUNT(*) FROM (SELECT ejercicio_id, objetivo_id, tipo_objetivo, "
            "COUNT(*) c FROM ejercicio_objetivo GROUP BY 1,2,3 HAVING c>1)"
        ).fetchone()[0] == 0,
        "sin_objetivos_huerfanos": conn.execute(
            "SELECT COUNT(*) FROM objetivos o LEFT JOIN ejercicio_objetivo eo "
            "ON eo.objetivo_id=o.id WHERE eo.objetivo_id IS NULL"
        ).fetchone()[0] == 0,
        "sin_objetivos_fuente": all(
            not conn.execute("SELECT 1 FROM objetivos WHERE id=?", (m.source_id,)).fetchone()
            for m in OBJECTIVE_MERGES
        ),
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise RuntimeError("Validación final fallida: " + ", ".join(failed))


def write_objective_csv(
    path: Path, names: dict[int, str], counts: dict[int, int]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow((
            "original_id", "original_nombre", "canonical_id", "canonical_nombre",
            "motivo", "categoria", "ejercicios_afectados",
        ))
        for merge in OBJECTIVE_MERGES:
            writer.writerow((
                merge.source_id, names.get(merge.source_id, "[ya unificado]"),
                merge.canonical_id,
                OBJECTIVE_NAMES.get(merge.canonical_id, names.get(merge.canonical_id, "")),
                merge.reason, merge.category, counts.get(merge.source_id, 0),
            ))


def write_catalog_csv(
    path: Path, catalog_names: dict[str, dict[int, str]],
    catalog_counts: dict[str, dict[int, int]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    specs = (
        ("espacios", SPACE_MERGES), ("tiempos", TIME_MERGES),
        ("materiales", MATERIAL_MERGES),
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow((
            "catalogo", "original_id", "original_nombre", "canonical_id",
            "canonical_nombre", "motivo", "ejercicios_afectados",
        ))
        for catalog, merges in specs:
            names = catalog_names[catalog]
            for merge in merges:
                canonical_name = names.get(merge.canonical_id, "")
                if catalog == "materiales":
                    canonical_name = normalize_material_name(canonical_name)
                writer.writerow((
                    catalog, merge.source_id,
                    names.get(merge.source_id, "[ya unificado]"),
                    merge.canonical_id, canonical_name, merge.reason,
                    catalog_counts[catalog].get(merge.source_id, 0),
                ))


def write_report(
    path: Path, before: dict[str, int | str], after: dict[str, int | str],
    objective_names: dict[int, str], objective_counts: dict[int, int],
    stats: dict[str, int], applied: bool, backup_path: Path | None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    affected_exercises = stats["affected_exercises"]
    spellings = sum(m.category == "ortografia" for m in OBJECTIVE_MERGES)
    lines = [
        "# Informe de normalización de la base de datos",
        "",
        f"Estado: **{'APLICADO Y VALIDADO' if applied else 'INFORME PREVIO — SIN MODIFICAR LA BASE'}**",
        "",
        "## Resumen",
        "",
        "| Métrica | Antes | Después |",
        "|---|---:|---:|",
        f"| Ejercicios | {before['ejercicios']} | {after['ejercicios']} |",
        f"| Objetivos | {before['objetivos']} | {after['objetivos']} |",
        f"| Relaciones ejercicio-objetivo | {before['relaciones_objetivo']} | {after['relaciones_objetivo']} |",
        f"| Tipos de tarea | {before['tipos_tarea']} | {after['tipos_tarea']} |",
        f"| Espacios | {before['espacios']} | {after['espacios']} |",
        f"| Tiempos | {before['tiempos']} | {after['tiempos']} |",
        f"| Materiales | {before['materiales']} | {after['materiales']} |",
        f"| Imágenes | {before['imagenes']} | {after['imagenes']} |",
        f"| Texto original | {before['texto_original']} | {after['texto_original']} |",
        "",
        f"- Variantes duplicadas de objetivos detectadas: **{len(OBJECTIVE_MERGES)}**.",
        f"- Variantes de objetivo clasificadas como errores ortográficos: **{spellings}**.",
        f"- Ejercicios distintos afectados por fusiones de objetivos: **{affected_exercises}**.",
        f"- Relaciones ejercicio-objetivo reasignadas: **{stats['objective_relations']}**.",
        f"- Objetivos redundantes unificados/eliminados: **{stats['objectives_removed']}**.",
        f"- Variantes redundantes en el resto de catálogos: **{len(SPACE_MERGES) + len(TIME_MERGES) + len(MATERIAL_MERGES)}** "
        f"({len(SPACE_MERGES)} espacios, {len(TIME_MERGES)} tiempos y {len(MATERIAL_MERGES)} materiales).",
        f"- Referencias reasignadas en espacios/tiempos/materiales: "
        f"**{stats['space_references']} / {stats['time_references']} / {stats['material_relations']}**.",
        f"- Nombres de objetivos ajustados para presentación: **{stats['objective_names_changed']}**.",
        f"- Nombres de materiales corregidos ortográfica/formalmente: **{stats['material_names_changed']}**.",
        f"- Nombres de ejercicios corregidos ortográficamente: **{stats['exercise_names_changed']}**.",
        f"- Casos ambiguos no modificados: **{len(AMBIGUOUS_CASES)}**.",
        "- `texto_original`, `nombre_original`, objetivos originales y materiales originales se conservaron.",
        "- No se detectaron duplicados en tipos de tarea ni en nombres normalizados de ejercicios.",
        "",
        "## Normalizaciones de objetivos",
        "",
        "| ID original | Original | ID canónico | Canónico | Motivo | Ejercicios |",
        "|---:|---|---:|---|---|---:|",
    ]
    for merge in OBJECTIVE_MERGES:
        original = objective_names.get(merge.source_id, "[ya unificado]").replace("|", "\\|")
        canonical = OBJECTIVE_NAMES.get(
            merge.canonical_id, objective_names.get(merge.canonical_id, "")
        ).replace("|", "\\|")
        lines.append(
            f"| {merge.source_id} | {original} | {merge.canonical_id} | "
            f"{canonical} | {merge.reason} | {objective_counts.get(merge.source_id, 0)} |"
        )
    lines.extend((
        "", "## Casos ambiguos no modificados", "",
        *[f"- {case}" for case in AMBIGUOUS_CASES],
        "", "## Integridad y trazabilidad", "",
        f"- `PRAGMA integrity_check`: **{'ok' if applied else 'pendiente de aplicación (ok en auditoría previa)'}**.",
        f"- Claves foráneas: **{'activadas y verificadas' if applied else 'se activarán durante la migración'}**.",
        f"- Backup: `{backup_path if backup_path else 'se creará antes de aplicar'}`.",
        f"- Mapeo completo de objetivos: `{DEFAULT_OBJECTIVE_CSV.relative_to(ROOT)}`.",
        f"- Mapeo de espacios, tiempos y materiales: `{DEFAULT_CATALOG_CSV.relative_to(ROOT)}`.",
        "", "## Criterios conservadores", "",
        "Solo se fusionaron diferencias mecánicas, erratas inequívocas y variantes "
        "cuya equivalencia fue confirmada con sus ejercicios asociados. Los conceptos "
        "que podrían expresar matices tácticos diferentes permanecen separados. La "
        "búsqueda semántica debe usar `objetivos.id` y `ejercicio_objetivo`, no `LIKE`.",
        "",
    ))
    path.write_text("\n".join(lines), encoding="utf-8")


def predicted_after(before: dict[str, int | str]) -> dict[str, int | str]:
    result = dict(before)
    result["objetivos"] = int(before["objetivos"]) - len(OBJECTIVE_MERGES)
    result["espacios"] = int(before["espacios"]) - len(SPACE_MERGES)
    result["tiempos"] = int(before["tiempos"]) - len(TIME_MERGES)
    result["materiales"] = int(before["materiales"]) - len(MATERIAL_MERGES)
    return result


def create_backup_locked(conn: sqlite3.Connection, database: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup = database.with_name(
        f"{database.name}.bak-before-normalization-{stamp}"
    )
    if backup.exists():
        raise RuntimeError(f"El backup ya existe: {backup}")
    source = sqlite3.connect(database)
    destination = sqlite3.connect(backup)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()
    check = sqlite3.connect(f"file:{backup}?mode=ro", uri=True)
    try:
        if check.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            backup.unlink(missing_ok=True)
            raise RuntimeError("El backup no supera PRAGMA integrity_check")
    finally:
        check.close()
    return backup


def run(database: Path, apply: bool) -> int:
    if not database.is_file():
        raise FileNotFoundError(database)
    conn = sqlite3.connect(database, isolation_level=None)
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        validate_preconditions(conn)
        before = snapshot(conn)
        objective_names = names_by_id(conn, "objetivos", "nombre_normalizado")
        catalog_names = {
            "espacios": names_by_id(conn, "espacios", "descripcion_original"),
            "tiempos": names_by_id(conn, "tiempos", "descripcion_original"),
            "materiales": names_by_id(conn, "materiales", "nombre_normalizado"),
        }
        objective_counts = source_relation_counts(
            conn, "ejercicio_objetivo", "objetivo_id", OBJECTIVE_MERGES
        )
        catalog_counts = {
            "espacios": {
                m.source_id: conn.execute(
                    "SELECT COUNT(*) FROM ejercicios WHERE espacio_id=?", (m.source_id,)
                ).fetchone()[0] for m in SPACE_MERGES
            },
            "tiempos": {
                m.source_id: conn.execute(
                    "SELECT COUNT(*) FROM ejercicios WHERE tiempo_id=?", (m.source_id,)
                ).fetchone()[0] for m in TIME_MERGES
            },
            "materiales": source_relation_counts(
                conn, "ejercicio_material", "material_id", MATERIAL_MERGES
            ),
        }
        affected_ids: set[int] = set()
        for merge in OBJECTIVE_MERGES:
            affected_ids.update(row[0] for row in conn.execute(
                "SELECT ejercicio_id FROM ejercicio_objetivo WHERE objetivo_id=?",
                (merge.source_id,),
            ))
        preview_stats = {
            "affected_exercises": len(affected_ids),
            "objective_relations": sum(objective_counts.values()),
            "objectives_removed": sum(m.source_id in objective_names for m in OBJECTIVE_MERGES),
            "objective_names_changed": sum(
                objective_names.get(i) not in (None, name) for i, name in OBJECTIVE_NAMES.items()
            ),
            "material_names_changed": sum(
                material_id not in {m.source_id for m in MATERIAL_MERGES}
                and normalize_material_name(name) != name
                for material_id, name in conn.execute(
                    "SELECT id, nombre_normalizado FROM materiales"
                )
            ),
            "exercise_names_changed": sum(
                normalize_exercise_name(name) != name
                for name, in conn.execute("SELECT nombre FROM ejercicios")
            ),
            "space_references": sum(catalog_counts["espacios"].values()),
            "time_references": sum(catalog_counts["tiempos"].values()),
            "material_relations": sum(catalog_counts["materiales"].values()),
        }
        is_pending = pending_changes(conn)
        if not is_pending:
            print("La base ya está normalizada; no se modificaron datos ni informes.")
            return 0
        write_objective_csv(DEFAULT_OBJECTIVE_CSV, objective_names, objective_counts)
        write_catalog_csv(DEFAULT_CATALOG_CSV, catalog_names, catalog_counts)
        write_report(
            DEFAULT_REPORT, before, predicted_after(before), objective_names,
            objective_counts, preview_stats, False, None,
        )
        if not apply:
            print(f"Auditoría previa generada: {DEFAULT_REPORT}")
            print(f"Objetivos: {before['objetivos']} -> {predicted_after(before)['objetivos']}")
            print(f"Ejercicios afectados: {len(affected_ids)}")
            print("Base de datos no modificada (use --apply para aplicar).")
            return 0
        assert_no_merge_collisions(conn)
        conn.execute("BEGIN IMMEDIATE")
        backup_path: Path | None = None
        try:
            backup_path = create_backup_locked(conn, database)
            objective_relations = merge_objectives(conn)
            space_references = merge_simple_catalog(
                conn, SPACE_MERGES, "espacios", "ejercicios", "espacio_id"
            )
            time_references = merge_simple_catalog(
                conn, TIME_MERGES, "tiempos", "ejercicios", "tiempo_id"
            )
            material_relations = merge_materials(conn)
            objective_names_changed, material_names_changed, exercise_names_changed = normalize_display_values(conn)
            refresh_denormalized_objectives(conn)
            after = snapshot(conn)
            validate_result(conn, before)
            conn.execute("COMMIT")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        final_stats = {
            "affected_exercises": len(affected_ids),
            "objective_relations": objective_relations,
            "objectives_removed": int(before["objetivos"]) - int(after["objetivos"]),
            "objective_names_changed": objective_names_changed,
            "material_names_changed": material_names_changed,
            "exercise_names_changed": exercise_names_changed,
            "space_references": space_references,
            "time_references": time_references,
            "material_relations": material_relations,
        }
        write_report(
            DEFAULT_REPORT, before, after, objective_names, objective_counts,
            final_stats, True, backup_path,
        )
        print(f"Backup: {backup_path}")
        print(f"Informe final: {DEFAULT_REPORT}")
        print(f"Objetivos: {before['objetivos']} -> {after['objetivos']}")
        print(f"Relaciones reasignadas: {objective_relations}")
        print("PRAGMA integrity_check: ok")
        return 0
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument(
        "--apply", action="store_true",
        help="crear backup y aplicar la migración (sin esta opción solo audita)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        arguments = parse_args()
        raise SystemExit(run(arguments.database.resolve(), arguments.apply))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
