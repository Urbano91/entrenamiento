"""Motor V2 de microciclo para SCOUT IA."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.models import Entrenamiento, Partido
from app.services.training_load import estimate_training_load
from app.services.training_proposal import build_training_proposal


ROLE_MAP = {
    1: {
        "code": "PREPARTIDO",
        "label": "Prepartido",
        "load": 32,
        "duration": 45,
        "reason": "Última sesión antes del partido: se reduce volumen y exigencia.",
    },
    2: {
        "code": "APROXIMACION",
        "label": "Aproximación competitiva",
        "load": 42,
        "duration": 60,
        "reason": "Sesión de aproximación al partido con carga contenida.",
    },
    3: {
        "code": "DESARROLLO_TACTICO",
        "label": "Desarrollo táctico",
        "load": 55,
        "duration": 70,
        "reason": "Sesión intermedia para desarrollar contenidos sin concentrar la carga máxima.",
    },
    4: {
        "code": "CARGA_PRINCIPAL",
        "label": "Día principal de carga",
        "load": 68,
        "duration": 80,
        "reason": "Día principal del microciclo con mayor margen respecto al partido.",
    },
}


def _training_exercises(entrenamiento: Entrenamiento) -> list[dict]:
    result = []
    for relation in entrenamiento.ejercicios_rel:
        ejercicio = relation.ejercicio
        result.append({
            "name": ejercicio.nombre,
            "task_type": ejercicio.tipo.nombre if ejercicio.tipo else None,
            "players": ejercicio.jugadores,
            "space": ejercicio.espacio.descripcion_original if ejercicio.espacio else None,
            "time_description": ejercicio.tiempo.descripcion_original if ejercicio.tiempo else None,
            "objective_1": ejercicio.objetivo_1_normalizado,
            "objective_2": ejercicio.objetivo_2_normalizado,
        })
    return result


def _analyse_training(entrenamiento: Entrenamiento) -> dict[str, Any]:
    result = estimate_training_load(
        exercises=_training_exercises(entrenamiento),
        training_duration_minutes=entrenamiento.duracion_minutos,
    )
    return {
        "score": result["score"],
        "level": result["level"],
    }


def _role_for_days_to_match(days_to_match: int) -> dict[str, Any]:
    if days_to_match <= 1:
        return ROLE_MAP[1]
    if days_to_match == 2:
        return ROLE_MAP[2]
    if days_to_match == 3:
        return ROLE_MAP[3]
    if days_to_match == 4:
        return ROLE_MAP[4]

    return {
        "code": "DESARROLLO",
        "label": "Desarrollo",
        "load": 60,
        "duration": 75,
        "reason": "Sesión de desarrollo situada con margen suficiente respecto al partido.",
    }


def build_weekly_training_proposal(
    db: Session,
    *,
    user_id: int,
    reference_date: date,
    training_dates: list[date],
    desired_objectives: list[str] | None = None,
    exercise_count: int = 4,
) -> dict[str, Any]:
    desired_objectives = desired_objectives or []

    next_match = (
        db.query(Partido)
        .filter(
            Partido.usuario_id == user_id,
            Partido.fecha >= reference_date,
        )
        .order_by(Partido.fecha.asc(), Partido.hora.asc())
        .first()
    )

    if not next_match:
        return {
            "status": "NO_MATCH",
            "message": "No hay un próximo partido registrado.",
            "next_match": None,
            "days": [],
        }

    match_date = next_match.fecha

    valid_training_dates = sorted({
        day for day in training_dates
        if reference_date <= day < match_date
    })

    week_start = reference_date - timedelta(days=reference_date.weekday())
    week_end = week_start + timedelta(days=6)

    weekly_trainings = (
        db.query(Entrenamiento)
        .filter(
            Entrenamiento.usuario_id == user_id,
            Entrenamiento.fecha >= week_start,
            Entrenamiento.fecha <= week_end,
        )
        .all()
    )

    weekly_analysis = [_analyse_training(x) for x in weekly_trainings]
    weekly_scores = [x["score"] for x in weekly_analysis if x["level"] != "SIN DATOS"]
    weekly_average_score = (
        round(sum(weekly_scores) / len(weekly_scores), 1)
        if weekly_scores else None
    )
    high_load_sessions = sum(1 for x in weekly_analysis if x["level"] == "ALTA")

    recent_start = reference_date - timedelta(days=14)
    recent_trainings = (
        db.query(Entrenamiento)
        .filter(
            Entrenamiento.usuario_id == user_id,
            Entrenamiento.fecha >= recent_start,
            Entrenamiento.fecha < reference_date,
        )
        .all()
    )

    recent_analysis = [_analyse_training(x) for x in recent_trainings]
    recent_scores = [x["score"] for x in recent_analysis if x["level"] != "SIN DATOS"]
    recent_average_score = (
        round(sum(recent_scores) / len(recent_scores), 1)
        if recent_scores else None
    )

    used_exercise_ids: set[int] = set()
    days: list[dict[str, Any]] = []

    cursor = reference_date
    while cursor < match_date:
        if cursor not in valid_training_dates:
            days.append({
                "fecha": cursor.isoformat(),
                "tipo": "DESCANSO",
                "role": {
                    "code": "DESCANSO",
                    "label": "Descanso",
                    "reason": "Día marcado como descanso por el entrenador.",
                },
                "proposal": None,
            })
            cursor += timedelta(days=1)
            continue

        days_to_match = (match_date - cursor).days
        role = _role_for_days_to_match(days_to_match)

        # Si la carga reciente es alta, reducimos un escalón de forma conservadora.
        target_load = role["load"]
        duration = role["duration"]
        role_reason = role["reason"]

        if (
            (weekly_average_score is not None and weekly_average_score >= 70)
            or (recent_average_score is not None and recent_average_score >= 70)
        ):
            target_load = max(30, target_load - 5)
            duration = max(40, duration - 5)
            role_reason += " La carga reciente es alta, por lo que se aplica una reducción adicional."

        proposal = build_training_proposal(
            db,
            user_id=user_id,
            days_to_match=days_to_match,
            weekly_average_score=weekly_average_score,
            recent_average_score=recent_average_score,
            high_load_sessions=high_load_sessions,
            desired_objectives=desired_objectives,
            exercise_count=exercise_count,
            target_load_override=target_load,
            duration_override=duration,
            session_role=role["code"],
            session_role_label=role["label"],
            session_role_reason=role_reason,
            excluded_exercise_ids=used_exercise_ids,
        )

        for exercise in proposal["exercises"]:
            used_exercise_ids.add(exercise["exercise_id"])

        days.append({
            "fecha": cursor.isoformat(),
            "tipo": "ENTRENAMIENTO",
            "role": proposal["role"],
            "proposal": proposal,
        })

        cursor += timedelta(days=1)

    return {
        "status": "DRAFT",
        "message": "SCOUT IA propone el microciclo. El entrenador decide.",
        "reference_date": reference_date.isoformat(),
        "next_match": {
            "partido_id": next_match.id,
            "fecha": next_match.fecha.isoformat(),
            "hora": next_match.hora.strftime("%H:%M") if next_match.hora else None,
            "rival": next_match.rival,
            "local_visitante": next_match.local_visitante,
            "campo": next_match.campo,
        },
        "context": {
            "weekly_average_score": weekly_average_score,
            "recent_average_score": recent_average_score,
            "high_load_sessions": high_load_sessions,
        },
        "days": days,
    }
