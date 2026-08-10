from datetime import date, datetime, time
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.models import Partido, Usuario
from app.services.season_context import active_season_id, selected_season_id


router = APIRouter(prefix="/api/partidos", tags=["Partidos"])


class PartidoCreate(BaseModel):
    fecha: date
    hora: Optional[time] = None
    rival: str = Field(min_length=1, max_length=160)
    local_visitante: Literal["local", "visitante"] = "local"
    campo: Optional[str] = Field(default=None, max_length=240)
    observaciones: Optional[str] = None

    model_config = {"extra": "forbid"}

    @field_validator("rival")
    @classmethod
    def validate_rival(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El rival es obligatorio")
        return value


class PartidoUpdate(BaseModel):
    fecha: Optional[date] = None
    hora: Optional[time] = None
    rival: Optional[str] = Field(default=None, max_length=160)
    local_visitante: Optional[Literal["local", "visitante"]] = None
    campo: Optional[str] = Field(default=None, max_length=240)
    observaciones: Optional[str] = None

    model_config = {"extra": "forbid"}

    @field_validator("rival")
    @classmethod
    def validate_rival(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("El rival no puede estar vacío")
        return value


class PartidoOut(BaseModel):
    id: int
    usuario_id: int
    temporada_id: int
    fecha: date
    hora: Optional[time]
    rival: str
    local_visitante: Literal["local", "visitante"]
    campo: Optional[str]
    observaciones: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


def _owned_partido(db: Session, partido_id: int, usuario_id: int) -> Partido:
    partido = db.query(Partido).filter(Partido.id == partido_id).first()
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    if partido.usuario_id != usuario_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return partido


@router.get("", response_model=list[PartidoOut])
def list_partidos(
    year: Optional[int] = Query(default=None, ge=2000, le=2100),
    month: Optional[int] = Query(default=None, ge=1, le=12),
    temporada_id: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if month is not None and year is None:
        raise HTTPException(status_code=422, detail="month requiere year")
    season_id = selected_season_id(db, current_user.id, temporada_id)
    query = db.query(Partido).filter(
        Partido.usuario_id == current_user.id,
        Partido.temporada_id == season_id,
    )
    if year is not None:
        start = date(year, month or 1, 1)
        if month is None:
            end = date(year, 12, 31)
        else:
            import calendar
            end = date(year, month, calendar.monthrange(year, month)[1])
        query = query.filter(Partido.fecha >= start, Partido.fecha <= end)
    return query.order_by(
        Partido.fecha.asc(), Partido.hora.asc(), Partido.created_at.asc()
    ).all()


@router.get("/{partido_id}", response_model=PartidoOut)
def get_partido(
    partido_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _owned_partido(db, partido_id, current_user.id)


@router.post("", response_model=PartidoOut, status_code=status.HTTP_201_CREATED)
def create_partido(
    data: PartidoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    temporada_id = active_season_id(db, current_user.id)
    partido = Partido(
        usuario_id=current_user.id,
        temporada_id=temporada_id,
        fecha=data.fecha,
        hora=data.hora,
        rival=data.rival,
        local_visitante=data.local_visitante,
        campo=data.campo.strip() if data.campo and data.campo.strip() else None,
        observaciones=(
            data.observaciones.strip()
            if data.observaciones and data.observaciones.strip() else None
        ),
    )
    db.add(partido)
    db.commit()
    db.refresh(partido)
    return partido


@router.put("/{partido_id}", response_model=PartidoOut)
def update_partido(
    partido_id: int,
    data: PartidoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    partido = _owned_partido(db, partido_id, current_user.id)
    fields = data.model_fields_set
    if "fecha" in fields:
        if data.fecha is None:
            raise HTTPException(status_code=422, detail="La fecha es obligatoria")
        partido.fecha = data.fecha
    if "hora" in fields:
        partido.hora = data.hora
    if "rival" in fields:
        if data.rival is None:
            raise HTTPException(status_code=422, detail="El rival es obligatorio")
        partido.rival = data.rival
    if "local_visitante" in fields:
        if data.local_visitante is None:
            raise HTTPException(status_code=422, detail="Local/visitante es obligatorio")
        partido.local_visitante = data.local_visitante
    if "campo" in fields:
        partido.campo = data.campo.strip() if data.campo and data.campo.strip() else None
    if "observaciones" in fields:
        partido.observaciones = (
            data.observaciones.strip()
            if data.observaciones and data.observaciones.strip() else None
        )
    db.commit()
    db.refresh(partido)
    return partido


@router.delete("/{partido_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partido(
    partido_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    partido = _owned_partido(db, partido_id, current_user.id)
    db.delete(partido)
    db.commit()
    return None
