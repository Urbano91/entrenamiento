#!/usr/bin/env python3
"""Indexa ejercicios de forma reproducible, incremental e idempotente."""

from __future__ import annotations

import sys
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.chdir(ROOT / "backend")

from app.db.database import SessionLocal, engine  # noqa: E402
from app.services.embeddings import get_embedding_provider  # noqa: E402
from app.services.exercise_similarity import (  # noqa: E402
    create_similarity_schema,
    index_all_exercises,
)


def main() -> int:
    if engine.dialect.name != "sqlite":
        raise SystemExit(
            "Este indexador MVP es exclusivamente local para SQLite; no se modificará PostgreSQL/Supabase."
        )
    create_similarity_schema(engine)
    provider = get_embedding_provider()
    db = SessionLocal()
    try:
        stats = index_all_exercises(db, provider)
    finally:
        db.close()
    print(f"Proveedor/modelo: {provider.provider_name}/{provider.model_name}")
    print(f"Ejercicios encontrados: {stats.found}")
    print(f"Embeddings existentes: {stats.existing}")
    print(f"Embeddings generados: {stats.generated}")
    print(f"Embeddings omitidos: {stats.skipped}")
    print(f"Errores: {stats.errors}")
    return 1 if stats.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
