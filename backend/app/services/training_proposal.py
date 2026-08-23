"""Motor V2 de propuesta de próxima sesión para SCOUT IA.

Objetivo:
- usar contexto semanal y proximidad del próximo partido;
- calcular una carga objetivo y duración orientativa;
- buscar una combinación REAL de ejercicios que se acerque a esa carga;
- respetar como preferencia:
    1. ejercicios propios del entrenador,
    2. favoritos,
    3. biblioteca general;
- evitar propuestas incoherentes como "objetivo 20/100" y sesión final 54/100
  sin explicarlo.

IMPORTANTE:
- NO usa un LLM.
- NO guarda entrenamientos.
- NO sustituye al entrenador.
- Los umbrales son heurísticas V2 de producto y deben validarse con cuerpos técnicos.
"""

from __future__ import annotations

from itertools import combinations
from typing import Any

from sqlalchemy.orm import Session

from app.services.exercise_recommender import select_exercise_candidates
from app.services.training_load import estimate_training_load


SOURCE_PENALTY = {
    "PROPIO": 0.0,
    "FAVORITO": 2.0,
    "BIBLIOTECA": 5.0,
}


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def determine_target_load(
    *,
    days_to_match: int | None,
    weekly_average_score: float | None,
    recent_average_score: float | None,
    high_load_sessions: int,
) -> dict[str, Any]:
    """
    Define una carga objetivo en la misma escala usada por training_load.py.

    La V2 evita objetivos extremadamente bajos el día previo al partido cuando
    la propia escala de ejercicios disponibles hace que sean poco alcanzables.

    Reglas base:
    - hoy: 25
    - mañana: 35
    - 2 días: 42
    - 3-4 días: 55
    - 5+ días: 65
    - sin partido: 55

    Después se ajusta por carga semanal/reciente, con suelo contextual.
    """

    reasons: list[str] = []

    if days_to_match is None:
        target = 55.0
        minimum_target = 35.0
        reasons.append(
            "No hay un próximo partido registrado; se propone una carga moderada."
        )
    elif days_to_match <= 0:
        target = 25.0
        minimum_target = 20.0
        reasons.append(
            "El partido es hoy; la propuesta prioriza una carga muy baja."
        )
    elif days_to_match == 1:
        target = 35.0
        minimum_target = 30.0
        reasons.append(
            "El partido es mañana; la propuesta prioriza activación y baja exigencia."
        )
    elif days_to_match == 2:
        target = 42.0
        minimum_target = 35.0
        reasons.append(
            "El partido está a 2 días; se limita la carga prevista."
        )
    elif days_to_match <= 4:
        target = 55.0
        minimum_target = 40.0
        reasons.append(
            f"El partido está a {days_to_match} días; se propone una carga moderada."
        )
    else:
        target = 65.0
        minimum_target = 45.0
        reasons.append(
            f"El partido está a {days_to_match} días; existe margen para una sesión más exigente."
        )

    if weekly_average_score is not None and weekly_average_score >= 70:
        target -= 8
        reasons.append(
            "La carga media de la semana ya es alta, por lo que se reduce la carga objetivo."
        )
    elif weekly_average_score is not None and weekly_average_score >= 60:
        target -= 4
        reasons.append(
            "La carga media semanal es moderada-alta, por lo que se aplica una pequeña reducción."
        )

    if recent_average_score is not None and recent_average_score >= 70:
        target -= 4
        reasons.append(
            "Los últimos 14 días presentan una carga media alta."
        )

    if high_load_sessions >= 3:
        target -= 3
        reasons.append(
            "Ya existen varias sesiones de carga alta en la semana."
        )

    target = round(
        _clamp(
            target,
            minimum_target,
            75.0,
        ),
        1,
    )

    level = (
        "BAJA"
        if target < 40
        else "MODERADA"
        if target < 70
        else "ALTA"
    )

    return {
        "target_score": target,
        "target_level": level,
        "reasons": reasons,
    }


def determine_target_duration(
    *,
    days_to_match: int | None,
) -> dict[str, Any]:
    """
    Duración orientativa V2.
    """

    if days_to_match is None:
        minutes = 75
        reason = "Sin partido próximo registrado, se propone una duración estándar."
    elif days_to_match <= 0:
        minutes = 30
        reason = "El partido es hoy; se limita mucho la duración."
    elif days_to_match == 1:
        minutes = 45
        reason = "El partido es mañana; se propone una sesión corta."
    elif days_to_match == 2:
        minutes = 60
        reason = "El partido está a 2 días; se propone una duración contenida."
    elif days_to_match <= 4:
        minutes = 70
        reason = f"El partido está a {days_to_match} días; se propone una duración intermedia."
    else:
        minutes = 80
        reason = f"El partido está a {days_to_match} días; existe margen para una sesión completa."

    return {
        "target_minutes": minutes,
        "reason": reason,
    }


