from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import get_db
from app.models.models import Ejercicio, TipoTarea, Objetivo, Material, Espacio, Tiempo, EjercicioObjetivo, EjercicioMaterial, EjercicioImagen
from app.schemas.schemas import EjercicioListOut, EjercicioDetailOut, PaginatedEjercicios
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/ejercicios", tags=["Ejercicios"], dependencies=[Depends(get_current_user)])

ANIMATIONS_DIR = Path(__file__).resolve().parents[3] / "animations"


def exercise_assets_dir(exercise_id: int) -> Path:
    return ANIMATIONS_DIR / str(exercise_id)


def animation_path(exercise_id: int) -> Path:
    return exercise_assets_dir(exercise_id) / "animacion.webm"


def cover_path(exercise_id: int) -> Path:
    return exercise_assets_dir(exercise_id) / "portada.webp"


def mark_animation_availability(exercise: Ejercicio) -> Ejercicio:
    exercise.tiene_portada = cover_path(exercise.id).is_file()
    exercise.tiene_animacion = animation_path(exercise.id).is_file()
    return exercise

@router.get("", response_model=PaginatedEjercicios)
def list_ejercicios(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
    tipo: Optional[str] = None,
    jugadores: Optional[int] = None,
    objetivo: Optional[str] = None,
    espacio: Optional[str] = None,
    tiempo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Ejercicio)

    # Buscador General
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                Ejercicio.codigo.ilike(search),
                Ejercicio.nombre.ilike(search),
                Ejercicio.desarrollo.ilike(search),
                Ejercicio.objetivos_asociados.any(
                    EjercicioObjetivo.objetivo.has(Objetivo.nombre_normalizado.ilike(search))
                )
            )
        )
    
    # Filtros
    if tipo:
        query = query.filter(Ejercicio.tipo.has(TipoTarea.nombre == tipo))
    if jugadores:
        query = query.filter(Ejercicio.jugadores == jugadores)
    if objetivo:
        query = query.filter(Ejercicio.objetivos_asociados.any(
            EjercicioObjetivo.objetivo.has(Objetivo.nombre_normalizado == objetivo)
        ))
    if espacio:
        query = query.filter(Ejercicio.espacio.has(Espacio.descripcion_original == espacio))
    if tiempo:
        query = query.filter(Ejercicio.tiempo.has(Tiempo.descripcion_original == tiempo))
    
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    for item in items:
        mark_animation_availability(item)
    
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages
    }

@router.get("/{id}/animacion")
def get_animacion(id: int, db: Session = Depends(get_db)):
    if not db.query(Ejercicio.id).filter(Ejercicio.id == id).first():
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")

    target = animation_path(id)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Animación no disponible")

    return FileResponse(
        target,
        media_type="video/webm",
        filename=f"ejercicio-{id}.webm",
        content_disposition_type="inline",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/{id}/portada")
def get_portada(id: int, db: Session = Depends(get_db)):
    if not db.query(Ejercicio.id).filter(Ejercicio.id == id).first():
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")

    target = cover_path(id)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Portada no disponible")

    return FileResponse(
        target,
        media_type="image/webp",
        filename=f"ejercicio-{id}-portada.webp",
        content_disposition_type="inline",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/{id}", response_model=EjercicioDetailOut)
def get_ejercicio(id: int, db: Session = Depends(get_db)):
    ejercicio = db.query(Ejercicio).filter(Ejercicio.id == id).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    return mark_animation_availability(ejercicio)
