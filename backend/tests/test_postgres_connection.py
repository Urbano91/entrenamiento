"""Comprobación de solo lectura sobre la PostgreSQL configurada.

Se omite en la suite SQLite habitual. Para ejecutarla contra Supabase:

    DATABASE_URL='postgresql+psycopg2://...' pytest -q \
        tests/test_postgres_connection.py
"""

import pytest
from sqlalchemy import text

from app.db.database import engine


EXPECTED_COUNTS = {
    "ejercicios": 114,
    "objetivos": 129,
    "entrenamientos": 2,
    "temporadas": 2,
    "partidos": 1,
}


def test_postgres_data_and_relationships_read_only():
    if engine.dialect.name != "postgresql":
        pytest.skip("Requiere DATABASE_URL de PostgreSQL/Supabase")

    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1

        for table_name, expected in EXPECTED_COUNTS.items():
            count = connection.execute(
                text(f'SELECT COUNT(*) FROM "{table_name}"')
            ).scalar_one()
            assert count == expected

        exercise = connection.execute(
            text("SELECT id, nombre FROM ejercicios ORDER BY id LIMIT 1")
        ).mappings().one()
        assert exercise["id"] > 0
        assert exercise["nombre"]

        relationship_counts = {
            "ejercicio_objetivo": 709,
            "ejercicio_imagen": 172,
            "entrenamiento_ejercicios": 4,
        }
        relationship_queries = {
            "ejercicio_objetivo": """
                SELECT COUNT(*)
                FROM ejercicio_objetivo AS relation
                JOIN ejercicios AS exercise ON exercise.id = relation.ejercicio_id
                JOIN objetivos AS objective ON objective.id = relation.objetivo_id
            """,
            "ejercicio_imagen": """
                SELECT COUNT(*)
                FROM ejercicio_imagen AS relation
                JOIN ejercicios AS exercise ON exercise.id = relation.ejercicio_id
                JOIN imagenes AS image ON image.id = relation.imagen_id
            """,
            "entrenamiento_ejercicios": """
                SELECT COUNT(*)
                FROM entrenamiento_ejercicios AS relation
                JOIN entrenamientos AS training
                    ON training.id = relation.entrenamiento_id
                JOIN ejercicios AS exercise ON exercise.id = relation.ejercicio_id
            """,
        }
        for relationship, query in relationship_queries.items():
            count = connection.execute(text(query)).scalar_one()
            assert count == relationship_counts[relationship]
