"""Administración interna de cuentas; no expone registro público."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.models import (
    Club, CoachAssignment, PerfilEntrenador, SportsCategory, Temporada,
    UserAccount, Usuario,
)
from app.scripts.create_user import get_password_hash
from app.services.permissions import AccountType, require_admin
from app.services.storage import StorageService, get_storage_service
from app.services.trainer_accounts import create_trainer_account
from app.services.user_deletion import delete_club_account, delete_trainer_user

router = APIRouter(prefix="/api/admin", tags=["Administración"])


class AdminClubCreate(BaseModel):
    nombre_club: str = Field(min_length=1, max_length=180)
    usuario: str = Field(min_length=1, max_length=120)
    password_provisional: str = Field(min_length=8)


class AdminTrainerCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=180)
    usuario: str = Field(min_length=1, max_length=120)
    password_provisional: str = Field(min_length=8)
    tipo: Literal["INDEPENDIENTE", "CLUB"] = "INDEPENDIENTE"
    club_id: Optional[int] = None
    categoria: Optional[str] = Field(default=None, min_length=1, max_length=120)
    temporada_id: Optional[int] = None


def _unique_username(db: Session, username: str) -> str:
    value = username.strip()
    if not value:
        raise HTTPException(status_code=422, detail="El usuario es obligatorio")
    if value.casefold() == "admin":
        raise HTTPException(status_code=409, detail="El usuario admin está reservado")
    if db.query(Usuario.id).filter(Usuario.usuario == value).first():
        raise HTTPException(status_code=409, detail="El usuario ya existe")
    return value


def account_payload(db: Session, user: Usuario) -> dict:
    account = db.get(UserAccount, user.id)
    profile = db.query(PerfilEntrenador).filter(
        PerfilEntrenador.usuario_id == user.id
    ).one_or_none()
    owned_club = db.query(Club).filter(Club.owner_user_id == user.id).one_or_none()
    assignments = db.query(CoachAssignment).filter(
        CoachAssignment.coach_user_id == user.id,
        CoachAssignment.active.is_(True),
    ).order_by(CoachAssignment.temporada_id.desc()).all()
    return {
        "user_id": user.id,
        "usuario": user.usuario,
        "account_type": account.account_type if account else "ENTRENADOR",
        "activo": user.activo,
        "must_change_password": bool(account and account.must_change_password),
        "display_name": (
            owned_club.nombre if owned_club else
            f"{profile.nombre} {profile.apellidos}" if profile else user.usuario
        ),
        "club_id": owned_club.id if owned_club else None,
        "assignments": [{
            "club_id": item.club_id,
            "club": item.club.nombre if item.club else None,
            "categoria": item.category.nombre,
            "temporada_id": item.temporada_id,
            "temporada": item.temporada.nombre,
        } for item in assignments],
    }


@router.get("/accounts")
def list_accounts(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(db, current_user)
    return [account_payload(db, user) for user in db.query(Usuario).order_by(Usuario.id).all()]


@router.get("/catalogs")
def catalogs(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(db, current_user)
    return {
        "clubs": [{"id": item.id, "nombre": item.nombre} for item in db.query(Club).order_by(Club.nombre).all()],
        "seasons": [{"id": item.id, "nombre": item.nombre} for item in db.query(Temporada).order_by(Temporada.nombre).all()],
        "categories": [item.nombre for item in db.query(SportsCategory).order_by(SportsCategory.nombre).all()],
    }


@router.post("/clubs", status_code=status.HTTP_201_CREATED)
def create_club(data: AdminClubCreate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(db, current_user)
    user = Usuario(
        usuario=_unique_username(db, data.usuario),
        password_hash=get_password_hash(data.password_provisional), activo=True,
    )
    try:
        db.add(user)
        db.flush()
        db.add(UserAccount(
            user_id=user.id, account_type=AccountType.CLUB.value,
            must_change_password=True, onboarding_complete=False,
        ))
        db.add(Club(owner_user_id=user.id, nombre=data.nombre_club.strip()))
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise
    return account_payload(db, user)


@router.post("/trainers", status_code=status.HTTP_201_CREATED)
def create_trainer(data: AdminTrainerCreate, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(db, current_user)
    season = db.get(Temporada, data.temporada_id) if data.temporada_id else None
    if data.temporada_id is not None and season is None:
        raise HTTPException(status_code=422, detail="Temporada no válida")
    club = None
    if data.tipo == "CLUB":
        club = db.get(Club, data.club_id) if data.club_id else None
        if club is None:
            raise HTTPException(status_code=422, detail="Selecciona un club válido")
    if bool(data.categoria) != bool(season):
        raise HTTPException(
            status_code=422,
            detail="Categoría y temporada deben asignarse conjuntamente",
        )
    user = create_trainer_account(
        db,
        nombre=data.nombre,
        apellidos=data.apellidos,
        usuario=data.usuario,
        password_provisional=data.password_provisional,
        club=club,
        season=season,
        category_name=data.categoria,
    )
    return account_payload(db, user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    require_admin(db, current_user)
    if user_id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="El administrador no puede eliminar su propia cuenta",
        )
    target = db.get(Usuario, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    account = db.get(UserAccount, user_id)
    if account is None or account.account_type != AccountType.TRAINER.value:
        raise HTTPException(
            status_code=403,
            detail="Solo se pueden eliminar cuentas de entrenador",
        )
    try:
        delete_trainer_user(db, target, storage)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo eliminar el usuario; no se aplicó ningún cambio",
        ) from exc
    return None


@router.delete("/clubs/{club_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_club(
    club_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(db, current_user)
    club = db.get(Club, club_id)
    if club is None:
        raise HTTPException(status_code=404, detail="Club no encontrado")
    try:
        delete_club_account(db, club)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo eliminar el club; no se aplicó ningún cambio",
        ) from exc
    return None
