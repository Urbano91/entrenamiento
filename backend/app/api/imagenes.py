import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.auth import get_current_user
from app.models.models import Imagen

router = APIRouter(prefix="/api/imagenes", tags=["Imagenes"], dependencies=[Depends(get_current_user)])

BASE_IMAGENES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../database/imagenes"))

@router.get("/{id}")
def get_imagen(id: int, db: Session = Depends(get_db)):
    imagen = db.query(Imagen).filter(Imagen.id == id).first()
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    
    # Prevenir path traversal asegurando que el archivo resida en BADE_IMAGENES_DIR
    target_path = os.path.abspath(os.path.join(BASE_IMAGENES_DIR, imagen.archivo))
    if not target_path.startswith(BASE_IMAGENES_DIR):
        raise HTTPException(status_code=400, detail="Acceso denegado")
        
    if not os.path.exists(target_path) or not os.path.isfile(target_path):
        raise HTTPException(status_code=404, detail="El archivo físico no existe")
        
    return FileResponse(target_path)
