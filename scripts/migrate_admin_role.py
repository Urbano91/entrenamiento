#!/usr/bin/env python3
"""Amplía roles/asignaciones sin alterar tablas de actividad ni ejercicios."""

from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "database" / "futbol_entrenamiento.sqlite"


def migrate(database: Path = DATABASE) -> None:
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        account_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='user_accounts'"
        ).fetchone()[0]
        assignment_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='coach_assignments'"
        ).fetchone()[0]
        connection.execute("BEGIN IMMEDIATE")
        if "'ADMIN'" not in account_sql:
            connection.executescript("""
                ALTER TABLE user_accounts RENAME TO user_accounts_pre_admin;
                CREATE TABLE user_accounts (
                    user_id INTEGER NOT NULL PRIMARY KEY,
                    account_type VARCHAR NOT NULL,
                    must_change_password BOOLEAN NOT NULL,
                    onboarding_complete BOOLEAN NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    CONSTRAINT ck_user_account_type
                        CHECK (account_type IN ('ADMIN', 'ENTRENADOR', 'CLUB')),
                    FOREIGN KEY(user_id) REFERENCES usuarios(id) ON DELETE CASCADE
                );
                INSERT INTO user_accounts
                    (user_id, account_type, must_change_password,
                     onboarding_complete, created_at, updated_at)
                SELECT user_id, account_type, must_change_password,
                       onboarding_complete, created_at, updated_at
                FROM user_accounts_pre_admin;
                DROP TABLE user_accounts_pre_admin;
            """)
        if "club_id INTEGER" in assignment_sql and "club_id INTEGER NOT NULL" in assignment_sql:
            connection.executescript("""
                ALTER TABLE coach_assignments RENAME TO coach_assignments_pre_admin;
                CREATE TABLE coach_assignments (
                    id INTEGER NOT NULL PRIMARY KEY,
                    coach_user_id INTEGER NOT NULL,
                    club_id INTEGER,
                    temporada_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    active BOOLEAN NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    CONSTRAINT uq_coach_assignment_context
                        UNIQUE (coach_user_id, club_id, temporada_id, category_id),
                    FOREIGN KEY(coach_user_id) REFERENCES usuarios(id),
                    FOREIGN KEY(club_id) REFERENCES clubs(id) ON DELETE CASCADE,
                    FOREIGN KEY(temporada_id) REFERENCES temporadas(id),
                    FOREIGN KEY(category_id) REFERENCES sports_categories(id)
                );
                INSERT INTO coach_assignments
                    (id, coach_user_id, club_id, temporada_id, category_id,
                     active, created_at)
                SELECT id, coach_user_id, club_id, temporada_id, category_id,
                       active, created_at
                FROM coach_assignments_pre_admin;
                DROP TABLE coach_assignments_pre_admin;
                CREATE INDEX ix_coach_assignments_club_season
                    ON coach_assignments(club_id, temporada_id);
                CREATE INDEX ix_coach_assignments_coach
                    ON coach_assignments(coach_user_id);
            """)
        admin = connection.execute(
            "SELECT id FROM usuarios WHERE usuario = 'admin'"
        ).fetchone()
        if admin:
            connection.execute(
                """UPDATE user_accounts
                   SET account_type='ADMIN', must_change_password=0,
                       onboarding_complete=1, updated_at=CURRENT_TIMESTAMP
                   WHERE user_id=?""",
                (admin[0],),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.close()


if __name__ == "__main__":
    migrate()
    print("Migración ADMIN aplicada correctamente")
