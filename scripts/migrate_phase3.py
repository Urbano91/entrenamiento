#!/usr/bin/env python3
"""Migración idempotente de Fase 3: hora de sesión y tabla partidos."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "database" / "futbol_entrenamiento.sqlite"
MIGRATION_ID = "20260810_01_phase3_partidos"


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(row[1] == column for row in conn.execute(f"PRAGMA table_info({table})"))


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def validate(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise RuntimeError("PRAGMA foreign_keys no está activado")
    if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise RuntimeError("PRAGMA integrity_check no es ok")
    if conn.execute("SELECT COUNT(*) FROM ejercicios").fetchone()[0] != 114:
        raise RuntimeError("La biblioteca no contiene 114 ejercicios")
    if conn.execute("SELECT COUNT(*) FROM imagenes").fetchone()[0] != 122:
        raise RuntimeError("La biblioteca no contiene 122 imágenes")


def create_backup(database: Path) -> Path:
    backup = database.with_name(
        f"{database.name}.bak-before-phase3-{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
            raise RuntimeError("El backup creado no supera integrity_check")
    finally:
        check.close()
    return backup


def migrate(database: Path, apply: bool) -> int:
    conn = sqlite3.connect(database, isolation_level=None)
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        validate(conn)
        needs_hour = not column_exists(conn, "entrenamientos", "hora")
        needs_matches = not table_exists(conn, "partidos")
        if not needs_hour and not needs_matches:
            print("Fase 3 ya está migrada; no se modificó la base ni se creó backup.")
            return 0
        print(f"Entrenamientos.hora pendiente: {'sí' if needs_hour else 'no'}")
        print(f"Tabla partidos pendiente: {'sí' if needs_matches else 'no'}")
        if not apply:
            print("Auditoría terminada sin cambios. Use --apply para migrar.")
            return 0

        backup = create_backup(database)
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "id TEXT PRIMARY KEY, applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )
            if needs_hour:
                conn.execute("ALTER TABLE entrenamientos ADD COLUMN hora TIME")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS partidos ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "usuario_id INTEGER NOT NULL, temporada_id INTEGER, "
                "fecha DATE NOT NULL, hora TIME, rival VARCHAR NOT NULL, "
                "local_visitante VARCHAR NOT NULL DEFAULT 'local' "
                "CHECK (local_visitante IN ('local', 'visitante')), "
                "campo VARCHAR, observaciones TEXT, "
                "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
                "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
                "FOREIGN KEY(usuario_id) REFERENCES usuarios(id), "
                "FOREIGN KEY(temporada_id) REFERENCES temporadas(id))"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_partidos_usuario_id ON partidos(usuario_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_partidos_temporada_id ON partidos(temporada_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_partidos_fecha ON partidos(fecha)"
            )
            conn.execute(
                "INSERT OR IGNORE INTO schema_migrations(id) VALUES (?)", (MIGRATION_ID,)
            )
            validate(conn)
            if conn.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise RuntimeError("La migración ha generado relaciones huérfanas")
            conn.execute("COMMIT")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        print(f"Backup: {backup}")
        print("Migración Fase 3 aplicada. integrity_check: ok")
        return 0
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    try:
        args = parse_args()
        raise SystemExit(migrate(args.database.resolve(), args.apply))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
