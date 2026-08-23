"""API de carga y propuesta de SCOUT IA.

ESTE ARCHIVO VA EN:
backend/app/api/training_load.py

NO pegar en backend/app/services/training_load.py
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.models import Entrenamiento, Partido, Usuario
from app.services.exercise_recommender import select_exercise_candidates
from app.services.permissions import require_trainer
from app.services.training_load import estimate_training_load
from app.services.training_proposal import build_training_proposal


router = APIRouter(
    prefix="/api/training-load",
    tags=["Training Load"],
)


def _training_exercises(entrenamiento: Entrenamiento) -> list[dict]:
    exercises = []

    for relation in entrenamiento.ejercicios_rel:
        ejercicio = relation.ejercicio

        exercises.append({
            "name": ejercicio.nombre,
            "task_type": ejercicio.tipo.nombre if ejercicio.tipo else None,
            "players": ejercicio.jugadores,
            "space": (
                ejercicio.espacio.descripcion_original
                if ejercicio.espacio
                else None
            ),
            "time_description": (
                ejercicio.tiempo.descripcion_original
                if ejercicio.tiempo
                else None
            ),
            "objective_1": ejercicio.objetivo_1_normalizado,
            "objective_2": ejercicio.objetivo_2_normalizado,
        })

    return exercises


def _analyse_training(entrenamiento: Entrenamiento) -> dict:
    result = estimate_training_load(
        exercises=_training_exercises(entrenamiento),
        training_duration_minutes=entrenamiento.duracion_minutos,
    )

    return {
        "entrenamiento_id": entrenamiento.id,
        "nombre": entrenamiento.nombre,
        "fecha": entrenamiento.fecha.isoformat(),
        "hora": (
            entrenamiento.hora.strftime("%H:%M")
            if entrenamiento.hora
            else None
        ),
        "duracion_minutos": entrenamiento.duracion_minutos,
        **result,
    }


@router.get("/exercise-candidates")
def get_exercise_candidates(
    objetivo: list[str] | None = Query(default=None),
    carga_objetivo: float | None = Query(default=None, ge=0, le=100),
    limite: int = Query(default=12, ge=1, le=50),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_trainer(db, current_user)

    candidates = select_exercise_candidates(
        db,
        user_id=current_user.id,
        desired_objectives=objetivo or [],
        target_load_score=carga_objetivo,
        limit=limite,
    )

    return {
        "user_id": current_user.id,
        "priority_rule": ["PROPIO", "FAVORITO", "BIBLIOTECA"],
        "filters": {
            "objetivos": objetivo or [],
            "carga_objetivo": carga_objetivo,
            "limite": limite,
        },
        "count": len(candidates),
        "candidates": candidates,
    }


@router.get("/proposal")
def get_training_proposal(
    fecha: date | None = Query(default=None),
    objetivo: list[str] | None = Query(default=None),
    ejercicios: int = Query(default=4, ge=1, le=6),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_trainer(db, current_user)

    reference_date = fecha or date.today()

    week_start = reference_date - timedelta(days=reference_date.weekday())
    week_end = week_start + timedelta(days=6)

    weekly_trainings = (
        db.query(Entrenamiento)
        .filter(
            Entrenamiento.usuario_id == current_user.id,
            Entrenamiento.fecha >= week_start,
            Entrenamiento.fecha <= week_end,
        )
        .order_by(
            Entrenamiento.fecha.asc(),
            Entrenamiento.hora.asc(),
        )
        .all()
    )

    weekly_analysis = [
        _analyse_training(training)
        for training in weekly_trainings
    ]

    weekly_scores = [
        item["score"]
        for item in weekly_analysis
        if item["level"] != "SIN DATOS"
    ]

    weekly_average_score = (
        round(sum(weekly_scores) / len(weekly_scores), 1)
        if weekly_scores
        else None
    )

    high_load_sessions = sum(
        1
        for item in weekly_analysis
        if item["level"] == "ALTA"
    )

    recent_start = reference_date - timedelta(days=14)

    recent_trainings = (
        db.query(Entrenamiento)
        .filter(
            Entrenamiento.usuario_id == current_user.id,
            Entrenamiento.fecha >= recent_start,
            Entrenamiento.fecha < reference_date,
        )
        .order_by(Entrenamiento.fecha.asc())
        .all()
    )

    recent_analysis = [
        _analyse_training(training)
        for training in recent_trainings
    ]

    recent_scores = [
        item["score"]
        for item in recent_analysis
        if item["level"] != "SIN DATOS"
    ]

    recent_average_score = (
        round(sum(recent_scores) / len(recent_scores), 1)
        if recent_scores
        else None
    )

    next_match = (
        db.query(Partido)
        .filter(
            Partido.usuario_id == current_user.id,
            Partido.fecha >= reference_date,
        )
        .order_by(
            Partido.fecha.asc(),
            Partido.hora.asc(),
        )
        .first()
    )

    days_to_match = (
        (next_match.fecha - reference_date).days
        if next_match
        else None
    )

    proposal = build_training_proposal(
        db,
        user_id=current_user.id,
        days_to_match=days_to_match,
        weekly_average_score=weekly_average_score,
        recent_average_score=recent_average_score,
        high_load_sessions=high_load_sessions,
        desired_objectives=objetivo or [],
        exercise_count=ejercicios,
    )

    return {
        "reference_date": reference_date.isoformat(),
        "next_match": (
            {
                "partido_id": next_match.id,
                "fecha": next_match.fecha.isoformat(),
                "hora": (
                    next_match.hora.strftime("%H:%M")
                    if next_match.hora
                    else None
                ),
                "rival": next_match.rival,
                "local_visitante": next_match.local_visitante,
                "campo": next_match.campo,
                "dias_desde_referencia": days_to_match,
            }
            if next_match
            else None
        ),
        "weekly_context": {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "training_count": len(weekly_analysis),
            "average_score": weekly_average_score,
            "high_load_sessions": high_load_sessions,
        },
        "recent_14_days": {
            "training_count": len(recent_analysis),
            "average_score": recent_average_score,
        },
        "proposal": proposal,
    }


@router.get("/week")
def get_week_training_load(
    fecha: date | None = Query(
        default=None,
        description="Fecha de referencia. Ejemplo: 2026-08-24",
    ),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_trainer(db, current_user)

    reference_date = fecha or date.today()

    week_start = reference_date - timedelta(days=reference_date.weekday())
    week_end = week_start + timedelta(days=6)

    trainings = (
        db.query(Entrenamiento)
        .filter(
            Entrenamiento.usuario_id == current_user.id,
            Entrenamiento.fecha >= week_start,
            Entrenamiento.fecha <= week_end,
        )
        .order_by(
            Entrenamiento.fecha.asc(),
            Entrenamiento.hora.asc(),
        )
        .all()
    )

    analysed_trainings = [
        _analyse_training(training)
        for training in trainings
    ]

    next_match = (
        db.query(Partido)
        .filter(
            Partido.usuario_id == current_user.id,
            Partido.fecha >= reference_date,
        )
        .order_by(
            Partido.fecha.asc(),
            Partido.hora.asc(),
        )
        .first()
    )

    next_match_data = None

    if next_match:
        next_match_data = {
            "partido_id": next_match.id,
            "fecha": next_match.fecha.isoformat(),
            "hora": (
                next_match.hora.strftime("%H:%M")
                if next_match.hora
                else None
            ),
            "rival": next_match.rival,
            "local_visitante": next_match.local_visitante,
            "campo": next_match.campo,
            "dias_desde_referencia": (
                next_match.fecha - reference_date
            ).days,
        }

    scores = [
        training["score"]
        for training in analysed_trainings
        if training["level"] != "SIN DATOS"
    ]

    average_score = (
        round(sum(scores) / len(scores), 1)
        if scores
        else None
    )

    high_count = sum(
        1
        for training in analysed_trainings
        if training["level"] == "ALTA"
    )

    moderate_count = sum(
        1
        for training in analysed_trainings
        if training["level"] == "MODERADA"
    )

    low_count = sum(
        1
        for training in analysed_trainings
        if training["level"] == "BAJA"
    )

    total_minutes = sum(
        training["duracion_minutos"] or 0
        for training in analysed_trainings
    )

    alerts: list[str] = []

    if high_count >= 2:
        alerts.append(
            f"Hay {high_count} sesiones de carga alta planificadas esta semana."
        )

    if next_match:
        for training in analysed_trainings:
            training_date = date.fromisoformat(training["fecha"])
            days_before_match = (next_match.fecha - training_date).days

            if (
                training["level"] == "ALTA"
                and 0 < days_before_match <= 2
            ):
                alerts.append(
                    f"La sesión '{training['nombre']}' tiene carga alta "
                    f"y está a {days_before_match} día(s) del próximo partido."
                )

    if not alerts and analysed_trainings:
        alerts.append(
            "No se han detectado alertas básicas de distribución de carga esta semana."
        )

    recent_start = reference_date - timedelta(days=14)

    recent_trainings = (
        db.query(Entrenamiento)
        .filter(
            Entrenamiento.usuario_id == current_user.id,
            Entrenamiento.fecha >= recent_start,
            Entrenamiento.fecha < reference_date,
        )
        .order_by(Entrenamiento.fecha.asc())
        .all()
    )

    recent_analysis = [
        _analyse_training(training)
        for training in recent_trainings
    ]

    recent_scores = [
        item["score"]
        for item in recent_analysis
        if item["level"] != "SIN DATOS"
    ]

    recent_average_score = (
        round(sum(recent_scores) / len(recent_scores), 1)
        if recent_scores
        else None
    )

    return {
        "reference_date": reference_date.isoformat(),
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "summary": {
            "training_count": len(analysed_trainings),
            "total_minutes": total_minutes,
            "average_score": average_score,
            "high_load_sessions": high_count,
            "moderate_load_sessions": moderate_count,
            "low_load_sessions": low_count,
        },
        "trainings": analysed_trainings,
        "next_match": next_match_data,
        "recent_14_days": {
            "training_count": len(recent_analysis),
            "average_score": recent_average_score,
        },
        "alerts": alerts,
    }


@router.get("/{entrenamiento_id}")
def get_training_load(
    entrenamiento_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_trainer(db, current_user)

    entrenamiento = (
        db.query(Entrenamiento)
        .filter(
            Entrenamiento.id == entrenamiento_id,
            Entrenamiento.usuario_id == current_user.id,
        )
        .first()
    )

    if entrenamiento is None:
        raise HTTPException(
            status_code=404,
            detail="Entrenamiento no encontrado",
        )

    return _analyse_training(entrenamiento)