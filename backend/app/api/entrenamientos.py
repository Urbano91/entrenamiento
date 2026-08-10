from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.models.models import (
    Entrenamiento, EntrenamientoEjercicio, Ejercicio, Usuario,
    EjercicioImagen
)
from app.api.auth import get_current_user
from app.services.season_context import active_season_id, selected_season_id

router = APIRouter(prefix="/api/entrenamientos", tags=["Entrenamientos"])


# ─── Schemas ────────────────────────────────────────────────────────────────

class EntrenamientoCreate(BaseModel):
    fecha: date
    nombre: str
    duracion_minutos: Optional[int] = None
    objetivo_principal: Optional[str] = None
    observaciones: Optional[str] = None

    model_config = {"extra": "forbid"}


class EntrenamientoUpdate(BaseModel):
    fecha: Optional[date] = None
    nombre: Optional[str] = None
    duracion_minutos: Optional[int] = None
    objetivo_principal: Optional[str] = None
    observaciones: Optional[str] = None

    model_config = {"extra": "forbid"}


class EjercicioEnEntrenoOut(BaseModel):
    id: int               # id de la relación EntrenamientoEjercicio
    ejercicio_id: int
    orden: int
    codigo: str
    nombre: str
    tipo: str
    jugadores: int
    espacio: str
    tiempo: str
    imagen_principal: Optional[int] = None

    model_config = {"from_attributes": True}


class EntrenamientoListOut(BaseModel):
    id: int
    temporada_id: int
    fecha: date
    nombre: str
    duracion_minutos: Optional[int]
    objetivo_principal: Optional[str]
    num_ejercicios: int = 0
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class EntrenamientoDetailOut(BaseModel):
    id: int
    fecha: date
    nombre: str
    duracion_minutos: Optional[int]
    objetivo_principal: Optional[str]
    observaciones: Optional[str]
    temporada_id: int
    ejercicios: List[EjercicioEnEntrenoOut] = []
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AgregarEjercicioIn(BaseModel):
    ejercicio_id: int
    orden: Optional[int] = None


class ReordenarItem(BaseModel):
    id: int    # id de EntrenamientoEjercicio
    orden: int


class ReutilizarIn(BaseModel):
    fecha: date
    nombre: Optional[str] = None
    duracion_minutos: Optional[int] = None
    objetivo_principal: Optional[str] = None
    observaciones: Optional[str] = None

    model_config = {"extra": "forbid"}


# ─── Helpers ────────────────────────────────────────────────────────────────

def _check_ownership(entrenamiento: Optional[Entrenamiento], usuario_id: int):
    if not entrenamiento:
        raise HTTPException(status_code=404, detail="Entrenamiento no encontrado")
    if entrenamiento.usuario_id != usuario_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")


