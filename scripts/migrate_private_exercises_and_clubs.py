#!/usr/bin/env python3
"""Instala de forma aditiva identidad, clubes y propiedad de ejercicios."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.chdir(ROOT / "backend")

from app.db.database import SessionLocal, engine  # noqa: E402
from app.models.models import (  # noqa: E402
    Club,
    CoachAssignment,
    ExerciseOwnership,
    ExerciseRelation,
    SportsCategory,
    UserAccount,
    Usuario,
    PerfilEntrenador,
)


OFFICIAL_EXERCISE_MAX_ID = 114


def main() -> None:
    if engine.dialect.name != "sqlite":
        raise SystemExit(
            "Este migrador es exclusivamente local para SQLite; no se modificará PostgreSQL/Supabase."
        )
    for table in (
        UserAccount.__table__,
        Club.__table__,
        SportsCategory.__table__,
        CoachAssignment.__table__,
        ExerciseOwnership.__table__,
    ):
        table.create(bind=engine, checkfirst=True)

    db = SessionLocal()
    try:
        accounts_created = 0
        for user in db.query(Usuario).order_by(Usuario.id):
            if db.get(UserAccount, user.id) is not None:
                continue
            has_profile = db.query(PerfilEntrenador.id).filter(
                PerfilEntrenador.usuario_id == user.id
            ).first() is not None
            db.add(UserAccount(
                user_id=user.id,
                account_type="ENTRENADOR",
                must_change_password=not has_profile,
                onboarding_complete=has_profile,
            ))
            accounts_created += 1

        ownerships_created = 0
        creator_by_exercise = {
            relation.source_exercise_id: relation.created_by
            for relation in db.query(ExerciseRelation)
            .filter(
                ExerciseRelation.source_exercise_id > OFFICIAL_EXERCISE_MAX_ID,
                ExerciseRelation.created_by.is_not(None),
            )
            .all()
        }
        fallback_row = db.query(Usuario.id).order_by(Usuario.id.desc()).first()
        fallback_user_id = fallback_row[0] if fallback_row else None
        exercise_ids = [
            row[0]
            for row in db.execute(
                __import__("sqlalchemy").text(
                    "SELECT id FROM ejercicios WHERE id > :official_max ORDER BY id"
                ),
                {"official_max": OFFICIAL_EXERCISE_MAX_ID},
            )
        ]
        for exercise_id in exercise_ids:
            if db.get(ExerciseOwnership, exercise_id) is not None:
                continue
            creator_id = creator_by_exercise.get(exercise_id) or fallback_user_id
            if creator_id is None:
                raise RuntimeError(
                    f"No se puede inferir propietario para el ejercicio {exercise_id}"
                )
            db.add(ExerciseOwnership(
                ejercicio_id=exercise_id, created_by_user_id=creator_id
            ))
            ownerships_created += 1
        db.commit()
        print(f"Cuentas inicializadas: {accounts_created}")
        print(f"Propiedades privadas inicializadas: {ownerships_created}")
        print("Ejercicios oficiales modificados: 0")
    finally:
        db.close()


if __name__ == "__main__":
    main()
