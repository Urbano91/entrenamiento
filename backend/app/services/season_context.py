from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import PerfilEntrenador, Temporada


def ensure_season_exists(db: Session, season_id: int) -> int:
    exists = db.query(Temporada.id).filter(Temporada.id == season_id).first()
    if not exists:
        raise HTTPException(status_code=422, detail="La temporada indicada no existe")
    return season_id


def active_season_id(db: Session, user_id: int) -> int:
    profile = db.query(PerfilEntrenador).filter(
        PerfilEntrenador.usuario_id == user_id
    ).first()
    if not profile or profile.temporada_actual_id is None:
        raise HTTPException(
            status_code=409,
            detail="Configura una temporada activa antes de planificar",
        )
    return ensure_season_exists(db, profile.temporada_actual_id)


def selected_season_id(
    db: Session, user_id: int, requested_season_id: Optional[int]
) -> int:
    if requested_season_id is not None:
        return ensure_season_exists(db, requested_season_id)
    return active_season_id(db, user_id)
