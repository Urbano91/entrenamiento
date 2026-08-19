from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import CoachAssignment, PerfilEntrenador, Temporada, Usuario
from app.api.auth import get_current_user
from app.services.permissions import require_trainer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/perfil", tags=["Perfil"])


class PerfilUpdate(BaseModel):
    nombre: str
    apellidos: str
    club_actual: Optional[str] = None
    temporada_actual_id: Optional[int] = None


class TemporadaMiniOut(BaseModel):
    id: int
    nombre: str

    model_config = {"from_attributes": True}


class PerfilOut(BaseModel):
    id: int
    usuario_id: int
    nombre: str
    apellidos: str
    club_actual: Optional[str]
    temporada_actual_id: Optional[int]
    temporada_actual: Optional[TemporadaMiniOut]
    puesto: Optional[str] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


@router.get("", response_model=PerfilOut)
def get_perfil(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_trainer(db, current_user)

    perfil = db.query(PerfilEntrenador).filter(
        PerfilEntrenador.usuario_id == current_user.id
    ).first()

    if not perfil:
        raise HTTPException(
            status_code=404,
            detail="Perfil no encontrado"
        )

    assignment = (
        db.query(CoachAssignment)
        .filter(
            CoachAssignment.coach_user_id == perfil.usuario_id,
            CoachAssignment.temporada_id == perfil.temporada_actual_id,
        )
        .order_by(CoachAssignment.id.desc())
        .first()
    )

    return {
        "id": perfil.id,
        "usuario_id": perfil.usuario_id,
        "nombre": perfil.nombre,
        "apellidos": perfil.apellidos,
        "club_actual": perfil.club_actual,
        "temporada_actual_id": perfil.temporada_actual_id,
        "temporada_actual": perfil.temporada_actual,
        "puesto": assignment.puesto if assignment else None,
        "created_at": perfil.created_at,
        "updated_at": perfil.updated_at,
    }
