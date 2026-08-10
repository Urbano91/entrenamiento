import calendar
from datetime import date, time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, selectinload

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.models import Entrenamiento, Partido, Usuario
from app.services.season_context import selected_season_id


router = APIRouter(prefix="/api/calendario", tags=["Calendario"])


def _training_payload(training: Entrenamiento) -> dict:
    return {
        "id": training.id,
        "nombre": training.nombre,
        "duracion_minutos": training.duracion_minutos,
        "num_ejercicios": len(training.ejercicios_rel),
        "objetivo_principal": training.objetivo_principal,
    }


def _match_payload(match: Partido) -> dict:
    return {
        "id": match.id,
        "temporada_id": match.temporada_id,
        "fecha": match.fecha.isoformat(),
        "hora": match.hora.isoformat(timespec="minutes") if match.hora else None,
        "rival": match.rival,
        "local_visitante": match.local_visitante,
        "campo": match.campo,
        "observaciones": match.observaciones,
        "created_at": match.created_at.isoformat() if match.created_at else None,
        "updated_at": match.updated_at.isoformat() if match.updated_at else None,
    }


@router.get("")
def get_calendario(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    temporada_id: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    season_id = selected_season_id(db, current_user.id, temporada_id)
    _, num_days = calendar.monthrange(year, month)
    fecha_inicio = date(year, month, 1)
    fecha_fin = date(year, month, num_days)

    entrenamientos = (
        db.query(Entrenamiento)
        .options(selectinload(Entrenamiento.ejercicios_rel))
        .filter(
            Entrenamiento.usuario_id == current_user.id,
            Entrenamiento.temporada_id == season_id,
            Entrenamiento.fecha >= fecha_inicio,
            Entrenamiento.fecha <= fecha_fin,
        )
        .all()
    )
    partidos = (
        db.query(Partido)
        .filter(
            Partido.usuario_id == current_user.id,
            Partido.temporada_id == season_id,
            Partido.fecha >= fecha_inicio,
            Partido.fecha <= fecha_fin,
        )
        .all()
    )

    # ``dias`` conserva el contrato de Fase 2. ``planificacion`` es el contrato
    # de Fase 3 y agrupa la representación por fecha sin fusionar registros.
    dias: dict[str, list[dict]] = {}
    planificacion: dict[str, dict] = {}

    training_groups: dict[str, list[Entrenamiento]] = {}
    for training in entrenamientos:
        training_groups.setdefault(training.fecha.isoformat(), []).append(training)

    match_groups: dict[str, list[Partido]] = {}
    for match in partidos:
        match_groups.setdefault(match.fecha.isoformat(), []).append(match)

    for key in sorted(set(training_groups) | set(match_groups)):
        daily_trainings = sorted(
            training_groups.get(key, []),
            key=lambda item: (
                item.created_at.isoformat() if item.created_at else "",
                item.id,
            ),
        )
        daily_matches = sorted(
            match_groups.get(key, []),
            key=lambda item: (
                item.hora is None, item.hora or time.max,
                item.created_at.isoformat() if item.created_at else "",
                item.id,
            ),
        )
        training_payloads = [_training_payload(item) for item in daily_trainings]
        match_payloads = [_match_payload(item) for item in daily_matches]
        if training_payloads:
            dias[key] = training_payloads
        planificacion[key] = {
            "fecha": key,
            "entrenamientos": training_payloads,
            "resumen_entrenamiento": {
                # Las filas actuales son sesiones/secciones. Mientras no exista
                # un padre explícito, su agrupación diaria representa un único
                # entrenamiento planificado.
                "entrenamientos_planificados": 1 if training_payloads else 0,
                "sesiones": len(training_payloads),
                "duracion_total": sum(
                    item.duracion_minutos or 0 for item in daily_trainings
                ),
                "num_ejercicios_total": sum(
                    len(item.ejercicios_rel) for item in daily_trainings
                ),
            },
            "partidos": match_payloads,
        }

    return {
        "year": year,
        "month": month,
        "temporada_id": season_id,
        "num_days": num_days,
        "dias": dias,
        "planificacion": planificacion,
    }
