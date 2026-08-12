from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.models import (
    CategoriaObjetivo,
    Ejercicio,
    ObjetivoNormalizadoV2,
    TaxonomiaObjetivoVersion,
)
from app.schemas.schemas import (
    CategoriaObjetivoV2Out,
    ObjetivoNormalizadoV2Out,
    ObjetivoV2TrazabilidadOut,
)
from app.services.taxonomy import (
    TaxonomyVersionUnavailable,
    exercise_taxonomy_trace,
    get_usable_taxonomy_version,
)
from app.services.permissions import get_visible_exercise
from app.models.models import Usuario


router = APIRouter(
    prefix="/api/taxonomia",
    tags=["Taxonomía V2"],
    dependencies=[Depends(get_current_user)],
)


def usable_version(db: Session = Depends(get_db)) -> TaxonomiaObjetivoVersion:
    try:
        return get_usable_taxonomy_version(db)
    except TaxonomyVersionUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def objective_rows(
    db: Session,
    version_id: int,
    categoria_id: Optional[int] = None,
) -> list[dict]:
    query = (
        db.query(
            ObjetivoNormalizadoV2.id.label("id"),
            ObjetivoNormalizadoV2.nombre.label("nombre"),
            ObjetivoNormalizadoV2.categoria_id.label("categoria_id"),
            CategoriaObjetivo.codigo.label("categoria_codigo"),
            CategoriaObjetivo.nombre.label("categoria_nombre"),
            ObjetivoNormalizadoV2.orden.label("orden"),
        )
        .join(
            CategoriaObjetivo,
            CategoriaObjetivo.id == ObjetivoNormalizadoV2.categoria_id,
        )
        .filter(
            ObjetivoNormalizadoV2.version_id == version_id,
            CategoriaObjetivo.version_id == version_id,
            ObjetivoNormalizadoV2.activo.is_(True),
        )
    )
    if categoria_id is not None:
        query = query.filter(ObjetivoNormalizadoV2.categoria_id == categoria_id)
    rows = query.order_by(
        CategoriaObjetivo.orden, ObjetivoNormalizadoV2.orden
    ).all()
    return [dict(row._mapping) for row in rows]


@router.get("/categorias", response_model=List[CategoriaObjetivoV2Out])
def get_categorias(
    db: Session = Depends(get_db),
    version: TaxonomiaObjetivoVersion = Depends(usable_version),
):
    return (
        db.query(CategoriaObjetivo)
        .filter(CategoriaObjetivo.version_id == version.id)
        .order_by(CategoriaObjetivo.orden)
        .all()
    )


@router.get("/objetivos", response_model=List[ObjetivoNormalizadoV2Out])
def get_objetivos(
    categoria_id: Optional[int] = Query(
        None, ge=1, description="Limita los objetivos a una categoría V2"
    ),
    db: Session = Depends(get_db),
    version: TaxonomiaObjetivoVersion = Depends(usable_version),
):
    return objective_rows(db, version.id, categoria_id)


@router.get(
    "/categorias/{categoria_id}/objetivos",
    response_model=List[ObjetivoNormalizadoV2Out],
)
def get_objetivos_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    version: TaxonomiaObjetivoVersion = Depends(usable_version),
):
    category_exists = (
        db.query(CategoriaObjetivo.id)
        .filter(
            CategoriaObjetivo.id == categoria_id,
            CategoriaObjetivo.version_id == version.id,
        )
        .first()
    )
    if category_exists is None:
        raise HTTPException(status_code=404, detail="Categoría V2 no encontrada")
    return objective_rows(db, version.id, categoria_id)


@router.get(
    "/objetivos/{objetivo_id}", response_model=ObjetivoNormalizadoV2Out
)
def get_objetivo(
    objetivo_id: int,
    db: Session = Depends(get_db),
    version: TaxonomiaObjetivoVersion = Depends(usable_version),
):
    rows = (
        db.query(
            ObjetivoNormalizadoV2.id.label("id"),
            ObjetivoNormalizadoV2.nombre.label("nombre"),
            ObjetivoNormalizadoV2.categoria_id.label("categoria_id"),
            CategoriaObjetivo.codigo.label("categoria_codigo"),
            CategoriaObjetivo.nombre.label("categoria_nombre"),
            ObjetivoNormalizadoV2.orden.label("orden"),
        )
        .join(
            CategoriaObjetivo,
            CategoriaObjetivo.id == ObjetivoNormalizadoV2.categoria_id,
        )
        .filter(
            ObjetivoNormalizadoV2.id == objetivo_id,
            ObjetivoNormalizadoV2.version_id == version.id,
            CategoriaObjetivo.version_id == version.id,
            ObjetivoNormalizadoV2.activo.is_(True),
        )
        .first()
    )
    if rows is None:
        raise HTTPException(status_code=404, detail="Objetivo V2 no encontrado")
    return dict(rows._mapping)


@router.get(
    "/ejercicios/{ejercicio_id}/objetivos",
    response_model=List[ObjetivoV2TrazabilidadOut],
)
def get_trazabilidad_ejercicio(
    ejercicio_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
    version: TaxonomiaObjetivoVersion = Depends(usable_version),
):
    get_visible_exercise(db, current_user, ejercicio_id)
    return exercise_taxonomy_trace(db, version.id, ejercicio_id)
