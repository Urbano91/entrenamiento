from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from uuid import uuid4

from fastapi import (
    APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.models import (
    DocumentoPlanificacion, Entrenamiento, Partido, PlanificacionDiaria,
    Usuario,
)
from app.services.season_context import selected_season_id
from app.services.document_validation import MAX_DOCUMENT_BYTES, validate_document
from app.services.storage import StorageService, get_storage_service
from app.services.permissions import require_onboarded_trainer


router = APIRouter(prefix="/api/planificaciones", tags=["Planificación diaria"])
documents_router = APIRouter(prefix="/api/documentos", tags=["Documentos"])


class NotaIn(BaseModel):
    contenido: str = Field(max_length=100_000)


class DocumentoOut(BaseModel):
    id: int
    planificacion_id: int
    partido_id: Optional[int]
    nombre_original: str
    nombre_archivo: str
    tipo_mime: str
    tamano: int
    fecha_subida: datetime
    download_url: str


class PlanificacionContextoOut(BaseModel):
    id: Optional[int]
    fecha: date
    nota: Optional[str]
    documentos: list[DocumentoOut]


def _document_out(document: DocumentoPlanificacion) -> DocumentoOut:
    return DocumentoOut(
        id=document.id,
        planificacion_id=document.planificacion_id,
        partido_id=document.partido_id,
        nombre_original=document.nombre_original,
        nombre_archivo=document.nombre_archivo,
        tipo_mime=document.tipo_mime,
        tamano=document.tamano,
        fecha_subida=document.fecha_subida,
        download_url=f"/api/documentos/{document.id}/descargar",
    )


def _get_plan(
    db: Session, user_id: int, season_id: int, planning_date: date
) -> Optional[PlanificacionDiaria]:
    return db.query(PlanificacionDiaria).filter(
        PlanificacionDiaria.usuario_id == user_id,
        PlanificacionDiaria.temporada_id == season_id,
        PlanificacionDiaria.fecha == planning_date,
    ).first()


def _get_or_create_plan(
    db: Session, user_id: int, season_id: int, planning_date: date
) -> PlanificacionDiaria:
    existing = _get_plan(db, user_id, season_id, planning_date)
    if existing:
        return existing
    plan = PlanificacionDiaria(
        usuario_id=user_id,
        temporada_id=season_id,
        fecha=planning_date,
    )
    db.add(plan)
    db.flush()
    return plan


def _owned_document(
    db: Session, document_id: int, user_id: int
) -> DocumentoPlanificacion:
    document = db.query(DocumentoPlanificacion).filter(
        DocumentoPlanificacion.id == document_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    if document.usuario_id != user_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return document


@router.get("/agenda")
def get_agenda(
    desde: date = Query(default_factory=date.today),
    limite: int = Query(default=4, ge=1, le=30),
    temporada_id: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_onboarded_trainer(db, current_user)
    season_id = selected_season_id(db, current_user.id, temporada_id)
    training_dates = {
        row[0] for row in db.query(Entrenamiento.fecha).filter(
            Entrenamiento.usuario_id == current_user.id,
            Entrenamiento.temporada_id == season_id,
            Entrenamiento.fecha >= desde,
        ).distinct().all()
    }
    match_dates = {
        row[0] for row in db.query(Partido.fecha).filter(
            Partido.usuario_id == current_user.id,
            Partido.temporada_id == season_id,
            Partido.fecha >= desde,
        ).distinct().all()
    }
    planned_dates = sorted(training_dates | match_dates)[:limite]
    result = []
    for planning_date in planned_dates:
        trainings = db.query(Entrenamiento).filter(
            Entrenamiento.usuario_id == current_user.id,
            Entrenamiento.temporada_id == season_id,
            Entrenamiento.fecha == planning_date,
        ).all()
        matches = db.query(Partido).filter(
            Partido.usuario_id == current_user.id,
            Partido.temporada_id == season_id,
            Partido.fecha == planning_date,
        ).order_by(Partido.hora.asc(), Partido.id.asc()).all()
        result.append({
            "fecha": planning_date.isoformat(),
            "entrenamiento": {
                "cantidad": 1 if trainings else 0,
                "sesiones": len(trainings),
                "duracion_total": sum(item.duracion_minutos or 0 for item in trainings),
            },
            "partidos": [{
                "id": match.id,
                "hora": match.hora.isoformat(timespec="minutes") if match.hora else None,
                "rival": match.rival,
                "local_visitante": match.local_visitante,
            } for match in matches],
            "url_calendario": f"/calendario?fecha={planning_date.isoformat()}",
        })
    return result


@router.get("/{planning_date}", response_model=PlanificacionContextoOut)
def get_planning_context(
    planning_date: date,
    temporada_id: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    season_id = selected_season_id(db, current_user.id, temporada_id)
    plan = _get_plan(db, current_user.id, season_id, planning_date)
    if not plan:
        return PlanificacionContextoOut(
            id=None, fecha=planning_date, nota=None, documentos=[]
        )
    return PlanificacionContextoOut(
        id=plan.id,
        fecha=plan.fecha,
        nota=plan.nota,
        documentos=[_document_out(item) for item in plan.documentos],
    )


@router.put("/{planning_date}/nota", response_model=PlanificacionContextoOut)
def save_note(
    planning_date: date,
    data: NotaIn,
    temporada_id: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_onboarded_trainer(db, current_user)
    season_id = selected_season_id(db, current_user.id, temporada_id)
    plan = _get_or_create_plan(db, current_user.id, season_id, planning_date)
    plan.nota = data.contenido.strip() or None
    db.commit()
    db.refresh(plan)
    return PlanificacionContextoOut(
        id=plan.id, fecha=plan.fecha, nota=plan.nota,
        documentos=[_document_out(item) for item in plan.documentos],
    )


@router.delete("/{planning_date}/nota", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    planning_date: date,
    temporada_id: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_onboarded_trainer(db, current_user)
    season_id = selected_season_id(db, current_user.id, temporada_id)
    plan = _get_plan(db, current_user.id, season_id, planning_date)
    if plan:
        plan.nota = None
        db.commit()
    return None


@router.get("/{planning_date}/documentos", response_model=list[DocumentoOut])
def list_documents(
    planning_date: date,
    partido_id: Optional[int] = None,
    temporada_id: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    season_id = selected_season_id(db, current_user.id, temporada_id)
    plan = _get_plan(db, current_user.id, season_id, planning_date)
    if not plan:
        return []
    documents = plan.documentos
    if partido_id is not None:
        documents = [item for item in documents if item.partido_id == partido_id]
    return [_document_out(item) for item in documents]


@router.post(
    "/{planning_date}/documentos", response_model=DocumentoOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    planning_date: date,
    archivo: UploadFile = File(...),
    partido_id: Optional[int] = Form(default=None),
    temporada_id: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    require_onboarded_trainer(db, current_user)
    season_id = selected_season_id(db, current_user.id, temporada_id)
    content = await archivo.read(MAX_DOCUMENT_BYTES + 1)
    original_name, canonical_mime = validate_document(
        archivo.filename or "", archivo.content_type, content
    )
    if partido_id is not None:
        match = db.query(Partido).filter(Partido.id == partido_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Partido no encontrado")
        if match.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        if match.fecha != planning_date:
            raise HTTPException(
                status_code=422,
                detail="El partido no pertenece a la fecha de planificación",
            )
        if match.temporada_id != season_id:
            raise HTTPException(
                status_code=422,
                detail="El partido no pertenece a la temporada seleccionada",
            )
    plan = _get_or_create_plan(db, current_user.id, season_id, planning_date)
    extension = Path(original_name).suffix.lower()
    stored_name = f"{uuid4().hex}{extension}"
    storage_key = (
        f"{current_user.id}/{season_id}/{planning_date.isoformat()}/{stored_name}"
    )
    storage.save(storage_key, content)
    document = DocumentoPlanificacion(
        planificacion_id=plan.id,
        partido_id=partido_id,
        usuario_id=current_user.id,
        nombre_original=original_name,
        nombre_archivo=stored_name,
        tipo_mime=canonical_mime,
        tamano=len(content),
        storage_key=storage_key,
    )
    try:
        db.add(document)
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        storage.delete(storage_key)
        raise
    return _document_out(document)


@documents_router.get("/{document_id}/descargar")
def download_document(
    document_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    document = _owned_document(db, document_id, current_user.id)

    def stream():
        with storage.open(document.storage_key) as handle:
            while chunk := handle.read(64 * 1024):
                yield chunk

    encoded_name = quote(document.nombre_original)
    return StreamingResponse(
        stream(), media_type=document.tipo_mime,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}",
            "Content-Length": str(document.tamano),
        },
    )


@documents_router.delete(
    "/{document_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_document(
    document_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    require_onboarded_trainer(db, current_user)
    document = _owned_document(db, document_id, current_user.id)
    storage.delete(document.storage_key)
    db.delete(document)
    db.commit()
    return None
