from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import PerfilEntrenador, Temporada, Usuario
from app.api.auth import get_current_user
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
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


@router.get("", response_model=PerfilOut)
def get_perfil(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    perfil = db.query(PerfilEntrenador).filter(PerfilEntrenador.usuario_id == current_user.id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return perfil


@router.put("", response_model=PerfilOut)
def upsert_perfil(
    data: PerfilUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    perfil = db.query(PerfilEntrenador).filter(PerfilEntrenador.usuario_id == current_user.id).first()
    if not perfil:
        perfil = PerfilEntrenador(usuario_id=current_user.id)
        db.add(perfil)

    perfil.nombre = data.nombre
    perfil.apellidos = data.apellidos
    perfil.club_actual = data.club_actual
    if "temporada_actual_id" in data.model_fields_set:
        if data.temporada_actual_id is not None:
            temporada = db.query(Temporada.id).filter(
                Temporada.id == data.temporada_actual_id
            ).first()
            if not temporada:
                raise HTTPException(status_code=422, detail="La temporada indicada no existe")
        perfil.temporada_actual_id = data.temporada_actual_id

    db.commit()
    db.refresh(perfil)
    return perfil
