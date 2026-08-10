from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer,
    String, Text, Time, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TipoTarea(Base):
    __tablename__ = "tipos_tarea"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)
    ejercicios = relationship("Ejercicio", back_populates="tipo")

class Espacio(Base):
    __tablename__ = "espacios"
    id = Column(Integer, primary_key=True, autoincrement=True)
    descripcion_original = Column(String, unique=True, nullable=False)
    ejercicios = relationship("Ejercicio", back_populates="espacio")

class Tiempo(Base):
    __tablename__ = "tiempos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    descripcion_original = Column(String, unique=True, nullable=False)
    ejercicios = relationship("Ejercicio", back_populates="tiempo")

class Ejercicio(Base):
    __tablename__ = "ejercicios"
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(Integer, unique=True, nullable=False)
    codigo = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    nombre_original = Column(String)
    tipo_tarea_id = Column(Integer, ForeignKey("tipos_tarea.id"), nullable=False)
    jugadores = Column(Integer, nullable=False)
    espacio_id = Column(Integer, ForeignKey("espacios.id"), nullable=False)
    tiempo_id = Column(Integer, ForeignKey("tiempos.id"), nullable=False)
    desarrollo = Column(String)
    objetivo_1_original = Column(String)
    objetivo_1_normalizado = Column(String)
    objetivo_2_original = Column(String)
    objetivo_2_normalizado = Column(String)

    tipo = relationship("TipoTarea", back_populates="ejercicios")
    espacio = relationship("Espacio", back_populates="ejercicios")
    tiempo = relationship("Tiempo", back_populates="ejercicios")

    objetivos_asociados = relationship("EjercicioObjetivo", back_populates="ejercicio")
    materiales_asociados = relationship("EjercicioMaterial", back_populates="ejercicio")
    imagenes_asociadas = relationship("EjercicioImagen", back_populates="ejercicio", order_by="EjercicioImagen.orden")

class Objetivo(Base):
    __tablename__ = "objetivos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_normalizado = Column(String, unique=True, nullable=False)
    ejercicios_asociados = relationship("EjercicioObjetivo", back_populates="objetivo")

class EjercicioObjetivo(Base):
    __tablename__ = "ejercicio_objetivo"
    ejercicio_id = Column(Integer, ForeignKey("ejercicios.id", ondelete="CASCADE"), primary_key=True)
    objetivo_id = Column(Integer, ForeignKey("objetivos.id"), primary_key=True)
    tipo_objetivo = Column(String, primary_key=True)
    objetivo_original = Column(String)

    ejercicio = relationship("Ejercicio", back_populates="objetivos_asociados")
    objetivo = relationship("Objetivo", back_populates="ejercicios_asociados")

class Material(Base):
    __tablename__ = "materiales"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_normalizado = Column(String, unique=True, nullable=False)
    ejercicios_asociados = relationship("EjercicioMaterial", back_populates="material")

class EjercicioMaterial(Base):
    __tablename__ = "ejercicio_material"
    ejercicio_id = Column(Integer, ForeignKey("ejercicios.id", ondelete="CASCADE"), primary_key=True)
    material_id = Column(Integer, ForeignKey("materiales.id"), primary_key=True)
    material_original = Column(String)

    ejercicio = relationship("Ejercicio", back_populates="materiales_asociados")
    material = relationship("Material", back_populates="ejercicios_asociados")

class Imagen(Base):
    __tablename__ = "imagenes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    archivo = Column(String, unique=True, nullable=False)
    sha256 = Column(String, unique=True, nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    
    ejercicios_asociados = relationship("EjercicioImagen", back_populates="imagen")

class EjercicioImagen(Base):
    __tablename__ = "ejercicio_imagen"
    ejercicio_id = Column(Integer, ForeignKey("ejercicios.id", ondelete="CASCADE"), primary_key=True)
    imagen_id = Column(Integer, ForeignKey("imagenes.id"), primary_key=True)
    orden = Column(Integer, primary_key=True)

    ejercicio = relationship("Ejercicio", back_populates="imagenes_asociadas")
    imagen = relationship("Imagen", back_populates="ejercicios_asociados")

class TextoOriginal(Base):
    __tablename__ = "texto_original"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ejercicio_id = Column(Integer, ForeignKey("ejercicios.id", ondelete="CASCADE"), nullable=False)
    categoria = Column(String, nullable=False)
    texto = Column(String, nullable=False)
    fila_origen = Column(Integer)
    columna_origen = Column(Integer)
    orden = Column(Integer, nullable=False)


# ==========================================
# FASE 2 — Tablas nuevas (no tocar Fase 1)
# ==========================================

class Temporada(Base):
    __tablename__ = "temporadas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)  # ej: "2026/27"
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)

    entrenamientos = relationship("Entrenamiento", back_populates="temporada")
    partidos = relationship("Partido", back_populates="temporada")
    perfiles = relationship("PerfilEntrenador", back_populates="temporada_actual")


