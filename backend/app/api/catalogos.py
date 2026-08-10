from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import TipoTarea, Objetivo, Material, Espacio, Tiempo
from app.schemas.schemas import TipoTareaOut, ObjetivoOut, MaterialOut, EspacioOut, TiempoOut
from app.api.auth import get_current_user

router = APIRouter(prefix="/api", tags=["Catalogos"], dependencies=[Depends(get_current_user)])

@router.get("/tipos", response_model=List[TipoTareaOut])
def get_tipos(db: Session = Depends(get_db)):
    return db.query(TipoTarea).order_by(TipoTarea.nombre).all()

@router.get("/objetivos", response_model=List[ObjetivoOut])
def get_objetivos(db: Session = Depends(get_db)):
    return db.query(Objetivo).order_by(Objetivo.nombre_normalizado).all()

@router.get("/materiales", response_model=List[MaterialOut])
def get_materiales(db: Session = Depends(get_db)):
    return db.query(Material).order_by(Material.nombre_normalizado).all()

@router.get("/espacios", response_model=List[EspacioOut])
def get_espacios(db: Session = Depends(get_db)):
    return db.query(Espacio).order_by(Espacio.descripcion_original).all()

@router.get("/tiempos", response_model=List[TiempoOut])
def get_tiempos(db: Session = Depends(get_db)):
    return db.query(Tiempo).order_by(Tiempo.descripcion_original).all()
