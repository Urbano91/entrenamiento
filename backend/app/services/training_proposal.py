"""Motor V3 de propuesta de sesión para SCOUT IA."""

from __future__ import annotations

from itertools import combinations
from typing import Any

from sqlalchemy.orm import Session

from app.services.exercise_recommender import select_exercise_candidates
from app.services.training_load import estimate_training_load

SOURCE_PENALTY = {"PROPIO": 0.0, "FAVORITO": 2.0, "BIBLIOTECA": 5.0}


def _level(score: float) -> str:
    if score < 40:
        return "BAJA"
    if score < 70:
        return "MODERADA"
    return "ALTA"


def _candidate_input(item: dict[str, Any]) -> dict[str, Any]:
    objectives = item.get("objectives") or []
    return {
        "name": item["name"],
        "task_type": item.get("task_type"),
        "players": item.get("players"),
        "space": item.get("space"),
        "time_description": item.get("time_description"),
        "objective_1": objectives[0] if len(objectives) > 0 else None,
        "objective_2": objectives[1] if len(objectives) > 1 else None,
    }


def _estimate(group, duration_minutes: int):
    return estimate_training_load(
        exercises=[_candidate_input(item) for item in group],
        training_duration_minutes=duration_minutes,
    )


def _best_combination(
    candidates: list[dict[str, Any]],
    *,
    target_score: float,
    duration_minutes: int,
    requested_count: int,
):
    if not candidates:
        return [], estimate_training_load(
            exercises=[],
            training_duration_minutes=duration_minutes,
        )

    own = [x for x in candidates if x.get("source") == "PROPIO"][:6]
    fav = [x for x in candidates if x.get("source") == "FAVORITO"][:6]
    lib = [x for x in candidates if x.get("source") == "BIBLIOTECA"][:6]

    pool = []
    seen = set()
    for item in own + fav + lib:
        if item["exercise_id"] not in seen:
            seen.add(item["exercise_id"])
            pool.append(item)

    max_count = min(requested_count, len(pool), 6)
    min_count = 1

    # El número de tareas no es fijo: se orienta por la duración de la sesión.
    if duration_minutes <= 35:
        ideal_count = 2
    elif duration_minutes <= 55:
        ideal_count = 3
    elif duration_minutes <= 75:
        ideal_count = 4
    elif duration_minutes <= 95:
        ideal_count = 5
    else:
        ideal_count = 6

    ideal_count = max(1, min(ideal_count, max_count))

    best = None
    best_estimate = None
    best_rank = None

    for count in range(min_count, max_count + 1):
        for group in combinations(pool, count):
            estimate = _estimate(group, duration_minutes)
            gap = abs(estimate["score"] - target_score)
            source_penalty = sum(SOURCE_PENALTY.get(x.get("source"), 8.0) for x in group)
            objective_bonus = sum(x.get("objective_match_count", 0) for x in group) * 2
            # Evita que el motor elija siempre 2 ejercicios solo porque su
            # media de carga se acerca al objetivo. La duración también manda.
            count_penalty = abs(ideal_count - count) * 14

            work_minutes = float(estimate.get("total_work_minutes") or 0)
            expected_work = max(duration_minutes * 0.55, 1)
            work_gap = abs(work_minutes - expected_work) / expected_work
            duration_coverage_penalty = min(work_gap, 1.5) * 12

            rank = (
                gap * 10
                + source_penalty
                - objective_bonus
                + count_penalty
                + duration_coverage_penalty
            )

            if best_rank is None or rank < best_rank:
                best_rank = rank
                best = group
                best_estimate = estimate

    return list(best or []), best_estimate or estimate_training_load(
        exercises=[],
        training_duration_minutes=duration_minutes,
    )


def build_training_proposal(
    db: Session,
    *,
    user_id: int,
    days_to_match: int | None,
    weekly_average_score: float | None,
    recent_average_score: float | None,
    high_load_sessions: int,
    desired_objectives: list[str] | None = None,
    exercise_count: int = 4,
    target_load_override: float | None = None,
    duration_override: int | None = None,
    session_role: str | None = None,
    session_role_label: str | None = None,
    session_role_reason: str | None = None,
    excluded_exercise_ids: set[int] | None = None,
) -> dict[str, Any]:
    desired_objectives = desired_objectives or []
    excluded_exercise_ids = excluded_exercise_ids or set()
    exercise_count = max(1, min(exercise_count, 6))

    target_score = float(target_load_override if target_load_override is not None else 55)
    duration_minutes = int(duration_override if duration_override is not None else 70)

    candidates = select_exercise_candidates(
        db,
        user_id=user_id,
        desired_objectives=desired_objectives,
        target_load_score=target_score,
        limit=250,
    )

    filtered = [
        x for x in candidates
        if x["exercise_id"] not in excluded_exercise_ids
    ]

    repeated_fallback = False
    if len(filtered) >= 2:
        candidates_to_use = filtered
    else:
        candidates_to_use = candidates
        repeated_fallback = True

    selected, estimated = _best_combination(
        candidates_to_use,
        target_score=target_score,
        duration_minutes=duration_minutes,
        requested_count=exercise_count,
    )

    source_counts = {
        "PROPIO": sum(1 for x in selected if x["source"] == "PROPIO"),
        "FAVORITO": sum(1 for x in selected if x["source"] == "FAVORITO"),
        "BIBLIOTECA": sum(1 for x in selected if x["source"] == "BIBLIOTECA"),
    }

    gap = round(abs(estimated["score"] - target_score), 1)
    if gap <= 5:
        fit_status = "MUY_AJUSTADA"
        fit_message = "La propuesta queda muy próxima a la carga objetivo."
    elif gap <= 10:
        fit_status = "AJUSTADA"
        fit_message = "La propuesta queda razonablemente próxima a la carga objetivo."
    else:
        fit_status = "LIMITADA_POR_BIBLIOTECA"
        fit_message = (
            "Con los ejercicios disponibles no es posible acercarse más "
            "sin modificar volumen o tiempos."
        )

    reasons = []
    if session_role_reason:
        reasons.append(session_role_reason)
    reasons.append(
        f"El rol de la sesión fija una carga objetivo de {target_score:g}/100 "
        f"y una duración de {duration_minutes} minutos."
    )
    if excluded_exercise_ids and not repeated_fallback:
        reasons.append("Se han evitado ejercicios ya usados en otras sesiones del microciclo.")
    if repeated_fallback:
        reasons.append("Ha sido necesario permitir alguna repetición por falta de alternativas.")
    reasons.append(fit_message)

    return {
        "status": "DRAFT",
        "message": "SCOUT IA propone. El entrenador decide.",
        "role": {
            "code": session_role,
            "label": session_role_label,
            "reason": session_role_reason,
        },
        "target": {
            "load_score": target_score,
            "load_level": _level(target_score),
            "duration_minutes": duration_minutes,
        },
        "context": {
            "days_to_match": days_to_match,
            "weekly_average_score": weekly_average_score,
            "recent_average_score": recent_average_score,
            "high_load_sessions": high_load_sessions,
            "desired_objectives": desired_objectives,
        },
        "selection_rule": ["PROPIO", "FAVORITO", "BIBLIOTECA"],
        "source_counts": source_counts,
        "exercises": selected,
        "estimated_proposal": {
            "score": estimated["score"],
            "level": estimated["level"],
            "total_work_minutes": estimated.get("total_work_minutes"),
            "reasons": estimated["reasons"],
        },
        "fit": {
            "target_score": target_score,
            "achieved_score": estimated["score"],
            "gap": gap,
            "status": fit_status,
            "message": fit_message,
        },
        "reasons": reasons,
    }
