import hashlib
import os
from datetime import datetime, timezone
from typing import Annotated, List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import Field
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

from app.db.database import get_db
from app.models.models import (
    CategoriaObjetivo, Ejercicio, EjercicioMaterial, EjercicioObjetivo,
    EjercicioObjetivoV2, EjercicioImagen, Espacio, ExerciseOwnership,
    ExerciseRelation, Imagen, Material, Objetivo, ObjetivoNormalizadoV2,
    PerfilEntrenador, CoachAssignment, Tiempo, TipoTarea, Usuario,
)
from app.schemas.schemas import (
    EjercicioCreate, EjercicioCreateOut, EjercicioDetailOut, EjercicioDraft,
    EjercicioListOut, EjercicioUpdate, PaginatedEjercicios, SimilarExercisesOut,
)
from app.api.auth import get_current_user
from app.services.taxonomy import (
    TaxonomyVersionUnavailable,
    exercise_taxonomy_filter,
    get_usable_taxonomy_version,
)
from app.services.embeddings import EmbeddingProviderError, get_embedding_provider
from app.services.exercise_similarity import (
    ensure_exercise_embedding,
    find_similar_exercises,
)
from app.services.permissions import (
    AccountType, account_type, can_view_exercise, get_visible_exercise,
    require_onboarded_trainer, require_private_exercise_owner,
    visible_exercise_filter,
)

router = APIRouter(prefix="/api/ejercicios", tags=["Ejercicios"], dependencies=[Depends(get_current_user)])

ANIMATIONS_DIR = Path(__file__).resolve().parents[3] / "animations"
IMAGES_DIR = Path(__file__).resolve().parents[3] / "database" / "imagenes"
MAX_EXERCISE_IMAGE_BYTES = 8 * 1024 * 1024


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


def mark_access_metadata(db: Session, exercise: Ejercicio, user: Usuario) -> Ejercicio:
    ownership = exercise.ownership
    exercise.is_official = ownership is None
    exercise.can_edit = bool(
        ownership
        and ownership.deleted_at is None
        and ownership.created_by_user_id == user.id
        and account_type(db, user.id) is AccountType.TRAINER
    )
    exercise.created_by_user_id = ownership.created_by_user_id if ownership else None
    exercise.creator_display = None
    exercise.assignment_context = None
    if ownership is not None:
        profile = db.query(PerfilEntrenador).filter(
            PerfilEntrenador.usuario_id == ownership.created_by_user_id
        ).one_or_none()
        if profile:
            exercise.creator_display = f"{profile.nombre} {profile.apellidos}".strip()
        assignment = db.query(CoachAssignment).filter(
            CoachAssignment.coach_user_id == ownership.created_by_user_id,
            CoachAssignment.active.is_(True),
        ).order_by(CoachAssignment.id.desc()).first()
        if assignment:
            exercise.assignment_context = (
                f"{assignment.category.nombre} · {assignment.club.nombre} · "
                f"{assignment.temporada.nombre}"
            )
    return mark_animation_availability(exercise)


def validate_exercise_draft(draft: EjercicioDraft, db: Session) -> list[ObjetivoNormalizadoV2]:
    if not draft.nombre.strip():
        raise HTTPException(status_code=422, detail="El nombre es obligatorio")
    if db.get(TipoTarea, draft.tipo_tarea_id) is None:
        raise HTTPException(status_code=422, detail="Tipo de tarea no válido")
    if db.get(Espacio, draft.espacio_id) is None:
        raise HTTPException(status_code=422, detail="Espacio no válido")
    if db.get(Tiempo, draft.tiempo_id) is None:
        raise HTTPException(status_code=422, detail="Duración no válida")
    try:
        version = get_usable_taxonomy_version(db)
    except TaxonomyVersionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    category = db.get(CategoriaObjetivo, draft.categoria_objetivo_id)
    if category is None or category.version_id != version.id:
        raise HTTPException(status_code=422, detail="Categoría de objetivos no válida")
    objective_ids = list(dict.fromkeys(draft.objetivo_ids))
    objectives = (
        db.query(ObjetivoNormalizadoV2)
        .filter(
            ObjetivoNormalizadoV2.id.in_(objective_ids),
            ObjetivoNormalizadoV2.version_id == version.id,
            ObjetivoNormalizadoV2.categoria_id == category.id,
            ObjetivoNormalizadoV2.activo.is_(True),
        )
        .order_by(ObjetivoNormalizadoV2.orden)
        .all()
    )
    if len(objectives) != len(objective_ids):
        raise HTTPException(
            status_code=422,
            detail="Todos los objetivos deben pertenecer a la única categoría elegida",
        )
    return objectives


