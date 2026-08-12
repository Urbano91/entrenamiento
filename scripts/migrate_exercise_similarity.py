#!/usr/bin/env python3
"""Crea únicamente las tablas aditivas de similitud de ejercicios."""

from __future__ import annotations

import sys
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.chdir(ROOT / "backend")

from app.db.database import engine  # noqa: E402
from app.services.exercise_similarity import create_similarity_schema  # noqa: E402


def main() -> None:
    if engine.dialect.name != "sqlite":
        raise SystemExit(
            "Este migrador es exclusivamente local para SQLite; no se modificará PostgreSQL/Supabase."
        )
    create_similarity_schema(engine)
    print("Esquema aditivo de similitud verificado.")


if __name__ == "__main__":
    main()
