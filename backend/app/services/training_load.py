"""Motor V1 de estimación de carga para SCOUT IA.

IMPORTANTE:
- Es una estimación previa de la sesión.
- No representa carga fisiológica real.
- No sustituye GPS, frecuencia cardiaca, RPE ni valoración profesional.
- El cálculo es determinista y explicable.
"""

from __future__ import annotations

import re
from typing import Any


# ============================================================
# CONFIGURACIÓN V1
# ============================================================

TASK_TYPE_SCORES = {
    "ABP": 35,
    "Acción Combinada": 55,
    "Ataque/Defensa": 75,
    "Circuito": 80,
    "Juego de Posesión": 75,
    "Juego de Posición": 75,
    "Juego lúdico": 45,
    "Partido Condicionado": 90,
    "Rondo": 60,
    "Rueda de pase": 45,
}


HIGH_DEMAND_KEYWORDS = {
    "fuerza",
    "fuerza explosiva",
    "fuerza resistencia",
    "pressing",
    "presión",
    "velocidad de reacción",
    "cambio de chip",
}

MEDIUM_DEMAND_KEYWORDS = {
    "finalización",
    "progresión",
    "movilidad",
    "coordinación",
    "regate",
    "juego real",
    "orientación de la presión",
}


# ============================================================
# TIEMPO
# ============================================================

def parse_time_description(description: str | None) -> dict[str, float]:
    if not description:
        return {
            "work_minutes": 0.0,
            "rest_minutes": 0.0,
            "total_minutes": 0.0,
            "density": 1.0,
        }

    text = description.strip().lower()

    interval_match = re.search(
        r"trabajo\s*(\d+(?:[.,]\d+)?)'\s*"
        r"descanso\s*(\d+(?:[.,]\d+)?)''\s*"
        r"\((\d+)\)",
        text,
        re.IGNORECASE,
    )

    if interval_match:
        work_per_rep = float(interval_match.group(1).replace(",", "."))
        rest_seconds = float(interval_match.group(2).replace(",", "."))
        repetitions = int(interval_match.group(3))

        work_minutes = work_per_rep * repetitions
        rests = max(repetitions - 1, 0)
        rest_minutes = (rest_seconds / 60.0) * rests
        total_minutes = work_minutes + rest_minutes

        density = (
            work_minutes / total_minutes
            if total_minutes > 0
            else 1.0
        )

        return {
            "work_minutes": round(work_minutes, 2),
            "rest_minutes": round(rest_minutes, 2),
            "total_minutes": round(total_minutes, 2),
            "density": round(density, 3),
        }

    series_match = re.search(
        r"(\d+)\s*series?\s*de\s*(\d+(?:[.,]\d+)?)'",
        text,
        re.IGNORECASE,
    )

    if series_match:
        series = int(series_match.group(1))
        minutes_per_series = float(series_match.group(2).replace(",", "."))

        work_minutes = series * minutes_per_series

        return {
            "work_minutes": round(work_minutes, 2),
            "rest_minutes": 0.0,
            "total_minutes": round(work_minutes, 2),
            "density": 1.0,
        }

    simple_match = re.search(
        r"(\d+(?:[.,]\d+)?)'",
        text,
    )

    if simple_match:
        minutes = float(simple_match.group(1).replace(",", "."))

        return {
            "work_minutes": round(minutes, 2),
            "rest_minutes": 0.0,
            "total_minutes": round(minutes, 2),
            "density": 1.0,
        }

    return {
        "work_minutes": 0.0,
        "rest_minutes": 0.0,
        "total_minutes": 0.0,
        "density": 1.0,
    }


# ============================================================
# ESPACIO
# ============================================================

def parse_space_area(description: str | None) -> float | None:
    if not description:
        return None

    text = (
        description.lower()
        .replace("metros", "")
        .replace("metro", "")
        .replace(".", "")
        .strip()
    )

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*x\s*(\d+(?:[.,]\d+)?)",
        text,
    )

    if not match:
        return None

    width = float(match.group(1).replace(",", "."))
    height = float(match.group(2).replace(",", "."))

    return round(width * height, 2)


def space_score(
    space_description: str | None,
    players: int | None,
) -> tuple[float, float | None]:
    area = parse_space_area(space_description)

    if area is None or not players or players <= 0:
        return 50.0, None

    area_per_player = area / players

    if area_per_player <= 10:
        score = 55
    elif area_per_player <= 25:
        score = 60
    elif area_per_player <= 50:
        score = 70
    elif area_per_player <= 80:
        score = 80
    else:
        score = 85

    return float(score), round(area_per_player, 2)


# ============================================================
# OBJETIVOS
# ============================================================

def objective_score(
    objective_1: str | None,
    objective_2: str | None,
) -> float:
    objectives = [
        value.strip().casefold()
        for value in (objective_1, objective_2)
        if value and value.strip()
    ]

    if not objectives:
        return 50.0

    joined = " | ".join(objectives)

    if any(keyword.casefold() in joined for keyword in HIGH_DEMAND_KEYWORDS):
        return 90.0

    if any(keyword.casefold() in joined for keyword in MEDIUM_DEMAND_KEYWORDS):
        return 70.0

    return 50.0


# ============================================================
# DURACIÓN + DENSIDAD
# ============================================================

def duration_density_score(time_description: str | None) -> tuple[float, dict]:
    parsed = parse_time_description(time_description)

    work_minutes = parsed["work_minutes"]
    density = parsed["density"]

    duration_component = min(
        (work_minutes / 25.0) * 100.0,
        100.0,
    )

    density_component = density * 100.0

    score = (
        duration_component * 0.75
        + density_component * 0.25
    )

    return round(score, 2), parsed