def next_exercise_identity(db: Session) -> tuple[int, str]:
    number = (db.query(func.max(Ejercicio.numero)).scalar() or 0) + 1
    code = f"USR{number}"
    while db.query(Ejercicio.id).filter(Ejercicio.codigo == code).first() is not None:
        number += 1
        code = f"USR{number}"
    return number, code


def image_extension(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    raise HTTPException(status_code=415, detail="La imagen debe ser PNG, JPEG o WebP")


def remove_private_image_if_unused(db: Session, image: Imagen) -> None:
    if db.query(EjercicioImagen).filter(EjercicioImagen.imagen_id == image.id).count():
        return
    if not image.archivo.startswith("entrenadores/"):
        return
    target = (IMAGES_DIR / image.archivo).resolve()
    base = IMAGES_DIR.resolve()
    if base in target.parents and target.is_file():
        target.unlink()
    db.delete(image)

@router.get("", response_model=PaginatedEjercicios)
def list_ejercicios(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
    tipo: Optional[str] = None,
    jugadores: Optional[int] = None,
    objetivo: Optional[str] = None,
    objetivo_v2_id: Optional[int] = Query(
        None,
        ge=1,
        description="ID del objetivo normalizado de la taxonomía V2 usable",
    ),
    objetivo_v2_ids: Optional[List[Annotated[int, Field(ge=1)]]] = Query(
        None,
        description=(
            "IDs repetibles de objetivos normalizados V2. "
            "Coincide con cualquiera de ellos (OR)."
        ),
    ),
    categoria_v2_id: Optional[int] = Query(
        None,
        ge=1,
        description="ID de la categoría de la taxonomía V2 usable",
    ),
    espacio: Optional[str] = None,
    tiempo: Optional[str] = None,
    scope: Optional[str] = Query(None, pattern="^(official|private)$"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    visibility = visible_exercise_filter(db, current_user)
    query = db.query(Ejercicio).filter(visibility)
    if scope == "official":
        query = query.filter(~Ejercicio.ownership.has())
    elif scope == "private":
        query = query.filter(Ejercicio.ownership.has(
            ExerciseOwnership.deleted_at.is_(None)
        ))

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
    selected_objective_ids = list(dict.fromkeys([
        *([] if objetivo_v2_id is None else [objetivo_v2_id]),
        *(objetivo_v2_ids or []),
    ]))
    if selected_objective_ids or categoria_v2_id is not None:
        try:
            taxonomy_version = get_usable_taxonomy_version(db)
        except TaxonomyVersionUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        query = query.filter(
            exercise_taxonomy_filter(
                taxonomy_version.id,
                objetivo_v2_ids=selected_objective_ids or None,
                categoria_v2_id=categoria_v2_id,
            )
        )
    if espacio:
        query = query.filter(Ejercicio.espacio.has(Espacio.descripcion_original == espacio))
    if tiempo:
        query = query.filter(Ejercicio.tiempo.has(Tiempo.descripcion_original == tiempo))
    
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    items = (
        query.order_by(Ejercicio.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    for item in items:
        mark_access_metadata(db, item, current_user)
    official_total = db.query(Ejercicio).filter(~Ejercicio.ownership.has()).count()
    private_total = db.query(Ejercicio).filter(
        visibility,
        Ejercicio.ownership.has(ExerciseOwnership.deleted_at.is_(None)),
    ).count()
    
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "official_total": official_total,
        "my_total": private_total,
    }


@router.post("/similares", response_model=SimilarExercisesOut)
def similares_ejercicios(
    draft: EjercicioDraft,
    exclude_exercise_id: Optional[int] = Query(None, ge=1),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_onboarded_trainer(db, current_user)
    validate_exercise_draft(draft, db)
    if exclude_exercise_id is not None:
        require_private_exercise_owner(db, current_user, exclude_exercise_id)
    try:
        raw_candidates = find_similar_exercises(
            db, draft, get_embedding_provider(), top_k=25,
            exclude_exercise_id=exclude_exercise_id,
        )
    except EmbeddingProviderError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    candidates = []
    private_threshold = float(os.getenv("PRIVATE_SIMILARITY_NOTICE_THRESHOLD", "0.75"))
    for candidate in raw_candidates:
        exercise = db.get(Ejercicio, candidate["exercise_id"])
        if exercise is not None and can_view_exercise(db, current_user, exercise):
            candidate.pop("owner_user_id", None)
            candidate.update(details_visible=True, private_match=False)
            candidates.append(candidate)
        elif (
            candidate["similarity"] >= private_threshold
            and not any(item["private_match"] for item in candidates)
        ):
            candidates.append({
                "exercise_id": None,
                "name": None,
                "similarity": None,
                "objectives": [],
                "description": None,
                "material": [],
                "players": None,
                "space": None,
                "duration": None,
                "details_visible": False,
                "private_match": True,
            })
        if len(candidates) == 5:
            break
    return {"candidates": candidates}


@router.post("", response_model=EjercicioCreateOut, status_code=201)
def create_ejercicio(
    payload: EjercicioCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_onboarded_trainer(db, current_user)
    objectives = validate_exercise_draft(payload, db)
    variant_target = None
    if payload.variant_of_id is not None:
        variant_target = get_visible_exercise(db, current_user, payload.variant_of_id)
    try:
        number, code = next_exercise_identity(db)
        exercise = Ejercicio(
            numero=number,
            codigo=code,
            nombre=payload.nombre.strip(),
            nombre_original=payload.nombre.strip(),
            tipo_tarea_id=payload.tipo_tarea_id,
            jugadores=payload.jugadores,
            espacio_id=payload.espacio_id,
            tiempo_id=payload.tiempo_id,
            desarrollo=(payload.descripcion or "").strip() or None,
        )
        db.add(exercise)
        db.flush()
        db.add(ExerciseOwnership(
            ejercicio_id=exercise.id,
            created_by_user_id=current_user.id,
        ))
        for objective in objectives:
            db.add(EjercicioObjetivoV2(ejercicio_id=exercise.id, objetivo_id=objective.id))
        for material_name in dict.fromkeys(
            item.strip() for item in payload.materiales if item.strip()
        ):
            material = (
                db.query(Material)
                .filter(func.lower(Material.nombre_normalizado) == material_name.casefold())
                .first()
            )
            if material is None:
                material = Material(nombre_normalizado=material_name)
                db.add(material)
                db.flush()
            db.add(
                EjercicioMaterial(
                    ejercicio_id=exercise.id,
                    material_id=material.id,
                    material_original=material_name,
                )
            )
        relation_type = None
        if variant_target is not None:
            relation_type = "VARIANTE_DE"
            db.add(
                ExerciseRelation(
                    source_exercise_id=exercise.id,
                    target_exercise_id=variant_target.id,
                    relation_type=relation_type,
                    created_by=current_user.id,
                )
            )
        db.commit()
        db.refresh(exercise)
    except Exception:
        db.rollback()
        raise

    # La indexación nunca impide guardar una decisión explícita del entrenador.
    # Si el proveedor falla, el script idempotente la completará posteriormente.
    try:
        ensure_exercise_embedding(db, exercise, get_embedding_provider())
        db.commit()
    except Exception:
        db.rollback()
    return {
        "exercise": mark_access_metadata(db, exercise, current_user),
        "relation_type": relation_type,
        "related_exercise_id": variant_target.id if variant_target else None,
    }


def replace_exercise_content(
    db: Session,
    exercise: Ejercicio,
    payload: EjercicioDraft,
    objectives: list[ObjetivoNormalizadoV2],
) -> None:
    exercise.nombre = payload.nombre.strip()
    exercise.nombre_original = payload.nombre.strip()
    exercise.tipo_tarea_id = payload.tipo_tarea_id
    exercise.jugadores = payload.jugadores
    exercise.espacio_id = payload.espacio_id
    exercise.tiempo_id = payload.tiempo_id
    exercise.desarrollo = (payload.descripcion or "").strip() or None
    db.query(EjercicioObjetivoV2).filter(
        EjercicioObjetivoV2.ejercicio_id == exercise.id
    ).delete(synchronize_session=False)
    for objective in objectives:
        db.add(EjercicioObjetivoV2(
            ejercicio_id=exercise.id, objetivo_id=objective.id
        ))
    db.query(EjercicioMaterial).filter(
        EjercicioMaterial.ejercicio_id == exercise.id
    ).delete(synchronize_session=False)
    for material_name in dict.fromkeys(
        item.strip() for item in payload.materiales if item.strip()
    ):
        material = db.query(Material).filter(
            func.lower(Material.nombre_normalizado) == material_name.casefold()
        ).first()
        if material is None:
            material = Material(nombre_normalizado=material_name)
            db.add(material)
            db.flush()
        db.add(EjercicioMaterial(
            ejercicio_id=exercise.id,
            material_id=material.id,
            material_original=material_name,
        ))


@router.put("/{id}", response_model=EjercicioDetailOut)
def update_ejercicio(
    id: int,
    payload: EjercicioUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exercise = require_private_exercise_owner(db, current_user, id)
    objectives = validate_exercise_draft(payload, db)
    replace_exercise_content(db, exercise, payload, objectives)
    exercise.ownership.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(exercise)
    try:
        ensure_exercise_embedding(db, exercise, get_embedding_provider())
        db.commit()
    except Exception:
        db.rollback()
    return mark_access_metadata(db, exercise, current_user)


@router.delete("/{id}", status_code=204)
def delete_ejercicio(
    id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exercise = require_private_exercise_owner(db, current_user, id)
    previous_images = [relation.imagen for relation in exercise.imagenes_asociadas]
    db.query(EjercicioImagen).filter(
        EjercicioImagen.ejercicio_id == exercise.id
    ).delete(synchronize_session=False)
    db.flush()
    for image in previous_images:
        remove_private_image_if_unused(db, image)
    exercise.ownership.deleted_at = datetime.now(timezone.utc)
    exercise.ownership.updated_at = datetime.now(timezone.utc)
    db.commit()
    return None


@router.post("/{id}/imagen", response_model=EjercicioDetailOut)
async def upload_ejercicio_image(
    id: int,
    image: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exercise = require_private_exercise_owner(db, current_user, id)
    data = await image.read(MAX_EXERCISE_IMAGE_BYTES + 1)
    if not data:
        raise HTTPException(status_code=422, detail="La imagen está vacía")
    if len(data) > MAX_EXERCISE_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="La imagen supera el límite de 8 MB")
    extension = image_extension(data)
    digest = hashlib.sha256(data).hexdigest()
    stored = db.query(Imagen).filter(Imagen.sha256 == digest).one_or_none()
    if stored is None:
        relative_path = f"entrenadores/{exercise.id}/{digest}{extension}"
        target = (IMAGES_DIR / relative_path).resolve()
        if IMAGES_DIR.resolve() not in target.parents:
            raise HTTPException(status_code=400, detail="Ruta de imagen no válida")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(data)
        stored = Imagen(archivo=relative_path, sha256=digest)
        db.add(stored)
        db.flush()
    previous = [relation.imagen for relation in exercise.imagenes_asociadas]
    db.query(EjercicioImagen).filter(
        EjercicioImagen.ejercicio_id == exercise.id
    ).delete(synchronize_session=False)
    db.flush()
    db.add(EjercicioImagen(
        ejercicio_id=exercise.id, imagen_id=stored.id, orden=1
    ))
    db.flush()
    for previous_image in previous:
        if previous_image.id != stored.id:
            remove_private_image_if_unused(db, previous_image)
    db.commit()
    db.refresh(exercise)
    return mark_access_metadata(db, exercise, current_user)


@router.delete("/{id}/imagen", status_code=204)
def delete_ejercicio_image(
    id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exercise = require_private_exercise_owner(db, current_user, id)
    previous = [relation.imagen for relation in exercise.imagenes_asociadas]
    db.query(EjercicioImagen).filter(
        EjercicioImagen.ejercicio_id == exercise.id
    ).delete(synchronize_session=False)
    db.flush()
    for image in previous:
        remove_private_image_if_unused(db, image)
    db.commit()
    return None

@router.get("/{id}/animacion")
def get_animacion(
    id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_visible_exercise(db, current_user, id)

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
def get_portada(
    id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_visible_exercise(db, current_user, id)

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
def get_ejercicio(
    id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ejercicio = get_visible_exercise(db, current_user, id)
    return mark_access_metadata(db, ejercicio, current_user)
