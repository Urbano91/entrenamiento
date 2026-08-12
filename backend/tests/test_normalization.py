"""Garantías de integridad de la normalización semántica."""

import re
import unicodedata

from sqlalchemy import text

from app.db.database import engine


def _key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def test_no_duplicate_objectives():
    with engine.connect() as connection:
        names = connection.execute(
            text("SELECT nombre_normalizado FROM objetivos")
        ).scalars().all()
    keys = [_key(name) for name in names]
    assert len(keys) == len(set(keys))


def test_no_orphan_exercise_objective_relations():
    with engine.connect() as connection:
        orphan_exercises = connection.execute(text(
            "SELECT COUNT(*) FROM ejercicio_objetivo eo "
            "LEFT JOIN ejercicios e ON e.id=eo.ejercicio_id WHERE e.id IS NULL"
        )).scalar_one()
        orphan_objectives = connection.execute(text(
            "SELECT COUNT(*) FROM ejercicio_objetivo eo "
            "LEFT JOIN objetivos o ON o.id=eo.objetivo_id WHERE o.id IS NULL"
        )).scalar_one()
        unused_objectives = connection.execute(text(
            "SELECT COUNT(*) FROM objetivos o LEFT JOIN ejercicio_objetivo eo "
            "ON eo.objetivo_id=o.id WHERE eo.objetivo_id IS NULL"
        )).scalar_one()
    assert orphan_exercises == 0
    assert orphan_objectives == 0
    assert unused_objectives == 0


def test_normalized_objective_names():
    with engine.connect() as connection:
        names = connection.execute(
            text("SELECT nombre_normalizado FROM objetivos")
        ).scalars().all()
    assert all(name == name.strip() for name in names)
    assert all(not re.search(r"\s{2,}", name) for name in names)
    assert all(not name.startswith(('.', '-')) for name in names)
    assert "Presión" in names
    assert "Finalización" in names


def test_ampitud_mapped_to_amplitud():
    with engine.connect() as connection:
        canonical_id = connection.execute(text(
            "SELECT id FROM objetivos WHERE nombre_normalizado='Amplitud'"
        )).scalar_one()
        typo_count = connection.execute(text(
            "SELECT COUNT(*) FROM objetivos "
            "WHERE lower(nombre_normalizado)='ampitud'"
        )).scalar_one()
        exercise_ids = set(connection.execute(text(
            "SELECT DISTINCT ejercicio_id FROM ejercicio_objetivo "
            "WHERE objetivo_id=:objective_id"
        ), {"objective_id": canonical_id}).scalars().all())
    assert canonical_id == 72
    assert typo_count == 0
    # Unión exacta de los ejercicios vinculados a Amplitud (72) y Ampitud
    # (127) antes de la migración; el ejercicio 67 aparecía en ambos conceptos.
    assert exercise_ids == {34, 67, 75, 85, 92, 99, 100}


def test_exercises_reference_canonical_objectives():
    retired_ids = tuple([
        15, 20, 129, 10, 21, 17, 137, 9, 29, 34, 37, 59, 44, 47,
        77, 18, 43, 83, 48, 89, 133, 139, 103, 121, 70, 64, 75,
        156, 118, 108, 100, 104, 112, 117, 102, 107, 106, 120, 114,
        161, 125, 127, 126, 143, 158, 147, 149, 180, 168, 170, 182, 171, 178,
    ])
    placeholders = ",".join(str(value) for value in retired_ids)
    with engine.connect() as connection:
        retired_relations = connection.execute(text(
            f"SELECT COUNT(*) FROM ejercicio_objetivo WHERE objetivo_id IN ({placeholders})"
        )).scalar_one()
        duplicate_relations = connection.execute(text(
            "SELECT COUNT(*) FROM (SELECT ejercicio_id, objetivo_id, tipo_objetivo, "
            "COUNT(*) AS n FROM ejercicio_objetivo GROUP BY 1,2,3 HAVING n>1)"
        )).scalar_one()
    assert retired_relations == 0
    assert duplicate_relations == 0


def test_sqlite_integrity():
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA integrity_check")).scalar_one() == "ok"
        assert connection.execute(text("PRAGMA foreign_key_check")).first() is None


def test_foreign_keys_enabled():
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1


def test_other_catalogs_have_no_formal_duplicates():
    with engine.connect() as connection:
        values = {
            "tipos_tarea": connection.execute(text("SELECT nombre FROM tipos_tarea")).scalars().all(),
            "espacios": connection.execute(text("SELECT descripcion_original FROM espacios")).scalars().all(),
            "tiempos": connection.execute(text("SELECT descripcion_original FROM tiempos")).scalars().all(),
            "materiales": connection.execute(text("SELECT nombre_normalizado FROM materiales")).scalars().all(),
        }
    for catalog_values in values.values():
        keys = [_key(value) for value in catalog_values]
        assert len(keys) == len(set(keys))


def test_denormalized_objective_fields_match_canonical_relations():
    with engine.connect() as connection:
        mismatches = connection.execute(text(
            "SELECT COUNT(*) FROM ejercicios e WHERE "
            "COALESCE(e.objetivo_1_normalizado, '') <> COALESCE(("
            "SELECT o.nombre_normalizado FROM ejercicio_objetivo eo "
            "JOIN objetivos o ON o.id=eo.objetivo_id "
            "WHERE eo.ejercicio_id=e.id AND eo.tipo_objetivo='principal'"
            "), '') OR COALESCE(e.objetivo_2_normalizado, '') <> COALESCE(("
            "SELECT o.nombre_normalizado FROM ejercicio_objetivo eo "
            "JOIN objetivos o ON o.id=eo.objetivo_id "
            "WHERE eo.ejercicio_id=e.id AND eo.tipo_objetivo='secundario'"
            "), '')"
        )).scalar_one()
    assert mismatches == 0


def test_source_counts_are_preserved():
    with engine.connect() as connection:
        assert connection.execute(text(
            "SELECT COUNT(*) FROM ejercicios e WHERE NOT EXISTS ("
            "SELECT 1 FROM exercise_ownership own WHERE own.ejercicio_id=e.id)"
        )).scalar_one() == 114
        assert connection.execute(text("SELECT COUNT(*) FROM imagenes")).scalar_one() == 122
        assert connection.execute(text("SELECT COUNT(*) FROM texto_original")).scalar_one() == 989
