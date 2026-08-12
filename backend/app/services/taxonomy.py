"""Consultas de solo lectura para la taxonomía de objetivos V2."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

from sqlalchemy import and_, exists, not_, or_
from sqlalchemy.orm import Session, aliased

from app.models.models import (
    CategoriaObjetivo,
    Ejercicio,
    EjercicioObjetivo,
    EjercicioObjetivoV2,
    MapeoExcepcionDestino,
    MapeoObjetivo,
    MapeoObjetivoDestino,
    MapeoObjetivoExcepcion,
    ObjetivoNormalizadoV2,
    TaxonomiaObjetivoVersion,
)


class TaxonomyVersionUnavailable(RuntimeError):
    """No existe una única versión que la API pueda consultar con seguridad."""


def get_usable_taxonomy_version(db: Session) -> TaxonomiaObjetivoVersion:
    """Devuelve ACTIVA o, mientras V2 no se active, el único borrador usable.

    La versión ACTIVA siempre tiene prioridad. La migración actual deja V2 en
    BORRADOR de forma intencionada; se admite ese estado únicamente cuando es
    la única versión no retirada. Si hubiera más de una candidata sin una
    versión ACTIVA, la selección sería ambigua y la API se detiene con 503.
    """

    active = (
        db.query(TaxonomiaObjetivoVersion)
        .filter(TaxonomiaObjetivoVersion.estado == "ACTIVA")
        .one_or_none()
    )
    if active is not None:
        return active

    candidates = (
        db.query(TaxonomiaObjetivoVersion)
        .filter(TaxonomiaObjetivoVersion.estado.in_(("APROBADA", "BORRADOR")))
        .order_by(TaxonomiaObjetivoVersion.id.desc())
        .all()
    )
    if len(candidates) != 1:
        raise TaxonomyVersionUnavailable(
            "No existe una versión ACTIVA ni una única versión V2 usable"
        )
    return candidates[0]


def exercise_taxonomy_filter(
    version_id: int,
    *,
    objetivo_v2_id: Optional[int] = None,
    objetivo_v2_ids: Optional[Sequence[int]] = None,
    categoria_v2_id: Optional[int] = None,
):
    """Construye un EXISTS correlacionado sin multiplicar ejercicios."""

    selected_objective_ids = tuple(dict.fromkeys([
        *([] if objetivo_v2_id is None else [objetivo_v2_id]),
        *(objetivo_v2_ids or []),
    ]))
    if not selected_objective_ids and categoria_v2_id is None:
        raise ValueError("Se requiere objetivo_v2_id o categoria_v2_id")

    source_relation = aliased(EjercicioObjetivo)
    mapping = aliased(MapeoObjetivo)
    global_destination = aliased(MapeoObjetivoDestino)
    global_objective = aliased(ObjetivoNormalizadoV2)
    overriding_exception = aliased(MapeoObjetivoExcepcion)

    global_target_conditions = [
        global_objective.version_id == version_id,
        global_objective.activo.is_(True),
    ]
    if selected_objective_ids:
        global_target_conditions.append(
            global_objective.id.in_(selected_objective_ids)
        )
    if categoria_v2_id is not None:
        global_target_conditions.append(
            global_objective.categoria_id == categoria_v2_id
        )

    exact_exception_exists = exists().where(
        and_(
            overriding_exception.version_id == version_id,
            overriding_exception.mapeo_id == mapping.id,
            overriding_exception.ejercicio_id == source_relation.ejercicio_id,
            overriding_exception.objetivo_origen_id
            == source_relation.objetivo_id,
            overriding_exception.tipo_objetivo
            == source_relation.tipo_objetivo,
        )
    )

    global_match = exists().where(
        and_(
            source_relation.ejercicio_id == Ejercicio.id,
            mapping.version_id == version_id,
            mapping.objetivo_origen_id == source_relation.objetivo_id,
            global_destination.mapeo_id == mapping.id,
            global_objective.id
            == global_destination.objetivo_normalizado_id,
            *global_target_conditions,
            not_(exact_exception_exists),
        )
    )

    exception = aliased(MapeoObjetivoExcepcion)
    exception_destination = aliased(MapeoExcepcionDestino)
    exception_objective = aliased(ObjetivoNormalizadoV2)
    exception_target_conditions = [
        exception_objective.version_id == version_id,
        exception_objective.activo.is_(True),
    ]
    if selected_objective_ids:
        exception_target_conditions.append(
            exception_objective.id.in_(selected_objective_ids)
        )
    if categoria_v2_id is not None:
        exception_target_conditions.append(
            exception_objective.categoria_id == categoria_v2_id
        )

    exception_match = exists().where(
        and_(
            exception.version_id == version_id,
            exception.ejercicio_id == Ejercicio.id,
            exception_destination.excepcion_id == exception.id,
            exception_objective.id
            == exception_destination.objetivo_normalizado_id,
            *exception_target_conditions,
        )
    )

    direct_relation = aliased(EjercicioObjetivoV2)
    direct_objective = aliased(ObjetivoNormalizadoV2)
    direct_conditions = [
        direct_relation.ejercicio_id == Ejercicio.id,
        direct_objective.id == direct_relation.objetivo_id,
        direct_objective.version_id == version_id,
        direct_objective.activo.is_(True),
    ]
    if selected_objective_ids:
        direct_conditions.append(direct_objective.id.in_(selected_objective_ids))
    if categoria_v2_id is not None:
        direct_conditions.append(direct_objective.categoria_id == categoria_v2_id)
    direct_match = exists().where(and_(*direct_conditions))

    return or_(global_match, exception_match, direct_match)


def exercise_taxonomy_trace(
    db: Session, version_id: int, ejercicio_id: int
) -> list[dict]:
    """Obtiene cada procedencia V2 con su objetivo original y rol histórico."""

    relation = aliased(EjercicioObjetivo)
    mapping = aliased(MapeoObjetivo)
    destination = aliased(MapeoObjetivoDestino)
    objective = aliased(ObjetivoNormalizadoV2)
    category = aliased(CategoriaObjetivo)
    overriding_exception = aliased(MapeoObjetivoExcepcion)

    exact_exception_exists = exists().where(
        and_(
            overriding_exception.version_id == version_id,
            overriding_exception.mapeo_id == mapping.id,
            overriding_exception.ejercicio_id == relation.ejercicio_id,
            overriding_exception.objetivo_origen_id == relation.objetivo_id,
            overriding_exception.tipo_objetivo == relation.tipo_objetivo,
        )
    )

    global_rows = (
        db.query(
            objective.id.label("objetivo_id"),
            objective.nombre.label("objetivo_nombre"),
            category.id.label("categoria_id"),
            category.codigo.label("categoria_codigo"),
            category.nombre.label("categoria_nombre"),
            mapping.objetivo_origen_id.label("objetivo_origen_id"),
            relation.objetivo_original.label("objetivo_original"),
            relation.tipo_objetivo.label("rol_historico"),
            category.orden.label("categoria_orden"),
            objective.orden.label("objetivo_orden"),
        )
        .select_from(relation)
        .join(
            mapping,
            and_(
                mapping.version_id == version_id,
                mapping.objetivo_origen_id == relation.objetivo_id,
            ),
        )
        .join(destination, destination.mapeo_id == mapping.id)
        .join(objective, objective.id == destination.objetivo_normalizado_id)
        .join(category, category.id == objective.categoria_id)
        .filter(
            relation.ejercicio_id == ejercicio_id,
            objective.version_id == version_id,
            objective.activo.is_(True),
            not_(exact_exception_exists),
        )
        .all()
    )

    exception = aliased(MapeoObjetivoExcepcion)
    exception_relation = aliased(EjercicioObjetivo)
    exception_destination = aliased(MapeoExcepcionDestino)
    exception_objective = aliased(ObjetivoNormalizadoV2)
    exception_category = aliased(CategoriaObjetivo)

    exception_rows = (
        db.query(
            exception_objective.id.label("objetivo_id"),
            exception_objective.nombre.label("objetivo_nombre"),
            exception_category.id.label("categoria_id"),
            exception_category.codigo.label("categoria_codigo"),
            exception_category.nombre.label("categoria_nombre"),
            exception.objetivo_origen_id.label("objetivo_origen_id"),
            exception_relation.objetivo_original.label("objetivo_original"),
            exception_relation.tipo_objetivo.label("rol_historico"),
            exception_category.orden.label("categoria_orden"),
            exception_objective.orden.label("objetivo_orden"),
        )
        .select_from(exception)
        .join(
            exception_relation,
            and_(
                exception_relation.ejercicio_id == exception.ejercicio_id,
                exception_relation.objetivo_id == exception.objetivo_origen_id,
                exception_relation.tipo_objetivo == exception.tipo_objetivo,
            ),
        )
        .join(
            exception_destination,
            exception_destination.excepcion_id == exception.id,
        )
        .join(
            exception_objective,
            exception_objective.id
            == exception_destination.objetivo_normalizado_id,
        )
        .join(
            exception_category,
            exception_category.id == exception_objective.categoria_id,
        )
        .filter(
            exception.version_id == version_id,
            exception.ejercicio_id == ejercicio_id,
            exception_objective.version_id == version_id,
            exception_objective.activo.is_(True),
        )
        .all()
    )

    rows = [
        {
            "objetivo_id": row[0],
            "objetivo_nombre": row[1],
            "categoria_id": row[2],
            "categoria_codigo": row[3],
            "categoria_nombre": row[4],
            "objetivo_origen_id": row[5],
            "objetivo_original": row[6],
            "rol_historico": row[7],
            "alcance": scope,
            "categoria_orden": row[8],
            "objetivo_orden": row[9],
        }
        for source_rows, scope in ((global_rows, "global"), (exception_rows, "excepcion"))
        for row in source_rows
    ]

    direct_rows = (
        db.query(
            ObjetivoNormalizadoV2.id.label("objetivo_id"),
            ObjetivoNormalizadoV2.nombre.label("objetivo_nombre"),
            CategoriaObjetivo.id.label("categoria_id"),
            CategoriaObjetivo.codigo.label("categoria_codigo"),
            CategoriaObjetivo.nombre.label("categoria_nombre"),
            CategoriaObjetivo.orden.label("categoria_orden"),
            ObjetivoNormalizadoV2.orden.label("objetivo_orden"),
        )
        .select_from(EjercicioObjetivoV2)
        .join(
            ObjetivoNormalizadoV2,
            ObjetivoNormalizadoV2.id == EjercicioObjetivoV2.objetivo_id,
        )
        .join(CategoriaObjetivo, CategoriaObjetivo.id == ObjetivoNormalizadoV2.categoria_id)
        .filter(
            EjercicioObjetivoV2.ejercicio_id == ejercicio_id,
            ObjetivoNormalizadoV2.version_id == version_id,
            ObjetivoNormalizadoV2.activo.is_(True),
        )
        .all()
    )
    rows.extend(
        {
            "objetivo_id": row.objetivo_id,
            "objetivo_nombre": row.objetivo_nombre,
            "categoria_id": row.categoria_id,
            "categoria_codigo": row.categoria_codigo,
            "categoria_nombre": row.categoria_nombre,
            "objetivo_origen_id": None,
            "objetivo_original": None,
            "rol_historico": "seleccion_directa",
            "alcance": "directo",
            "categoria_orden": row.categoria_orden,
            "objetivo_orden": row.objetivo_orden,
        }
        for row in direct_rows
    )
    rows.sort(
        key=lambda row: (
            row["categoria_orden"], row["objetivo_orden"],
            row["objetivo_origen_id"] or 0, row["rol_historico"], row["alcance"],
        )
    )
    for row in rows:
        row.pop("categoria_orden")
        row.pop("objetivo_orden")
    return rows
