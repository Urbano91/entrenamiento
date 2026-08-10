#!/usr/bin/env python3
"""Aísla calendarios por temporada sin eliminar datos históricos."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "database" / "futbol_entrenamiento.sqlite"
MIGRATION_ID = "20260810_03_isolated_season_calendars"


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def validate_library(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise RuntimeError("PRAGMA integrity_check no es ok")
    if conn.execute("SELECT COUNT(*) FROM ejercicios").fetchone()[0] != 114:
        raise RuntimeError("La biblioteca no contiene 114 ejercicios")
    if conn.execute("SELECT COUNT(*) FROM imagenes").fetchone()[0] != 122:
        raise RuntimeError("La biblioteca no contiene 122 imágenes")


def create_backup(database: Path) -> Path:
    backup = database.with_name(
        f"{database.name}.bak-season-calendar-migration-"
        f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
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
            raise RuntimeError("El backup automático no supera integrity_check")
    finally:
        check.close()
    return backup


def assign_active_seasons(conn: sqlite3.Connection) -> None:
    for table in ("entrenamientos", "partidos", "planificaciones_diarias"):
        conn.execute(
            f"UPDATE {table} SET temporada_id=("
            "SELECT perfil.temporada_actual_id FROM perfiles_entrenador AS perfil "
            f"WHERE perfil.usuario_id={table}.usuario_id"
            f") WHERE {table}.temporada_id IS NULL"
        )
        unresolved = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE temporada_id IS NULL"
        ).fetchone()[0]
        if unresolved:
            raise RuntimeError(
                f"{table}: hay {unresolved} registros sin una temporada activa inferible"
            )
        invalid = conn.execute(
            f"SELECT COUNT(*) FROM {table} AS item "
            "LEFT JOIN temporadas AS temporada ON temporada.id=item.temporada_id "
            "WHERE temporada.id IS NULL"
        ).fetchone()[0]
        if invalid:
            raise RuntimeError(f"{table}: hay {invalid} temporadas inexistentes")


def rebuild_event_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE entrenamientos__season_new ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL, "
        "temporada_id INTEGER NOT NULL, fecha DATE NOT NULL, hora TIME, "
        "nombre VARCHAR NOT NULL, duracion_minutos INTEGER, "
        "objetivo_principal TEXT, observaciones TEXT, "
        "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
        "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
        "FOREIGN KEY(usuario_id) REFERENCES usuarios(id), "
        "FOREIGN KEY(temporada_id) REFERENCES temporadas(id))"
    )
    conn.execute(
        "INSERT INTO entrenamientos__season_new "
        "SELECT id, usuario_id, temporada_id, fecha, hora, nombre, "
        "duracion_minutos, objetivo_principal, observaciones, created_at, updated_at "
        "FROM entrenamientos"
    )

    conn.execute(
        "CREATE TABLE partidos__season_new ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL, "
        "temporada_id INTEGER NOT NULL, fecha DATE NOT NULL, hora TIME, "
        "rival VARCHAR NOT NULL, local_visitante VARCHAR NOT NULL DEFAULT 'local' "
        "CHECK (local_visitante IN ('local', 'visitante')), campo VARCHAR, "
        "observaciones TEXT, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
        "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
        "FOREIGN KEY(usuario_id) REFERENCES usuarios(id), "
        "FOREIGN KEY(temporada_id) REFERENCES temporadas(id))"
    )
    conn.execute(
        "INSERT INTO partidos__season_new "
        "SELECT id, usuario_id, temporada_id, fecha, hora, rival, local_visitante, "
        "campo, observaciones, created_at, updated_at FROM partidos"
    )

    conn.execute(
        "CREATE TABLE planificaciones_diarias__season_new ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL, "
        "temporada_id INTEGER NOT NULL, fecha DATE NOT NULL, nota TEXT, "
        "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
        "updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
        "CONSTRAINT uq_planificacion_usuario_temporada_fecha "
        "UNIQUE(usuario_id, temporada_id, fecha), "
        "FOREIGN KEY(usuario_id) REFERENCES usuarios(id), "
        "FOREIGN KEY(temporada_id) REFERENCES temporadas(id))"
    )
    conn.execute(
        "INSERT INTO planificaciones_diarias__season_new "
        "SELECT id, usuario_id, temporada_id, fecha, nota, created_at, updated_at "
        "FROM planificaciones_diarias"
    )

    for table in ("entrenamientos", "partidos", "planificaciones_diarias"):
        conn.execute(f"DROP TABLE {table}")
        conn.execute(f"ALTER TABLE {table}__season_new RENAME TO {table}")

    conn.execute("CREATE INDEX ix_partidos_usuario_id ON partidos(usuario_id)")
    conn.execute("CREATE INDEX ix_partidos_temporada_id ON partidos(temporada_id)")
    conn.execute("CREATE INDEX ix_partidos_fecha ON partidos(fecha)")
    conn.execute(
        "CREATE INDEX ix_planificaciones_diarias_usuario_id "
        "ON planificaciones_diarias(usuario_id)"
    )
    conn.execute(
        "CREATE INDEX ix_planificaciones_diarias_temporada_id "
        "ON planificaciones_diarias(temporada_id)"
    )
    conn.execute(
        "CREATE INDEX ix_planificaciones_diarias_fecha "
        "ON planificaciones_diarias(fecha)"
    )


def migrate(database: Path, apply: bool) -> int:
    conn = sqlite3.connect(database, isolation_level=None)
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        validate_library(conn)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "id TEXT PRIMARY KEY, applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        if conn.execute(
            "SELECT 1 FROM schema_migrations WHERE id=?", (MIGRATION_ID,)
        ).fetchone():
            print("La migración de calendarios por temporada ya está aplicada.")
            return 0
        null_counts = {
            table: conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE temporada_id IS NULL"
            ).fetchone()[0]
            for table in ("entrenamientos", "partidos", "planificaciones_diarias")
        }
        print(f"Registros sin temporada: {null_counts}")
        if not apply:
            print("Auditoría terminada sin cambios. Use --apply para migrar.")
            return 0

        backup = create_backup(database)
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("BEGIN IMMEDIATE")
        try:
            before = {
                table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in (
                    "entrenamientos", "entrenamiento_ejercicios", "partidos",
                    "planificaciones_diarias", "documentos_planificacion",
                )
            }
            assign_active_seasons(conn)
            rebuild_event_tables(conn)
            after = {
                table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in before
            }
            if before != after:
                raise RuntimeError(f"Los recuentos han cambiado: {before} != {after}")
            if conn.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise RuntimeError("La migración ha generado relaciones huérfanas")
            conn.execute(
                "INSERT INTO schema_migrations(id) VALUES (?)", (MIGRATION_ID,)
            )
            validate_library(conn)
            conn.execute("COMMIT")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.execute("PRAGMA foreign_keys=ON")
        print(f"Backup automático: {backup}")
        print("Migración aplicada: calendarios aislados e integrity_check ok.")
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
