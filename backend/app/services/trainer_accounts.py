"""Creación común de cuentas de entrenador para ADMIN y CLUB."""

from __future__ import annotations

import re
import secrets
import string
import unicodedata
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import (
    Club, CoachAssignment, PerfilEntrenador, SportsCategory, Temporada,
    UserAccount, Usuario,
)
from app.scripts.create_user import get_password_hash
from app.services.permissions import AccountType


@dataclass(frozen=True)
class TrainerCredentials:
    usuario: str
    password_provisional: str


def _credential_token(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    without_accents = "".join(
        character for character in normalized
        if not unicodedata.combining(character)
    ).casefold()
    parts = re.findall(r"[a-z0-9]+", without_accents)
    return parts[0] if parts else ""


def generate_trainer_username(db: Session, nombre: str, apellidos: str) -> str:
    """Genera nombre.apellido y resuelve colisiones con un sufijo numérico."""

    first_name = _credential_token(nombre)
    first_surname = _credential_token(apellidos)
    if not first_name or not first_surname:
        raise HTTPException(
            status_code=422,
            detail="Nombre y apellidos deben contener caracteres válidos",
        )
    base = f"{first_name}.{first_surname}"[:120].rstrip(".")
    candidate = base
    suffix = 2
    while db.query(Usuario.id).filter(
        func.lower(Usuario.usuario) == candidate.casefold()
    ).first():
        suffix_text = str(suffix)
        candidate = f"{base[:120 - len(suffix_text)]}{suffix_text}"
        suffix += 1
    return candidate


def generate_temporary_password(length: int = 14) -> str:
    """Crea una clave provisional robusta que solo se devuelve al crear la cuenta."""

    if length < 8:
        raise ValueError("La contraseña temporal debe tener al menos 8 caracteres")
    alphabet = string.ascii_letters + string.digits + "-_.!"
    characters = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("-_.!"),
        *(secrets.choice(alphabet) for _ in range(length - 4)),
    ]
    secrets.SystemRandom().shuffle(characters)
    return "".join(characters)


def generate_trainer_credentials(
    db: Session, nombre: str, apellidos: str
) -> TrainerCredentials:
    return TrainerCredentials(
        usuario=generate_trainer_username(db, nombre, apellidos),
        password_provisional=generate_temporary_password(),
    )


def create_trainer_account(
    db: Session,
    *,
    nombre: str,
    apellidos: str,
    usuario: str,
    password_provisional: str,
    club: Club | None,
    season: Temporada | None,
    category_name: str | None,
    puesto: str = "Entrenador",
    parent_coach_assignment_id: int | None = None,
) -> Usuario:
    username = usuario.strip()

    if not username:
        raise HTTPException(
            status_code=422,
            detail="El usuario es obligatorio",
        )

    if username.casefold() == "admin":
        raise HTTPException(
            status_code=409,
            detail="El usuario admin está reservado",
        )

    if db.query(Usuario.id).filter(Usuario.usuario == username).first():
        raise HTTPException(
            status_code=409,
            detail="El usuario ya existe",
        )

    normalized_category = category_name.strip() if category_name else None

    if bool(normalized_category) != bool(season):
        raise HTTPException(
            status_code=422,
            detail="Categoría y temporada deben asignarse conjuntamente",
        )

    category = (
        db.query(SportsCategory)
        .filter(SportsCategory.nombre.ilike(normalized_category))
        .one_or_none()
        if normalized_category
        else None
    )

    user = Usuario(
        usuario=username,
        password_hash=get_password_hash(password_provisional),
        activo=True,
    )

    try:
        if normalized_category and category is None:
            category = SportsCategory(nombre=normalized_category)
            db.add(category)
            db.flush()

        db.add(user)
        db.flush()

        db.add(
            UserAccount(
                user_id=user.id,
                account_type=AccountType.TRAINER.value,
                must_change_password=True,
                onboarding_complete=False,
            )
        )

        db.add(
            PerfilEntrenador(
                usuario_id=user.id,
                nombre=nombre.strip(),
                apellidos=apellidos.strip(),
                club_actual=club.nombre if club else None,
                temporada_actual_id=season.id if season else None,
            )
        )

        if season and category:
            db.add(
                CoachAssignment(
                    coach_user_id=user.id,
                    club_id=club.id if club else None,
                    temporada_id=season.id,
                    category_id=category.id,
                    puesto=puesto,
                    parent_coach_assignment_id=parent_coach_assignment_id,
                    active=True,
                    visible_in_club=True,
                )
            )

        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise

    return user