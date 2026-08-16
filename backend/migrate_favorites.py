#!/usr/bin/env python3
"""
Migración idempotente: crea la tabla exercise_favorites si no existe.
Ejecutar una sola vez tras actualizar el código:
    cd backend && source venv/bin/activate && python migrate_favorites.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import engine, Base
from app.models.models import ExerciseFavorite  # noqa: F401 — registers the model

def main():
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("✅ Migración completada: tabla exercise_favorites lista.")

if __name__ == "__main__":
    main()
