"""Representación, indexación y similitud de ejercicios."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models.models import (
    Ejercicio,
    EjercicioObjetivoV2,
    ExerciseEmbedding,
    ExerciseOwnership,
    ExerciseRelation,
)
from app.schemas.schemas import EjercicioDraft
from app.services.embeddings import EmbeddingProvider
from app.services.taxonomy import (
    TaxonomyVersionUnavailable,
    exercise_taxonomy_trace,
    get_usable_taxonomy_version,
)


@dataclass(frozen=True)
class ExerciseSemanticDocument:
    name: str
    objectives: tuple[str, ...] = field(default_factory=tuple)
    description: Optional[str] = None
    material: tuple[str, ...] = field(default_factory=tuple)
    players: Optional[int] = None
    space: Optional[str] = None
    duration: Optional[str] = None


@dataclass(frozen=True)
class IndexStats:
    found: int
    existing: int
    generated: int
    skipped: int
    errors: int


def create_similarity_schema(engine: Engine) -> None:
    """Crea exclusivamente las tablas aditivas de esta funcionalidad."""

    tables = [
        ExerciseEmbedding.__table__,
        ExerciseRelation.__table__,
        EjercicioObjetivoV2.__table__,
    ]
    for table in tables:
        table.create(bind=engine, checkfirst=True)


def normalize_representation(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in value.split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines).casefold()


def build_structured_representation(document: ExerciseSemanticDocument) -> str:
    sections: list[tuple[str, list[str]]] = [("NOMBRE", [document.name])]
    if document.objectives:
        sections.append(("OBJETIVOS", sorted(set(document.objectives), key=str.casefold)))
    if document.description:
        sections.append(("DESCRIPCIÓN", [document.description]))
    if document.material:
        sections.append(("MATERIAL", sorted(set(document.material), key=str.casefold)))
    if document.players is not None:
        sections.append(("JUGADORES", [str(document.players)]))
    if document.space:
        sections.append(("ESPACIO", [document.space]))
    if document.duration:
        sections.append(("DURACIÓN", [document.duration]))
    return normalize_representation(
        "\n\n".join(f"{label}:\n" + "\n".join(values) for label, values in sections)
    )


def representation_hash(representation: str) -> str:
    normalized = normalize_representation(representation)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    score = sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)
    return max(0.0, min(1.0, score))


def _objective_names(db: Session, exercise: Ejercicio) -> tuple[str, ...]:
    direct = [row.objetivo.nombre for row in exercise.objetivos_v2_directos]
    if direct:
        return tuple(dict.fromkeys(direct))
    try:
        version = get_usable_taxonomy_version(db)
        traced = exercise_taxonomy_trace(db, version.id, exercise.id)
    except TaxonomyVersionUnavailable:
        traced = []
    names = [row["objetivo_nombre"] for row in traced]
    if not names:
        names = [
            row.objetivo.nombre_normalizado
            for row in exercise.objetivos_asociados
            if row.objetivo is not None
        ]
    return tuple(dict.fromkeys(names))


def document_from_exercise(db: Session, exercise: Ejercicio) -> ExerciseSemanticDocument:
    materials = tuple(
        dict.fromkeys(
            (row.material_original or row.material.nombre_normalizado).strip()
            for row in exercise.materiales_asociados
            if row.material_original or row.material is not None
        )
    )
    return ExerciseSemanticDocument(
        name=exercise.nombre,
        objectives=_objective_names(db, exercise),
        description=exercise.desarrollo,
        material=materials,
        players=exercise.jugadores,
        space=exercise.espacio.descripcion_original if exercise.espacio else None,
        duration=exercise.tiempo.descripcion_original if exercise.tiempo else None,
    )


def document_from_draft(db: Session, draft: EjercicioDraft) -> ExerciseSemanticDocument:
    from app.models.models import Espacio, ObjetivoNormalizadoV2, Tiempo

    objectives = (
        db.query(ObjetivoNormalizadoV2)
        .filter(ObjetivoNormalizadoV2.id.in_(list(dict.fromkeys(draft.objetivo_ids))))
        .order_by(ObjetivoNormalizadoV2.orden)
        .all()
    )
    space = db.get(Espacio, draft.espacio_id)
    duration = db.get(Tiempo, draft.tiempo_id)
    return ExerciseSemanticDocument(
        name=draft.nombre.strip(),
        objectives=tuple(row.nombre for row in objectives),
        description=draft.descripcion,
        material=tuple(item.strip() for item in draft.materiales if item.strip()),
        players=draft.jugadores,
        space=space.descripcion_original if space else None,
        duration=duration.descripcion_original if duration else None,
    )


def ensure_exercise_embedding(
    db: Session,
    exercise: Ejercicio,
    provider: EmbeddingProvider,
) -> tuple[ExerciseEmbedding, bool]:
    representation = build_structured_representation(document_from_exercise(db, exercise))
    source_hash = representation_hash(representation)
    stored = (
        db.query(ExerciseEmbedding)
        .filter(
            ExerciseEmbedding.ejercicio_id == exercise.id,
            ExerciseEmbedding.provider == provider.provider_name,
            ExerciseEmbedding.model == provider.model_name,
        )
        .one_or_none()
    )
    if stored is not None and stored.source_hash == source_hash:
        return stored, False
    vector = provider.embed([representation])[0]
    if stored is None:
        stored = ExerciseEmbedding(
            ejercicio_id=exercise.id,
            provider=provider.provider_name,
            model=provider.model_name,
            embedding=json.dumps(vector, separators=(",", ":")),
            source_hash=source_hash,
        )
        db.add(stored)
    else:
        stored.embedding = json.dumps(vector, separators=(",", ":"))
        stored.source_hash = source_hash
    db.flush()
    return stored, True


def index_all_exercises(db: Session, provider: EmbeddingProvider) -> IndexStats:
    exercises = db.query(Ejercicio).filter(
        ~Ejercicio.ownership.has()
        | Ejercicio.ownership.has(ExerciseOwnership.deleted_at.is_(None))
    ).order_by(Ejercicio.id).all()
    existing = (
        db.query(ExerciseEmbedding)
        .filter(
            ExerciseEmbedding.provider == provider.provider_name,
            ExerciseEmbedding.model == provider.model_name,
        )
        .count()
    )
    generated = skipped = errors = 0
    for exercise in exercises:
        try:
            _, changed = ensure_exercise_embedding(db, exercise, provider)
            db.commit()
            if changed:
                generated += 1
            else:
                skipped += 1
        except Exception:
            db.rollback()
            errors += 1
    return IndexStats(len(exercises), existing, generated, skipped, errors)


def find_similar_exercises(
    db: Session,
    draft: EjercicioDraft,
    provider: EmbeddingProvider,
    *,
    top_k: int = 5,
    exclude_exercise_id: Optional[int] = None,
) -> list[dict]:
    representation = build_structured_representation(
        document_from_draft(db, draft)
    )
    query_vector = provider.embed([representation])[0]

    embedding_rows = (
        db.query(ExerciseEmbedding)
        .filter(
            ExerciseEmbedding.provider == provider.provider_name,
            ExerciseEmbedding.model == provider.model_name,
        )
        .all()
    )

    if not embedding_rows:
        return []

    exercise_ids = [
        row.ejercicio_id
        for row in embedding_rows
        if row.ejercicio_id != exclude_exercise_id
    ]

    if not exercise_ids:
        return []

    exercises = (
        db.query(Ejercicio)
        .filter(Ejercicio.id.in_(exercise_ids))
        .all()
    )

    exercises_by_id = {
        exercise.id: exercise
        for exercise in exercises
    }

    candidates = []

    for stored in embedding_rows:
        if stored.ejercicio_id == exclude_exercise_id:
            continue

        exercise = exercises_by_id.get(stored.ejercicio_id)
        if exercise is None:
            continue

        if (
            exercise.ownership is not None
            and exercise.ownership.deleted_at is not None
        ):
            continue

        try:
            vector = json.loads(stored.embedding)
        except (TypeError, json.JSONDecodeError):
            continue

        candidates.append(
            {
                "exercise_id": exercise.id,
                "name": exercise.nombre,
                "similarity": cosine_similarity(query_vector, vector),
                "owner_user_id": (
                    exercise.ownership.created_by_user_id
                    if exercise.ownership
                    else None
                ),
            }
        )

    candidates.sort(
        key=lambda row: (-row["similarity"], row["exercise_id"])
    )

    results = []

    for candidate in candidates[:top_k]:
        exercise = exercises_by_id[candidate["exercise_id"]]
        document = document_from_exercise(db, exercise)

        candidate.update(
            {
                "objectives": list(document.objectives),
                "description": (document.description or "")[:240] or None,
                "material": list(document.material),
                "players": exercise.jugadores,
                "space": document.space or "",
                "duration": document.duration or "",
            }
        )

        results.append(candidate)

    return results
