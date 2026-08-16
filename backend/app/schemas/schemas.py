from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Optional, List
from datetime import date, datetime

class UsuarioBase(BaseModel):
    usuario: str

class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioRegister(UsuarioBase):
    password: str = Field(min_length=8)


class ClubRegister(UsuarioRegister):
    nombre_club: str = Field(min_length=1, max_length=180)


class UsuarioLogin(BaseModel):
    usuario: str
    password: str

class UsuarioOut(UsuarioBase):
    id: int
    activo: bool
    account_type: Literal["ADMIN", "ENTRENADOR", "CLUB"]
    must_change_password: bool
    onboarding_complete: bool
    model_config = ConfigDict(from_attributes=True)


class OnboardingComplete(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=180)
    password: str = Field(min_length=8)


class ProvisionalPasswordChange(BaseModel):
    password: str = Field(min_length=8)

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


class CategoriaObjetivoV2Out(BaseModel):
    id: int
    codigo: str
    nombre: str
    orden: int
    model_config = ConfigDict(from_attributes=True)


class ObjetivoNormalizadoV2Out(BaseModel):
    id: int
    nombre: str
    categoria_id: int
    categoria_codigo: str
    categoria_nombre: str
    orden: int


class ObjetivoV2TrazabilidadOut(BaseModel):
    objetivo_id: int
    objetivo_nombre: str
    categoria_id: int
    categoria_codigo: str
    categoria_nombre: str
    objetivo_origen_id: Optional[int]
    objetivo_original: Optional[str]
    rol_historico: str
    alcance: str

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
    is_official: bool = True
    can_edit: bool = False
    is_favorite: bool = False
    created_by_user_id: Optional[int] = None
    creator_display: Optional[str] = None
    assignment_context: Optional[str] = None
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
    official_total: int = 0
    my_total: int = 0
    favorite_total: int = 0


class EjercicioDraft(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    descripcion: Optional[str] = None
    tipo_tarea_id: int
    jugadores: int = Field(ge=1)
    espacio_id: int
    tiempo_id: int
    categoria_objetivo_id: int
    objetivo_ids: List[int] = Field(min_length=1)
    materiales: List[str] = Field(default_factory=list)


class SimilarExerciseCandidate(BaseModel):
    exercise_id: Optional[int] = None
    name: Optional[str] = None
    similarity: Optional[float] = None
    objectives: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    material: List[str] = Field(default_factory=list)
    players: Optional[int] = None
    space: Optional[str] = None
    duration: Optional[str] = None
    details_visible: bool = True
    private_match: bool = False


class SimilarExercisesOut(BaseModel):
    candidates: List[SimilarExerciseCandidate]


class EjercicioCreate(EjercicioDraft):
    variant_of_id: Optional[int] = None


class EjercicioUpdate(EjercicioDraft):
    pass


class EjercicioCreateOut(BaseModel):
    exercise: EjercicioDetailOut
    relation_type: Optional[str] = None
    related_exercise_id: Optional[int] = None