def _candidate_to_training_input(item: dict[str, Any]) -> dict[str, Any]:
    objectives = item.get("objectives") or []

    return {
        "name": item["name"],
        "task_type": item.get("task_type"),
        "players": item.get("players"),
        "space": item.get("space"),
        "time_description": item.get("time_description"),
        "objective_1": objectives[0] if len(objectives) >= 1 else None,
        "objective_2": objectives[1] if len(objectives) >= 2 else None,
    }


def _estimate_candidate_group(
    group: tuple[dict[str, Any], ...],
    *,
    duration_minutes: int,
) -> dict[str, Any]:
    return estimate_training_load(
        exercises=[
            _candidate_to_training_input(item)
            for item in group
        ],
        training_duration_minutes=duration_minutes,
    )


def _combination_rank(
    group: tuple[dict[str, Any], ...],
    *,
    estimated_score: float,
    target_score: float,
    desired_objectives: list[str],
) -> tuple[float, float, float]:
    """
    Menor es mejor.

    Prioridades:
    1. acercarse de verdad a la carga objetivo;
    2. preferir propios > favoritos > biblioteca;
    3. premiar coincidencias con objetivos.

    La prioridad de origen es una preferencia, no una obligación que pueda
    romper completamente la carga objetivo.
    """

    load_gap = abs(estimated_score - target_score)

    source_penalty = sum(
        SOURCE_PENALTY.get(item.get("source"), 8.0)
        for item in group
    )

    objective_matches = sum(
        item.get("objective_match_count", 0)
        for item in group
    )

    # El gap de carga manda claramente.
    total_rank = (
        load_gap * 10.0
        + source_penalty
        - objective_matches * 2.0
    )

    return (
        round(total_rank, 3),
        round(load_gap, 3),
        round(source_penalty, 3),
    )