def _enrich_ejercicios(rel_list: list) -> List[EjercicioEnEntrenoOut]:
    result = []
    for rel in rel_list:
        ej = rel.ejercicio
        # Primera imagen
        primera = None
        if ej.imagenes_asociadas:
            primera = ej.imagenes_asociadas[0].imagen.id
        result.append(EjercicioEnEntrenoOut(
            id=rel.id,
            ejercicio_id=ej.id,
            orden=rel.orden,
            codigo=ej.codigo,
            nombre=ej.nombre,
            tipo=ej.tipo.nombre if ej.tipo else "",
            jugadores=ej.jugadores,
            espacio=ej.espacio.descripcion_original if ej.espacio else "",
            tiempo=ej.tiempo.descripcion_original if ej.tiempo else "",
            imagen_principal=primera,
        ))
    return result


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.get("", response_model=List[EntrenamientoListOut])
def list_entrenamientos(
    temporada_id: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    season_id = selected_season_id(db, current_user.id, temporada_id)
    entrenamientos = (
        db.query(Entrenamiento)
        .filter(
            Entrenamiento.usuario_id == current_user.id,
            Entrenamiento.temporada_id == season_id,
        )
        .order_by(
            Entrenamiento.fecha.desc(), Entrenamiento.created_at.desc(),
        )
        .all()
    )
    result = []
    for e in entrenamientos:
        result.append(EntrenamientoListOut(
            id=e.id,
            temporada_id=e.temporada_id,
            fecha=e.fecha,
            nombre=e.nombre,
            duracion_minutos=e.duracion_minutos,
            objetivo_principal=e.objetivo_principal,
            num_ejercicios=len(e.ejercicios_rel),
            created_at=e.created_at,
        ))
    return result


@router.get("/{id}", response_model=EntrenamientoDetailOut)
def get_entrenamiento(
    id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    e = db.query(Entrenamiento).filter(Entrenamiento.id == id).first()
    _check_ownership(e, current_user.id)
    return EntrenamientoDetailOut(
        id=e.id,
        fecha=e.fecha,
        nombre=e.nombre,
        duracion_minutos=e.duracion_minutos,
        objetivo_principal=e.objetivo_principal,
        observaciones=e.observaciones,
        temporada_id=e.temporada_id,
        ejercicios=_enrich_ejercicios(e.ejercicios_rel),
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


@router.post("", response_model=EntrenamientoDetailOut, status_code=201)
def create_entrenamiento(
    data: EntrenamientoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    season_id = active_season_id(db, current_user.id)
    e = Entrenamiento(
        usuario_id=current_user.id,
        temporada_id=season_id,
        fecha=data.fecha,
        hora=None,
        nombre=data.nombre,
        duracion_minutos=data.duracion_minutos,
        objetivo_principal=data.objetivo_principal,
        observaciones=data.observaciones,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return EntrenamientoDetailOut(
        id=e.id, fecha=e.fecha, nombre=e.nombre,
        duracion_minutos=e.duracion_minutos,
        objetivo_principal=e.objetivo_principal,
        observaciones=e.observaciones,
        temporada_id=e.temporada_id,
        ejercicios=[], created_at=e.created_at, updated_at=e.updated_at,
    )


@router.put("/{id}", response_model=EntrenamientoDetailOut)
def update_entrenamiento(
    id: int,
    data: EntrenamientoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    e = db.query(Entrenamiento).filter(Entrenamiento.id == id).first()
    _check_ownership(e, current_user.id)
    if data.fecha is not None: e.fecha = data.fecha
    if data.nombre is not None: e.nombre = data.nombre
    if data.duracion_minutos is not None: e.duracion_minutos = data.duracion_minutos
    if data.objetivo_principal is not None: e.objetivo_principal = data.objetivo_principal
    if data.observaciones is not None: e.observaciones = data.observaciones
    db.commit()
    db.refresh(e)
    return EntrenamientoDetailOut(
        id=e.id, fecha=e.fecha, nombre=e.nombre,
        duracion_minutos=e.duracion_minutos,
        objetivo_principal=e.objetivo_principal,
        observaciones=e.observaciones,
        temporada_id=e.temporada_id,
        ejercicios=_enrich_ejercicios(e.ejercicios_rel),
        created_at=e.created_at, updated_at=e.updated_at,
    )


@router.delete("/{id}", status_code=204)
def delete_entrenamiento(
    id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    e = db.query(Entrenamiento).filter(Entrenamiento.id == id).first()
    _check_ownership(e, current_user.id)
    db.delete(e)
    db.commit()
    return None


@router.post("/{id}/reutilizar", response_model=EntrenamientoDetailOut, status_code=201)
def reutilizar_entrenamiento(
    id: int,
    data: ReutilizarIn,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    original = db.query(Entrenamiento).filter(Entrenamiento.id == id).first()
    _check_ownership(original, current_user.id)
    destination_season_id = active_season_id(db, current_user.id)

    copia = Entrenamiento(
        usuario_id=current_user.id,
        temporada_id=destination_season_id,
        fecha=data.fecha,
        hora=None,
        nombre=data.nombre if data.nombre is not None else original.nombre,
        duracion_minutos=data.duracion_minutos if data.duracion_minutos is not None else original.duracion_minutos,
        objetivo_principal=data.objetivo_principal if data.objetivo_principal is not None else original.objetivo_principal,
        observaciones=data.observaciones if data.observaciones is not None else original.observaciones,
    )
    db.add(copia)
    db.flush()  # obtener copia.id

    for rel in original.ejercicios_rel:
        nuevo_rel = EntrenamientoEjercicio(
            entrenamiento_id=copia.id,
            ejercicio_id=rel.ejercicio_id,
            orden=rel.orden,
        )
        db.add(nuevo_rel)

    db.commit()
    db.refresh(copia)
    return EntrenamientoDetailOut(
        id=copia.id, fecha=copia.fecha, nombre=copia.nombre,
        duracion_minutos=copia.duracion_minutos,
        objetivo_principal=copia.objetivo_principal,
        observaciones=copia.observaciones,
        temporada_id=copia.temporada_id,
        ejercicios=_enrich_ejercicios(copia.ejercicios_rel),
        created_at=copia.created_at, updated_at=copia.updated_at,
    )


# ─── Ejercicios del entrenamiento ───────────────────────────────────────────

@router.post("/{id}/ejercicios", response_model=EjercicioEnEntrenoOut, status_code=201)
def add_ejercicio(
    id: int,
    data: AgregarEjercicioIn,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    e = db.query(Entrenamiento).filter(Entrenamiento.id == id).first()
    _check_ownership(e, current_user.id)

    ejercicio = db.query(Ejercicio).filter(Ejercicio.id == data.ejercicio_id).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")

    orden = data.orden
    if orden is None:
        max_orden = max((r.orden for r in e.ejercicios_rel), default=-1)
        orden = max_orden + 1

    rel = EntrenamientoEjercicio(
        entrenamiento_id=e.id,
        ejercicio_id=ejercicio.id,
        orden=orden,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)

    primera = None
    if ejercicio.imagenes_asociadas:
        primera = ejercicio.imagenes_asociadas[0].imagen.id

    return EjercicioEnEntrenoOut(
        id=rel.id, ejercicio_id=ejercicio.id, orden=rel.orden,
        codigo=ejercicio.codigo, nombre=ejercicio.nombre,
        tipo=ejercicio.tipo.nombre if ejercicio.tipo else "",
        jugadores=ejercicio.jugadores,
        espacio=ejercicio.espacio.descripcion_original if ejercicio.espacio else "",
        tiempo=ejercicio.tiempo.descripcion_original if ejercicio.tiempo else "",
        imagen_principal=primera,
    )


@router.delete("/{id}/ejercicios/{relacion_id}", status_code=204)
def remove_ejercicio(
    id: int,
    relacion_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    e = db.query(Entrenamiento).filter(Entrenamiento.id == id).first()
    _check_ownership(e, current_user.id)

    rel = db.query(EntrenamientoEjercicio).filter(
        EntrenamientoEjercicio.id == relacion_id,
        EntrenamientoEjercicio.entrenamiento_id == id
    ).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    db.delete(rel)
    db.commit()
    return None


@router.put("/{id}/ejercicios/reordenar", status_code=200)
def reordenar_ejercicios(
    id: int,
    items: List[ReordenarItem],
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    e = db.query(Entrenamiento).filter(Entrenamiento.id == id).first()
    _check_ownership(e, current_user.id)

    for item in items:
        rel = db.query(EntrenamientoEjercicio).filter(
            EntrenamientoEjercicio.id == item.id,
            EntrenamientoEjercicio.entrenamiento_id == id
        ).first()
        if rel:
            rel.orden = item.orden

    db.commit()
    db.refresh(e)
    return {"ok": True}