# ============================================================
# CARGA DE UN EJERCICIO
# ============================================================

def estimate_exercise_load(
    *,
    name: str,
    task_type: str | None,
    players: int | None,
    space: str | None,
    time_description: str | None,
    objective_1: str | None = None,
    objective_2: str | None = None,
) -> dict[str, Any]:

    temporal_score, temporal_data = duration_density_score(
        time_description
    )

    task_score = float(
        TASK_TYPE_SCORES.get(task_type or "", 50)
    )

    spatial_score, area_per_player = space_score(
        space,
        players,
    )

    objectives_score = objective_score(
        objective_1,
        objective_2,
    )

    score = (
        temporal_score * 0.35
        + task_score * 0.30
        + spatial_score * 0.20
        + objectives_score * 0.15
    )

    # Ajuste V1 para circuitos intensos cortos.
    if task_type == "Circuito" and objectives_score >= 90:
        score += 5

    score = round(max(0.0, min(score, 100.0)), 1)

    reasons: list[str] = []

    work_minutes = temporal_data["work_minutes"]

    if work_minutes:
        reasons.append(
            f"{work_minutes:g} minutos de trabajo efectivo"
        )

    if task_type:
        reasons.append(
            f"tarea de tipo {task_type}"
        )

    if area_per_player is not None:
        reasons.append(
            f"{area_per_player:g} m² aproximadamente por jugador"
        )

    if objectives_score >= 90:
        reasons.append(
            "objetivos asociados a una demanda elevada"
        )
    elif objectives_score >= 70:
        reasons.append(
            "objetivos con demanda moderada"
        )

    return {
        "name": name,
        "score": score,
        "level": load_level(score),
        "work_minutes": temporal_data["work_minutes"],
        "rest_minutes": temporal_data["rest_minutes"],
        "density": temporal_data["density"],
        "area_per_player": area_per_player,
        "components": {
            "duration_density": temporal_score,
            "task_type": task_score,
            "space": spatial_score,
            "objectives": objectives_score,
        },
        "reasons": reasons,
    }


# ============================================================
# CARGA DE ENTRENAMIENTO COMPLETO
# ============================================================

def estimate_training_load(
    *,
    exercises: list[dict[str, Any]],
    training_duration_minutes: int | None = None,
) -> dict[str, Any]:

    if not exercises:
        return {
            "score": 0.0,
            "level": "SIN DATOS",
            "exercise_loads": [],
            "reasons": [
                "No hay ejercicios suficientes para estimar la carga"
            ],
        }

    exercise_loads = [
        estimate_exercise_load(
            name=exercise["name"],
            task_type=exercise.get("task_type"),
            players=exercise.get("players"),
            space=exercise.get("space"),
            time_description=exercise.get("time_description"),
            objective_1=exercise.get("objective_1"),
            objective_2=exercise.get("objective_2"),
        )
        for exercise in exercises
    ]

    total_work_minutes = sum(
        item["work_minutes"]
        for item in exercise_loads
    )

    if total_work_minutes > 0:
        exercise_score = sum(
            item["score"] * item["work_minutes"]
            for item in exercise_loads
        ) / total_work_minutes
    else:
        exercise_score = sum(
            item["score"]
            for item in exercise_loads
        ) / len(exercise_loads)

    if training_duration_minutes and training_duration_minutes > 0:
        session_duration_score = min(
            (training_duration_minutes / 90.0) * 100.0,
            100.0,
        )

        final_score = (
            exercise_score * 0.75
            + session_duration_score * 0.25
        )
    else:
        final_score = exercise_score

    final_score = round(
        max(0.0, min(final_score, 100.0)),
        1,
    )

    reasons = build_training_reasons(
        exercise_loads=exercise_loads,
        training_duration_minutes=training_duration_minutes,
    )

    return {
        "score": final_score,
        "level": load_level(final_score),
        "total_work_minutes": round(total_work_minutes, 1),
        "training_duration_minutes": training_duration_minutes,
        "exercise_loads": exercise_loads,
        "reasons": reasons,
    }


# ============================================================
# EXPLICACIÓN DE LA SESIÓN
# ============================================================

def build_training_reasons(
    *,
    exercise_loads: list[dict[str, Any]],
    training_duration_minutes: int | None,
) -> list[str]:

    reasons: list[str] = []

    if training_duration_minutes:
        reasons.append(
            f"{training_duration_minutes} minutos de duración total"
        )

    high_tasks = [
        item
        for item in exercise_loads
        if item["score"] >= 70
    ]

    if len(high_tasks) >= 2:
        reasons.append(
            "acumulación de varias tareas de exigencia elevada"
        )

    game_tasks = [
        item
        for item in exercise_loads
        if item["components"]["task_type"] >= 75
    ]

    if len(game_tasks) >= 2:
        reasons.append(
            "predominio de tareas de alta participación"
        )

    high_density_tasks = [
        item
        for item in exercise_loads
        if item["density"] >= 0.85
    ]

    if len(high_density_tasks) >= 2:
        reasons.append(
            "alta densidad de trabajo en varios ejercicios"
        )

    if not reasons:
        reasons.append(
            "estimación calculada a partir de la composición de la sesión"
        )

    return reasons


# ============================================================
# NIVEL VISUAL
# ============================================================

def load_level(score: float) -> str:
    if score < 40:
        return "BAJA"

    if score < 70:
        return "MODERADA"

    return "ALTA"
