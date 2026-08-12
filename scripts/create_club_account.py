#!/usr/bin/env python3
"""Crea una cuenta Club local sin reutilizar credenciales de entrenador."""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.chdir(ROOT / "backend")

from app.db.database import SessionLocal, engine  # noqa: E402
from app.models.models import Club, UserAccount, Usuario  # noqa: E402
from app.scripts.create_user import get_password_hash  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--usuario", required=True)
    parser.add_argument("--nombre", required=True)
    args = parser.parse_args()
    password = getpass.getpass("Contraseña inicial del Club: ")
    confirmation = getpass.getpass("Repetir contraseña: ")
    if len(password) < 8 or password != confirmation:
        raise SystemExit("La contraseña debe tener 8 caracteres y coincidir")
    if engine.dialect.name != "sqlite":
        raise SystemExit("Este comando local no modificará PostgreSQL/Supabase.")
    db = SessionLocal()
    try:
        if db.query(Usuario.id).filter(Usuario.usuario == args.usuario).first():
            raise SystemExit("El usuario ya existe")
        user = Usuario(
            usuario=args.usuario,
            password_hash=get_password_hash(password),
            activo=True,
        )
        db.add(user)
        db.flush()
        db.add(UserAccount(
            user_id=user.id,
            account_type="CLUB",
            must_change_password=False,
            onboarding_complete=True,
        ))
        db.add(Club(owner_user_id=user.id, nombre=args.nombre.strip()))
        db.commit()
        print(f"Club creado con user_id={user.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
