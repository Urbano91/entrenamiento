"""Selección V1 de candidatos para futuras propuestas de SCOUT IA.

Regla de prioridad:
1. Ejercicios creados por el entrenador.
2. Ejercicios favoritos del entrenador.
3. Resto de la biblioteca oficial.

Dentro de cada nivel se priorizan:
- coincidencia con objetivos deseados;
- cercanía a la carga objetivo estimada.

Este servicio NO genera una sesión y NO usa un LLM.
Solo prepara candidatos reales y explicables de la base de datos.
"""

from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.models import (
    Ejercicio,
    ExerciseFavorite,
    ExerciseOwnership,
)
from app.services.training_load import estimate_exercise_load


SOURCE_OWN = "PROPIO"
SOURCE_FAVORITE = "FAVORITO"
SOURCE_LIBRARY = "BIBLIOTECA"

SOURCE_PRIORITY = {
    SOURCE_OWN: 0,
    SOURCE_FAVORITE: 1,
    SOURCE_LIBRARY: 2,
}


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.casefold().strip().split())


def _exercise_objectives(exercise: Ejercicio) -> list[str]:
    """Obtiene objetivos conocidos del ejercicio sin inventar información."""

    values: list[str] = []

    for value in (
        exercise.objetivo_1_normalizado,
        exercise.objetivo_2_normalizado,
    ):
        if value and value.strip():
            values.append(value.strip())

    # Ejercicios creados con la taxonomía V2 pueden tener objetivos directos.
    for relation in getattr(exercise, "objetivos_v2_directos", []) or []:
        objective = getattr(relation, "objetivo", None)
        name = getattr(objective, "nombre", None)
        if name and name.strip():
            values.append(name.strip())

    # Elimina duplicados conservando el orden.
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        key = _normalize(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value)

    return result


def _objective_matches(
    exercise_objectives: Iterable[str],
    desired_objectives: Iterable[str],
) -> tuple[int, list[str]]:
    desired = [
        (_normalize(value), value.strip())
        for value in desired_objectives
        if value and value.strip()
    ]

    if not desired:
        return 0, []

    available = [
        (_normalize(value), value)
        for value in exercise_objectives
        if value and value.strip()
    ]

    matched: list[str] = []

    for desired_normalized, desired_original in desired:
        if any(
            desired_normalized == available_normalized
            or desired_normalized in available_normalized
            or available_normalized in desired_normalized
            for available_normalized, _ in available
        ):
            matched.append(desired_original)

    return len(matched), matched


def _visible_exercises_for_user(
    db: Session,
    user_id: int,
) -> list[Ejercicio]:
    """
    Devuelve:
    - biblioteca oficial: ejercicio sin fila de ownership;
    - ejercicios propios activos del usuario.

    Excluye ejercicios privados de otros usuarios y ejercicios propios borrados.
    """

    return (
        db.query(Ejercicio)
        .outerjoin(
            ExerciseOwnership,
            ExerciseOwnership.ejercicio_id == Ejercicio.id,
        )
        .filter(
            or_(
                ExerciseOwnership.ejercicio_id.is_(None),
                and_(
                    ExerciseOwnership.created_by_user_id == user_id,
                    ExerciseOwnership.deleted_at.is_(None),
                ),
            )
        )
        .order_by(Ejercicio.id.asc())
        .all()
    )


def select_exercise_candidates(
    db: Session,
    *,
    user_id: int,
    desired_objectives: list[str] | None = None,
    target_load_score: float | None = None,
    limit: int = 12,
) -> list[dict[str, Any]]:
    """
    Selecciona candidatos reales respetando estrictamente la prioridad:

        PROPIO -> FAVORITO -> BIBLIOTECA

    `target_load_score` es opcional y debe estar entre 0 y 100.
    `desired_objectives` puede estar vacío.
    """

    desired_objectives = desired_objectives or []

    if limit <= 0:
        return []

    if target_load_score is not None:
        target_load_score = max(0.0, min(float(target_load_score), 100.0))

    own_ids = {
        row[0]
        for row in (
            db.query(ExerciseOwnership.ejercicio_id)
            .filter(
                ExerciseOwnership.created_by_user_id == user_id,
                ExerciseOwnership.deleted_at.is_(None),
            )
            .all()
        )
    }

    favorite_ids = {
        row[0]
        for row in (
            db.query(ExerciseFavorite.ejercicio_id)
            .filter(ExerciseFavorite.usuario_id == user_id)
            .all()
        )
    }

    exercises = _visible_exercises_for_user(db, user_id)

    candidates: list[dict[str, Any]] = []

    for exercise in exercises:
        if exercise.id in own_ids:
            source = SOURCE_OWN
        elif exercise.id in favorite_ids:
            source = SOURCE_FAVORITE
        else:
            source = SOURCE_LIBRARY

        objectives = _exercise_objectives(exercise)
        match_count, matched_objectives = _objective_matches(
            objectives,
            desired_objectives,
        )

        load = estimate_exercise_load(
            name=exercise.nombre,
            task_type=exercise.tipo.nombre if exercise.tipo else None,
            players=exercise.jugadores,
            space=(
                exercise.espacio.descripcion_original
                if exercise.espacio
                else None
            ),
            time_description=(
                exercise.tiempo.descripcion_original
                if exercise.tiempo
                else None
            ),
            objective_1=exercise.objetivo_1_normalizado,
            objective_2=exercise.objetivo_2_normalizado,
        )

        load_distance = (
            abs(load["score"] - target_load_score)
            if target_load_score is not None
            else 0.0
        )

        reasons: list[str] = []

        if source == SOURCE_OWN:
            reasons.append("Ejercicio creado por el entrenador")
        elif source == SOURCE_FAVORITE:
            reasons.append("Ejercicio marcado como favorito")
        else:
            reasons.append("Ejercicio disponible en la biblioteca SCOUT IA")

        if matched_objectives:
            reasons.append(
                "Coincide con: " + ", ".join(matched_objectives)
            )

        if target_load_score is not None:
            reasons.append(
                f"Carga estimada {load['score']}/100, "
                f"cercana al objetivo {target_load_score:g}/100"
            )

        candidates.append(
            {
                "exercise_id": exercise.id,
                "name": exercise.nombre,
                "source": source,
                "source_priority": SOURCE_PRIORITY[source],
                "task_type": (
                    exercise.tipo.nombre
                    if exercise.tipo
                    else None
                ),
                "players": exercise.jugadores,
                "space": (
                    exercise.espacio.descripcion_original
                    if exercise.espacio
                    else None
                ),
                "time_description": (
                    exercise.tiempo.descripcion_original
                    if exercise.tiempo
                    else None
                ),
                "objectives": objectives,
                "matched_objectives": matched_objectives,
                "objective_match_count": match_count,
                "load_score": load["score"],
                "load_level": load["level"],
                "load_distance": round(load_distance, 1),
                "reasons": reasons,
            }
        )

    candidates.sort(
        key=lambda item: (
            item["source_priority"],
            -item["objective_match_count"],
            item["load_distance"],
            item["exercise_id"],
        )
    )

    return candidates[:limit]
