"""Eliminación transaccional de una cuenta de entrenador y sus datos privados."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.models import (
    Club,
    CoachAssignment,
    DocumentoPlanificacion,
    Ejercicio,
    EjercicioImagen,
    EjercicioMaterial,
    EjercicioObjetivo,
    EjercicioObjetivoV2,
    Entrenamiento,
    EntrenamientoEjercicio,
    ExerciseEmbedding,
    ExerciseOwnership,
    ExerciseRelation,
    Imagen,
    MapeoExcepcionDestino,
    MapeoObjetivoExcepcion,
    Partido,
    PerfilEntrenador,
    PlanificacionDiaria,
    TextoOriginal,
    Usuario,
)
from app.services.storage import StorageService


IMAGES_DIR = Path(__file__).resolve().parents[3] / "database" / "imagenes"


def _bulk_delete(query) -> None:
    query.delete(synchronize_session=False)


def delete_trainer_user(
    db: Session,
    target: Usuario,
    storage: StorageService,
) -> dict[str, int]:
    """Borra al entrenador y sus datos propios en una única transacción.

    Los documentos e imágenes se conservan temporalmente en memoria para poder
    restaurarlos si la transacción de base de datos no llega a confirmarse.
    """

    target_id = target.id
    private_exercise_ids = [
        row[0]
        for row in db.query(ExerciseOwnership.ejercicio_id).filter(
            ExerciseOwnership.created_by_user_id == target_id
        ).all()
    ]
    training_ids = [
        row[0]
        for row in db.query(Entrenamiento.id).filter(
            Entrenamiento.usuario_id == target_id
        ).all()
    ]
    match_ids = [
        row[0]
        for row in db.query(Partido.id).filter(Partido.usuario_id == target_id).all()
    ]
    plan_ids = [
        row[0]
        for row in db.query(PlanificacionDiaria.id).filter(
            PlanificacionDiaria.usuario_id == target_id
        ).all()
    ]

    document_query = db.query(DocumentoPlanificacion).filter(
        or_(
            DocumentoPlanificacion.usuario_id == target_id,
            DocumentoPlanificacion.planificacion_id.in_(plan_ids or [-1]),
            DocumentoPlanificacion.partido_id.in_(match_ids or [-1]),
        )
    )
    documents = document_query.all()
    document_backups: dict[str, bytes] = {}
    for document in documents:
        try:
            with storage.open(document.storage_key) as handle:
                document_backups[document.storage_key] = handle.read()
        except FileNotFoundError:
            pass

    image_rows = (
        db.query(Imagen)
        .join(EjercicioImagen, EjercicioImagen.imagen_id == Imagen.id)
        .filter(EjercicioImagen.ejercicio_id.in_(private_exercise_ids or [-1]))
        .distinct()
        .all()
    )
    image_backups: dict[Path, bytes] = {}
    for image in image_rows:
        if not image.archivo.startswith("entrenadores/"):
            continue
        path = (IMAGES_DIR / image.archivo).resolve()
        if IMAGES_DIR.resolve() in path.parents and path.is_file():
            image_backups[path] = path.read_bytes()

    deleted_files = False
    try:
        _bulk_delete(document_query)
        _bulk_delete(
            db.query(PlanificacionDiaria).filter(
                PlanificacionDiaria.usuario_id == target_id
            )
        )
        _bulk_delete(db.query(Partido).filter(Partido.usuario_id == target_id))

        _bulk_delete(
            db.query(EntrenamientoEjercicio).filter(
                or_(
                    EntrenamientoEjercicio.entrenamiento_id.in_(training_ids or [-1]),
                    EntrenamientoEjercicio.ejercicio_id.in_(private_exercise_ids or [-1]),
                )
            )
        )
        _bulk_delete(
            db.query(Entrenamiento).filter(Entrenamiento.usuario_id == target_id)
        )

        exception_ids = [
            row[0]
            for row in db.query(MapeoObjetivoExcepcion.id).filter(
                MapeoObjetivoExcepcion.ejercicio_id.in_(private_exercise_ids or [-1])
            ).all()
        ]
        _bulk_delete(
            db.query(MapeoExcepcionDestino).filter(
                MapeoExcepcionDestino.excepcion_id.in_(exception_ids or [-1])
            )
        )
        _bulk_delete(
            db.query(MapeoObjetivoExcepcion).filter(
                MapeoObjetivoExcepcion.id.in_(exception_ids or [-1])
            )
        )
        _bulk_delete(
            db.query(ExerciseRelation).filter(
                or_(
                    ExerciseRelation.created_by == target_id,
                    ExerciseRelation.source_exercise_id.in_(private_exercise_ids or [-1]),
                    ExerciseRelation.target_exercise_id.in_(private_exercise_ids or [-1]),
                )
            )
        )
        for model in (
            ExerciseEmbedding,
            EjercicioObjetivoV2,
            EjercicioObjetivo,
            EjercicioMaterial,
            TextoOriginal,
        ):
            _bulk_delete(
                db.query(model).filter(
                    model.ejercicio_id.in_(private_exercise_ids or [-1])
                )
            )
        _bulk_delete(
            db.query(EjercicioImagen).filter(
                EjercicioImagen.ejercicio_id.in_(private_exercise_ids or [-1])
            )
        )
        db.flush()
        for image in image_rows:
            if not db.query(EjercicioImagen).filter(
                EjercicioImagen.imagen_id == image.id
            ).first() and image.archivo.startswith("entrenadores/"):
                db.delete(image)

        _bulk_delete(
            db.query(ExerciseOwnership).filter(
                ExerciseOwnership.created_by_user_id == target_id
            )
        )
        _bulk_delete(
            db.query(Ejercicio).filter(Ejercicio.id.in_(private_exercise_ids or [-1]))
        )
        _bulk_delete(
            db.query(CoachAssignment).filter(
                CoachAssignment.coach_user_id == target_id
            )
        )
        _bulk_delete(
            db.query(PerfilEntrenador).filter(
                PerfilEntrenador.usuario_id == target_id
            )
        )
        db.delete(target)
        db.flush()

        deleted_files = True
        for key in document_backups:
            storage.delete(key)
        for path in image_backups:
            if path.exists():
                path.unlink()
        db.commit()
    except Exception:
        db.rollback()
        if deleted_files:
            for key, content in document_backups.items():
                try:
                    storage.save(key, content)
                except FileExistsError:
                    pass
            for path, content in image_backups.items():
                if not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(content)
        raise

    return {
        "trainings": len(training_ids),
        "matches": len(match_ids),
        "private_exercises": len(private_exercise_ids),
    }


def delete_club_account(db: Session, club: Club) -> dict[str, int]:
    """Elimina el club y su cuenta, conservando las cuentas de entrenadores."""

    club_id = club.id
    owner = club.owner
    assignments = db.query(CoachAssignment).filter(
        CoachAssignment.club_id == club_id
    ).all()
    coach_ids = {assignment.coach_user_id for assignment in assignments}
    try:
        _bulk_delete(
            db.query(CoachAssignment).filter(CoachAssignment.club_id == club_id)
        )
        db.flush()
        for coach_id in coach_ids:
            profile = db.query(PerfilEntrenador).filter(
                PerfilEntrenador.usuario_id == coach_id
            ).one_or_none()
            if profile is None or profile.club_actual != club.nombre:
                continue
            other_assignment = db.query(CoachAssignment).filter(
                CoachAssignment.coach_user_id == coach_id,
                CoachAssignment.club_id.is_not(None),
                CoachAssignment.active.is_(True),
            ).order_by(CoachAssignment.id.desc()).first()
            profile.club_actual = (
                other_assignment.club.nombre if other_assignment else None
            )
        db.delete(club)
        db.flush()
        db.delete(owner)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"assignments": len(assignments), "trainers_preserved": len(coach_ids)}
