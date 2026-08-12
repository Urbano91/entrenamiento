"""Autorización centralizada para identidad, clubes y ejercicios."""

from __future__ import annotations

from enum import Enum

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.models import (
    Club,
    CoachAssignment,
    Ejercicio,
    ExerciseOwnership,
    UserAccount,
    Usuario,
)


class AccountType(str, Enum):
    ADMIN = "ADMIN"
    TRAINER = "ENTRENADOR"
    CLUB = "CLUB"


def get_account(db: Session, user_id: int) -> UserAccount | None:
    return db.get(UserAccount, user_id)


def account_type(db: Session, user_id: int) -> AccountType:
    account = get_account(db, user_id)
    return AccountType(account.account_type if account else AccountType.TRAINER.value)


def require_trainer(db: Session, user: Usuario) -> None:
    if account_type(db, user.id) is not AccountType.TRAINER:
        raise HTTPException(status_code=403, detail="Acción reservada a entrenadores")


def require_onboarded_trainer(db: Session, user: Usuario) -> None:
    """Bloquea trabajo deportivo hasta sustituir la clave provisional."""

    require_trainer(db, user)
    account = get_account(db, user.id)
    if account is not None and (
        account.must_change_password or not account.onboarding_complete
    ):
        raise HTTPException(
            status_code=409,
            detail="Debes completar la configuración inicial de tu cuenta",
        )


def require_club(db: Session, user: Usuario) -> Club:
    if account_type(db, user.id) is not AccountType.CLUB:
        raise HTTPException(status_code=403, detail="Acción reservada a clubes")
    account = get_account(db, user.id)
    if account and (account.must_change_password or not account.onboarding_complete):
        raise HTTPException(status_code=409, detail="Debes cambiar la contraseña provisional")
    club = db.query(Club).filter(Club.owner_user_id == user.id).one_or_none()
    if club is None:
        raise HTTPException(status_code=409, detail="El perfil de Club no está configurado")
    return club


def require_admin(db: Session, user: Usuario) -> None:
    if account_type(db, user.id) is not AccountType.ADMIN:
        raise HTTPException(status_code=403, detail="Acción reservada a administración")
    account = get_account(db, user.id)
    if account and (account.must_change_password or not account.onboarding_complete):
        raise HTTPException(status_code=409, detail="Debes cambiar la contraseña provisional")


def club_coach_user_ids(db: Session, club_id: int) -> set[int]:
    return {
        row[0]
        for row in db.query(CoachAssignment.coach_user_id)
        .filter(CoachAssignment.club_id == club_id, CoachAssignment.active.is_(True))
        .distinct()
        .all()
    }


def visible_exercise_filter(db: Session, user: Usuario):
    """Oficiales + privados propios; para Club, privados de sus entrenadores."""

    owner_ids = {user.id}
    if account_type(db, user.id) is AccountType.CLUB:
        club = require_club(db, user)
        owner_ids = club_coach_user_ids(db, club.id)
    return or_(
        ~Ejercicio.ownership.has(),
        Ejercicio.ownership.has(
            and_(
                ExerciseOwnership.created_by_user_id.in_(owner_ids),
                ExerciseOwnership.deleted_at.is_(None),
            )
        ),
    )


def can_view_exercise(db: Session, user: Usuario, exercise: Ejercicio) -> bool:
    ownership = exercise.ownership
    if ownership is None:
        return True
    if ownership.deleted_at is not None:
        return False
    if ownership.created_by_user_id == user.id:
        return True
    if account_type(db, user.id) is AccountType.CLUB:
        club = require_club(db, user)
        return ownership.created_by_user_id in club_coach_user_ids(db, club.id)
    return False


def get_visible_exercise(
    db: Session, user: Usuario, exercise_id: int
) -> Ejercicio:
    exercise = db.get(Ejercicio, exercise_id)
    if exercise is None or not can_view_exercise(db, user, exercise):
        # No revelar si un ID pertenece a otro entrenador.
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    return exercise


def require_private_exercise_owner(
    db: Session, user: Usuario, exercise_id: int
) -> Ejercicio:
    require_onboarded_trainer(db, user)
    exercise = db.get(Ejercicio, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    ownership = exercise.ownership
    if ownership is None:
        raise HTTPException(status_code=403, detail="Los ejercicios oficiales son inmutables")
    if ownership.created_by_user_id != user.id:
        raise HTTPException(status_code=403, detail="No puedes modificar un ejercicio ajeno")
    if ownership.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    return exercise