class PerfilEntrenador(Base):
    __tablename__ = "perfiles_entrenador"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    apellidos = Column(String, nullable=False)
    club_actual = Column(String)
    temporada_actual_id = Column(Integer, ForeignKey("temporadas.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    usuario = relationship("Usuario")
    temporada_actual = relationship("Temporada", back_populates="perfiles")


class Entrenamiento(Base):
    __tablename__ = "entrenamientos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    temporada_id = Column(Integer, ForeignKey("temporadas.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=True)
    nombre = Column(String, nullable=False)
    duracion_minutos = Column(Integer)
    objetivo_principal = Column(Text)
    observaciones = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    usuario = relationship("Usuario")
    temporada = relationship("Temporada", back_populates="entrenamientos")
    ejercicios_rel = relationship(
        "EntrenamientoEjercicio",
        back_populates="entrenamiento",
        order_by="EntrenamientoEjercicio.orden",
        cascade="all, delete-orphan"
    )


class EntrenamientoEjercicio(Base):
    __tablename__ = "entrenamiento_ejercicios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entrenamiento_id = Column(Integer, ForeignKey("entrenamientos.id", ondelete="CASCADE"), nullable=False)
    ejercicio_id = Column(Integer, ForeignKey("ejercicios.id"), nullable=False)
    orden = Column(Integer, nullable=False, default=0)

    entrenamiento = relationship("Entrenamiento", back_populates="ejercicios_rel")
    ejercicio = relationship("Ejercicio")


# ==========================================
# FASE 3 — Partidos y planificación diaria
# ==========================================

class Partido(Base):
    __tablename__ = "partidos"
    __table_args__ = (
        CheckConstraint(
            "local_visitante IN ('local', 'visitante')",
            name="ck_partidos_local_visitante",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    temporada_id = Column(Integer, ForeignKey("temporadas.id"), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    hora = Column(Time, nullable=True)
    rival = Column(String, nullable=False)
    local_visitante = Column(String, nullable=False, default="local")
    campo = Column(String)
    observaciones = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )

    usuario = relationship("Usuario")
    temporada = relationship("Temporada", back_populates="partidos")
    documentos = relationship("DocumentoPlanificacion", back_populates="partido")


# ==========================================
# FASE 3.1 — Contexto diario y documentos
# ==========================================

class PlanificacionDiaria(Base):
    __tablename__ = "planificaciones_diarias"
    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "temporada_id", "fecha",
            name="uq_planificacion_usuario_temporada_fecha",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    temporada_id = Column(Integer, ForeignKey("temporadas.id"), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    nota = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )

    usuario = relationship("Usuario")
    temporada = relationship("Temporada")
    documentos = relationship(
        "DocumentoPlanificacion", back_populates="planificacion",
        cascade="all, delete-orphan",
    )


class DocumentoPlanificacion(Base):
    __tablename__ = "documentos_planificacion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    planificacion_id = Column(
        Integer, ForeignKey("planificaciones_diarias.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    partido_id = Column(
        Integer, ForeignKey("partidos.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    nombre_original = Column(String, nullable=False)
    nombre_archivo = Column(String, nullable=False)
    tipo_mime = Column(String, nullable=False)
    tamano = Column(Integer, nullable=False)
    storage_key = Column(String, unique=True, nullable=False)
    fecha_subida = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    planificacion = relationship("PlanificacionDiaria", back_populates="documentos")
    partido = relationship("Partido", back_populates="documentos")
    usuario = relationship("Usuario")