def _choose_best_combination(
    candidates: list[dict[str, Any]],
    *,
    target_score: float,
    duration_minutes: int,
    desired_objectives: list[str],
    requested_count: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Busca la combinación cuya carga global quede más cerca del objetivo.

    Para que el cálculo sea razonable:
    - toma hasta 12 mejores candidatos por cada origen;
    - prueba combinaciones desde 2 hasta requested_count ejercicios;
    - favorece el número solicitado, pero permite una tarea menos si mejora
      claramente la carga objetivo.
    """

    if not candidates:
        return [], estimate_training_load(
            exercises=[],
            training_duration_minutes=duration_minutes,
        )

    own = [
        item for item in candidates
        if item.get("source") == "PROPIO"
    ][:12]

    favorites = [
        item for item in candidates
        if item.get("source") == "FAVORITO"
    ][:12]

    library = [
        item for item in candidates
        if item.get("source") == "BIBLIOTECA"
    ][:12]

    pool = own + favorites + library

    # Quitar duplicados por exercise_id manteniendo el orden.
    unique_pool: list[dict[str, Any]] = []
    seen_ids: set[int] = set()

    for item in pool:
        exercise_id = item["exercise_id"]
        if exercise_id not in seen_ids:
            seen_ids.add(exercise_id)
            unique_pool.append(item)

    if not unique_pool:
        return [], estimate_training_load(
            exercises=[],
            training_duration_minutes=duration_minutes,
        )

    max_count = min(
        requested_count,
        len(unique_pool),
    )

    min_count = 2 if max_count >= 2 else 1

    best_group: tuple[dict[str, Any], ...] | None = None
    best_estimate: dict[str, Any] | None = None
    best_rank: tuple[float, float, float, int] | None = None

    for count in range(min_count, max_count + 1):
        for group in combinations(unique_pool, count):
            estimate = _estimate_candidate_group(
                group,
                duration_minutes=duration_minutes,
            )

            rank = _combination_rank(
                group,
                estimated_score=estimate["score"],
                target_score=target_score,
                desired_objectives=desired_objectives,
            )

            # Pequeña penalización por alejarse del nº de ejercicios pedido.
            count_penalty = abs(requested_count - count) * 3

            comparable_rank = (
                rank[0] + count_penalty,
                rank[1],
                rank[2],
                -count,
            )

            if best_rank is None or comparable_rank < best_rank:
                best_rank = comparable_rank
                best_group = group
                best_estimate = estimate

    if best_group is None or best_estimate is None:
        selected = unique_pool[:max_count]
        fallback = estimate_training_load(
            exercises=[
                _candidate_to_training_input(item)
                for item in selected
            ],
            training_duration_minutes=duration_minutes,
        )
        return selected, fallback

    return list(best_group), best_estimate


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
) -> dict[str, Any]:
    """
    Construye una propuesta V2 estructurada.

    La diferencia fundamental respecto a V1 es que NO toma simplemente
    los primeros candidatos. Busca la combinación completa cuya carga
    estimada esté más cerca del objetivo.
    """

    desired_objectives = desired_objectives or []
    exercise_count = max(1, min(exercise_count, 6))

    target_load = determine_target_load(
        days_to_match=days_to_match,
        weekly_average_score=weekly_average_score,
        recent_average_score=recent_average_score,
        high_load_sessions=high_load_sessions,
    )

    target_duration = determine_target_duration(
        days_to_match=days_to_match,
    )

    # Recuperamos candidatos suficientes de los 3 niveles.
    candidates = select_exercise_candidates(
        db,
        user_id=user_id,
        desired_objectives=desired_objectives,
        target_load_score=target_load["target_score"],
        limit=250,
    )

    selected, estimated_proposal = _choose_best_combination(
        candidates,
        target_score=target_load["target_score"],
        duration_minutes=target_duration["target_minutes"],
        desired_objectives=desired_objectives,
        requested_count=exercise_count,
    )

    source_counts = {
        "PROPIO": sum(
            1 for item in selected
            if item["source"] == "PROPIO"
        ),
        "FAVORITO": sum(
            1 for item in selected
            if item["source"] == "FAVORITO"
        ),
        "BIBLIOTECA": sum(
            1 for item in selected
            if item["source"] == "BIBLIOTECA"
        ),
    }

    achieved_score = estimated_proposal["score"]
    target_score = target_load["target_score"]
    load_gap = round(abs(achieved_score - target_score), 1)

    if load_gap <= 5:
        feasibility = "MUY_AJUSTADA"
        feasibility_message = (
            "La propuesta queda muy próxima a la carga objetivo."
        )
    elif load_gap <= 10:
        feasibility = "AJUSTADA"
        feasibility_message = (
            "La propuesta queda razonablemente próxima a la carga objetivo."
        )
    else:
        feasibility = "LIMITADA_POR_BIBLIOTECA"
        feasibility_message = (
            "Con los ejercicios disponibles, no es posible acercarse más "
            "a la carga objetivo sin modificar ejercicios, volumen o tiempos."
        )

    proposal_reasons = [
        *target_load["reasons"],
        target_duration["reason"],
    ]

    if desired_objectives:
        proposal_reasons.append(
            "Se han priorizado ejercicios relacionados con: "
            + ", ".join(desired_objectives)
            + "."
        )

    if source_counts["PROPIO"] > 0:
        proposal_reasons.append(
            "Se han priorizado ejercicios creados por el entrenador siempre que encajan con la carga objetivo."
        )

    if source_counts["FAVORITO"] > 0:
        proposal_reasons.append(
            "Se han utilizado favoritos cuando mejoraban el ajuste de la sesión."
        )

    if source_counts["BIBLIOTECA"] > 0:
        proposal_reasons.append(
            "Se ha recurrido a la biblioteca general cuando permitía acercar mejor la sesión al objetivo."
        )

    proposal_reasons.append(
        feasibility_message
    )

    return {
        "status": "DRAFT",
        "message": "SCOUT IA propone. El entrenador decide.",
        "target": {
            "load_score": target_score,
            "load_level": target_load["target_level"],
            "duration_minutes": target_duration["target_minutes"],
        },
        "context": {
            "days_to_match": days_to_match,
            "weekly_average_score": weekly_average_score,
            "recent_average_score": recent_average_score,
            "high_load_sessions": high_load_sessions,
            "desired_objectives": desired_objectives,
        },
        "selection_rule": [
            "PROPIO",
            "FAVORITO",
            "BIBLIOTECA",
        ],
        "selection_strategy": (
            "La prioridad de origen se respeta como preferencia, "
            "pero la carga objetivo manda sobre la composición final."
        ),
        "source_counts": source_counts,
        "exercises": selected,
        "estimated_proposal": {
            "score": achieved_score,
            "level": estimated_proposal["level"],
            "total_work_minutes": estimated_proposal.get(
                "total_work_minutes"
            ),
            "reasons": estimated_proposal["reasons"],
        },
        "fit": {
            "target_score": target_score,
            "achieved_score": achieved_score,
            "gap": load_gap,
            "status": feasibility,
            "message": feasibility_message,
        },
        "reasons": proposal_reasons,
    }