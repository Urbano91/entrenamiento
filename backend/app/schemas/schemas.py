from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime

class UsuarioBase(BaseModel):
    usuario: str

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioLogin(BaseModel):
    usuario: str
    password: str

class UsuarioOut(UsuarioBase):
    id: int
    activo: bool
    model_config = ConfigDict(from_attributes=True)

class TipoTareaOut(BaseModel):
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)

class EspacioOut(BaseModel):
    id: int
    descripcion_original: str
    model_config = ConfigDict(from_attributes=True)

class TiempoOut(BaseModel):
    id: int
    descripcion_original: str
    model_config = ConfigDict(from_attributes=True)

class ObjetivoOut(BaseModel):
    id: int
    nombre_normalizado: str
    model_config = ConfigDict(from_attributes=True)

class EjercicioObjetivoOut(BaseModel):
    tipo_objetivo: str
    objetivo_original: Optional[str]
    objetivo: ObjetivoOut
    model_config = ConfigDict(from_attributes=True)

class MaterialOut(BaseModel):
    id: int
    nombre_normalizado: str
    model_config = ConfigDict(from_attributes=True)
    
class EjercicioMaterialOut(BaseModel):
    material_original: Optional[str]
    material: MaterialOut
    model_config = ConfigDict(from_attributes=True)

class ImagenOut(BaseModel):
    id: int
    archivo: str
    width: Optional[int]
    height: Optional[int]
    model_config = ConfigDict(from_attributes=True)

class EjercicioImagenOut(BaseModel):
    orden: int
    imagen: ImagenOut
    model_config = ConfigDict(from_attributes=True)

class EjercicioListOut(BaseModel):
    id: int
    numero: int
    codigo: str
    nombre: str
    tipo_tarea_id: int
    tipo: TipoTareaOut
    jugadores: int
    espacio: EspacioOut
    tiempo: TiempoOut
    objetivo_1_normalizado: Optional[str] = None
    tiene_portada: bool = False
    tiene_animacion: bool = False
    model_config = ConfigDict(from_attributes=True)

class EjercicioDetailOut(EjercicioListOut):
    desarrollo: Optional[str]
    objetivo_1_original: Optional[str]
    objetivo_2_original: Optional[str]
    objetivo_2_normalizado: Optional[str]
    
    objetivos_asociados: List[EjercicioObjetivoOut] = []
    materiales_asociados: List[EjercicioMaterialOut] = []
    imagenes_asociadas: List[EjercicioImagenOut] = []

class PaginatedEjercicios(BaseModel):
    items: List[EjercicioListOut]
    page: int
    page_size: int
    total: int
    total_pages: int
