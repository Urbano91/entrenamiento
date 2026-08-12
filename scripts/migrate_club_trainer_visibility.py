"""Añade de forma idempotente la visibilidad del entrenador dentro de cada club."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = f"sqlite:///{ROOT / 'database' / 'futbol_entrenamiento.sqlite'}"


def main() -> None:
    database_url = os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
    engine = create_engine(database_url)
    if engine.dialect.name != "sqlite":
        raise RuntimeError("Esta migración local solo está autorizada para SQLite")
    columns = {column["name"] for column in inspect(engine).get_columns("coach_assignments")}
    if "visible_in_club" in columns:
        print("coach_assignments.visible_in_club ya existe")
        return
    with engine.begin() as connection:
        connection.execute(text(
            "ALTER TABLE coach_assignments "
            "ADD COLUMN visible_in_club BOOLEAN NOT NULL DEFAULT 1"
        ))
    print("coach_assignments.visible_in_club añadido correctamente")


if __name__ == "__main__":
    main()
