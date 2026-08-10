from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from pydantic import BaseModel

from app.db.database import get_db
from app.models.models import PerfilEntrenador, Temporada, Usuario
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/temporadas", tags=["Temporadas"])


class TemporadaCreate(BaseModel):
    nombre: str
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


class TemporadaOut(BaseModel):
    id: int
    nombre: str
    fecha_inicio: Optional[date]
    fecha_fin: Optional[date]
    activa: bool = False

    model_config = {"from_attributes": True}


@router.get("", response_model=List[TemporadaOut])
def list_temporadas(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    perfil = db.query(PerfilEntrenador).filter(
        PerfilEntrenador.usuario_id == current_user.id
    ).first()
    active_id = perfil.temporada_actual_id if perfil else None
    return [
        TemporadaOut(
            id=item.id,
            nombre=item.nombre,
            fecha_inicio=item.fecha_inicio,
            fecha_fin=item.fecha_fin,
            activa=item.id == active_id,
        )
        for item in db.query(Temporada).order_by(Temporada.nombre).all()
    ]


@router.post("", response_model=TemporadaOut)
def create_temporada(
    data: TemporadaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    temporada = Temporada(
        nombre=data.nombre,
        fecha_inicio=data.fecha_inicio,
        fecha_fin=data.fecha_fin
    )
    db.add(temporada)
    db.flush()
    perfil = db.query(PerfilEntrenador).filter(
        PerfilEntrenador.usuario_id == current_user.id
    ).first()
    if perfil:
        perfil.temporada_actual_id = temporada.id
    db.commit()
    db.refresh(temporada)
    return TemporadaOut(
        id=temporada.id,
        nombre=temporada.nombre,
        fecha_inicio=temporada.fecha_inicio,
        fecha_fin=temporada.fecha_fin,
        activa=perfil is not None,
    )
