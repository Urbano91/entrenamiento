from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey,
    ForeignKeyConstraint, Index, Integer, String, Text, Time,
    UniqueConstraint, text, true,
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

    account = relationship(
        "UserAccount", back_populates="usuario", uselist=False,
        cascade="all, delete-orphan",
    )

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

    embeddings = relationship(
        "ExerciseEmbedding", back_populates="ejercicio", cascade="all, delete-orphan"
    )
    objetivos_v2_directos = relationship(
        "EjercicioObjetivoV2", back_populates="ejercicio", cascade="all, delete-orphan"
    )
    ownership = relationship(
        "ExerciseOwnership", back_populates="ejercicio", uselist=False,
        cascade="all, delete-orphan",
    )


class ExerciseEmbedding(Base):
    """Representación vectorial aditiva; no altera la tabla histórica."""

    __tablename__ = "exercise_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "ejercicio_id", "provider", "model", name="uq_exercise_embedding_model"
        ),
        Index("ix_exercise_embeddings_lookup", "provider", "model"),
        Index("ix_exercise_embeddings_source_hash", "source_hash"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ejercicio_id = Column(
        Integer, ForeignKey("ejercicios.id", ondelete="CASCADE"), nullable=False
    )
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    embedding = Column(Text, nullable=False)
    source_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )

    ejercicio = relationship("Ejercicio", back_populates="embeddings")


class ExerciseRelation(Base):
    __tablename__ = "exercise_relations"
    __table_args__ = (
        CheckConstraint(
            "relation_type IN ('VARIANTE_DE')", name="ck_exercise_relation_type"
        ),
        CheckConstraint(
            "source_exercise_id != target_exercise_id",
            name="ck_exercise_relation_distinct",
        ),
        UniqueConstraint(
            "source_exercise_id", "target_exercise_id", "relation_type",
            name="uq_exercise_relation",
        ),
        Index("ix_exercise_relations_target", "target_exercise_id", "relation_type"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_exercise_id = Column(
        Integer, ForeignKey("ejercicios.id", ondelete="CASCADE"), nullable=False,
        index=True,
    )
    target_exercise_id = Column(
        Integer, ForeignKey("ejercicios.id", ondelete="CASCADE"), nullable=False
    )
    relation_type = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EjercicioObjetivoV2(Base):
    """Objetivos V2 elegidos directamente para ejercicios de nueva creación."""

    __tablename__ = "ejercicio_objetivo_v2"
    __table_args__ = (
        UniqueConstraint(
            "ejercicio_id", "objetivo_id", name="uq_ejercicio_objetivo_v2"
        ),
        Index("ix_ejercicio_objetivo_v2_objetivo", "objetivo_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ejercicio_id = Column(
        Integer, ForeignKey("ejercicios.id", ondelete="CASCADE"), nullable=False
    )
    objetivo_id = Column(
        Integer, ForeignKey("objetivos_normalizados_v2.id"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ejercicio = relationship("Ejercicio", back_populates="objetivos_v2_directos")
    objetivo = relationship("ObjetivoNormalizadoV2")


# ==========================================
# IDENTIDAD, CLUBES Y EJERCICIOS PRIVADOS — capa aditiva
# ==========================================

class UserAccount(Base):
    __tablename__ = "user_accounts"
    __table_args__ = (
        CheckConstraint(
            "account_type IN ('ADMIN', 'ENTRENADOR', 'CLUB')",
            name="ck_user_account_type",
        ),
    )

    user_id = Column(
        Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    account_type = Column(String, nullable=False, default="ENTRENADOR")
    must_change_password = Column(Boolean, nullable=False, default=True)
    onboarding_complete = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )

    usuario = relationship("Usuario", back_populates="account")


class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_user_id = Column(
        Integer, ForeignKey("usuarios.id"), unique=True, nullable=False, index=True
    )
    nombre = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )

    owner = relationship("Usuario")
    assignments = relationship("CoachAssignment", back_populates="club")


class SportsCategory(Base):
    __tablename__ = "sports_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CoachAssignment(Base):
    __tablename__ = "coach_assignments"
    __table_args__ = (
        UniqueConstraint(
            "coach_user_id", "club_id", "temporada_id", "category_id",
            name="uq_coach_assignment_context",
        ),
        Index("ix_coach_assignments_club_season", "club_id", "temporada_id"),
        Index("ix_coach_assignments_coach", "coach_user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    coach_user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    club_id = Column(
        Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=True
    )
    temporada_id = Column(Integer, ForeignKey("temporadas.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("sports_categories.id"), nullable=False)

    puesto = Column(String, nullable=False, default="Entrenador")

    parent_coach_assignment_id = Column(
        Integer,
        ForeignKey("coach_assignments.id", ondelete="SET NULL"),
        nullable=True,
    )

    active = Column(Boolean, nullable=False, default=True)

    visible_in_club = Column(
        Boolean, nullable=False, default=True, server_default=true()
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    coach = relationship("Usuario")
    club = relationship("Club", back_populates="assignments")
    temporada = relationship("Temporada")
    category = relationship("SportsCategory")

    parent_coach_assignment = relationship(
        "CoachAssignment",
        remote_side=[id],
        foreign_keys=[parent_coach_assignment_id],
    )


class ExerciseOwnership(Base):
    """La ausencia de fila identifica un ejercicio oficial e inmutable."""

    __tablename__ = "exercise_ownership"
    __table_args__ = (
        Index("ix_exercise_ownership_creator_deleted", "created_by_user_id", "deleted_at"),
    )

    ejercicio_id = Column(
        Integer, ForeignKey("ejercicios.id", ondelete="CASCADE"), primary_key=True
    )
    created_by_user_id = Column(
        Integer, ForeignKey("usuarios.id"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    ejercicio = relationship("Ejercicio", back_populates="ownership")
    creator = relationship("Usuario")


class ExerciseFavorite(Base):
    """Ejercicios guardados por un entrenador. Tabla aditiva."""

    __tablename__ = "exercise_favorites"
    __table_args__ = (
        UniqueConstraint(
            "ejercicio_id", "usuario_id", name="uq_exercise_favorite"
        ),
        Index("ix_exercise_favorites_user", "usuario_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ejercicio_id = Column(
        Integer, ForeignKey("ejercicios.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id = Column(
        Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ejercicio = relationship("Ejercicio")
    usuario = relationship("Usuario")


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
# TAXONOMÍA DE OBJETIVOS V2 — capa aditiva
# ==========================================

class TaxonomiaObjetivoVersion(Base):
    __tablename__ = "taxonomia_objetivo_versiones"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('BORRADOR', 'APROBADA', 'ACTIVA', 'RETIRADA')",
            name="ck_taxonomia_objetivo_version_estado",
        ),
        CheckConstraint(
            "estado != 'ACTIVA' OR fecha_activacion IS NOT NULL",
            name="ck_taxonomia_objetivo_version_activacion",
        ),
        Index(
            "uq_taxonomia_objetivo_version_activa",
            "estado",
            unique=True,
            sqlite_where=text("estado = 'ACTIVA'"),
            postgresql_where=text("estado = 'ACTIVA'"),
        ),
    )

    id = Column(Integer, primary_key=True)
    codigo_version = Column(String, unique=True, nullable=False)
    estado = Column(String, nullable=False)
    fecha_creacion = Column(String, nullable=False)
    fecha_activacion = Column(String)
    motivo = Column(Text, nullable=False)
    manifiesto_sha256 = Column(String, nullable=False)
    catalogo_sha256 = Column(String, nullable=False)
    created_at = Column(String, nullable=False, server_default=func.current_timestamp())


class CategoriaObjetivo(Base):
    __tablename__ = "categorias_objetivo"
    __table_args__ = (
        UniqueConstraint("version_id", "codigo"),
        UniqueConstraint("version_id", "nombre"),
        UniqueConstraint("version_id", "orden"),
        CheckConstraint("orden > 0", name="ck_categoria_objetivo_orden"),
    )

    id = Column(Integer, primary_key=True)
    version_id = Column(
        Integer,
        ForeignKey("taxonomia_objetivo_versiones.id", ondelete="CASCADE"),
        nullable=False,
    )
    codigo = Column(String, nullable=False)
    nombre = Column(String, nullable=False)
    orden = Column(Integer, nullable=False)


class ObjetivoNormalizadoV2(Base):
    __tablename__ = "objetivos_normalizados_v2"
    __table_args__ = (
        UniqueConstraint("version_id", "nombre"),
        UniqueConstraint("version_id", "categoria_id", "orden"),
        CheckConstraint("orden > 0", name="ck_objetivo_normalizado_v2_orden"),
    )

    id = Column(Integer, primary_key=True)
    version_id = Column(
        Integer,
        ForeignKey("taxonomia_objetivo_versiones.id", ondelete="CASCADE"),
        nullable=False,
    )
    categoria_id = Column(Integer, ForeignKey("categorias_objetivo.id"), nullable=False)
    nombre = Column(String, nullable=False)
    orden = Column(Integer, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)


class MapeoObjetivo(Base):
    __tablename__ = "mapeos_objetivo"
    __table_args__ = (
        UniqueConstraint("version_id", "objetivo_origen_id"),
        UniqueConstraint("id", "version_id", "objetivo_origen_id"),
        CheckConstraint(
            "accion IN ('MANTENER', 'UNIFICAR', 'DIVIDIR', 'REUBICAR')",
            name="ck_mapeo_objetivo_accion",
        ),
        CheckConstraint(
            "confianza IN ('ALTA', 'MEDIA', 'BAJA')",
            name="ck_mapeo_objetivo_confianza",
        ),
        CheckConstraint(
            "estado_decision IN ('APROBADO', 'CONTEXTO', 'FORMATO', 'EXCEPCION')",
            name="ck_mapeo_objetivo_estado_decision",
        ),
    )

    id = Column(Integer, primary_key=True)
    version_id = Column(
        Integer,
        ForeignKey("taxonomia_objetivo_versiones.id", ondelete="CASCADE"),
        nullable=False,
    )
    objetivo_origen_id = Column(Integer, ForeignKey("objetivos.id"), nullable=False)
    objetivo_origen_snapshot = Column(String, nullable=False)
    frecuencia_ejercicios = Column(Integer, nullable=False)
    frecuencia_relaciones = Column(Integer, nullable=False)
    accion = Column(String, nullable=False)
    confianza = Column(String, nullable=False)
    estado_decision = Column(String, nullable=False)
    decision_entrenador = Column(String, nullable=False)
    motivo = Column(Text, nullable=False)


class MapeoObjetivoDestino(Base):
    __tablename__ = "mapeo_objetivo_destinos"
    __table_args__ = (
        UniqueConstraint("mapeo_id", "objetivo_normalizado_id"),
        UniqueConstraint("mapeo_id", "orden"),
        CheckConstraint("orden > 0", name="ck_mapeo_objetivo_destino_orden"),
    )

    id = Column(Integer, primary_key=True)
    mapeo_id = Column(
        Integer, ForeignKey("mapeos_objetivo.id", ondelete="CASCADE"), nullable=False
    )
    objetivo_normalizado_id = Column(
        Integer, ForeignKey("objetivos_normalizados_v2.id"), nullable=False
    )
    orden = Column(Integer, nullable=False)


class TerminoClasificacion(Base):
    __tablename__ = "terminos_clasificacion"
    __table_args__ = (
        UniqueConstraint("version_id", "tipo", "nombre"),
        CheckConstraint(
            "tipo IN ('FASE', 'PRIORIDAD', 'CONTEXTO', 'FORMATO')",
            name="ck_termino_clasificacion_tipo",
        ),
    )

    id = Column(Integer, primary_key=True)
    version_id = Column(
        Integer,
        ForeignKey("taxonomia_objetivo_versiones.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo = Column(String, nullable=False)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text)


class MapeoObjetivoTermino(Base):
    __tablename__ = "mapeo_objetivo_terminos"
    __table_args__ = (
        UniqueConstraint("mapeo_id", "termino_id"),
        UniqueConstraint("mapeo_id", "orden"),
        CheckConstraint("orden > 0", name="ck_mapeo_objetivo_termino_orden"),
    )

    id = Column(Integer, primary_key=True)
    mapeo_id = Column(
        Integer, ForeignKey("mapeos_objetivo.id", ondelete="CASCADE"), nullable=False
    )
    termino_id = Column(
        Integer, ForeignKey("terminos_clasificacion.id"), nullable=False
    )
    orden = Column(Integer, nullable=False)


class MapeoObjetivoExcepcion(Base):
    __tablename__ = "mapeos_objetivo_excepciones"
    __table_args__ = (
        UniqueConstraint(
            "version_id", "ejercicio_id", "objetivo_origen_id", "tipo_objetivo"
        ),
        ForeignKeyConstraint(
            ["mapeo_id", "version_id", "objetivo_origen_id"],
            [
                "mapeos_objetivo.id",
                "mapeos_objetivo.version_id",
                "mapeos_objetivo.objetivo_origen_id",
            ],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["ejercicio_id", "objetivo_origen_id", "tipo_objetivo"],
            [
                "ejercicio_objetivo.ejercicio_id",
                "ejercicio_objetivo.objetivo_id",
                "ejercicio_objetivo.tipo_objetivo",
            ],
        ),
    )

    id = Column(Integer, primary_key=True)
    version_id = Column(
        Integer,
        ForeignKey("taxonomia_objetivo_versiones.id", ondelete="CASCADE"),
        nullable=False,
    )
    mapeo_id = Column(Integer, nullable=False)
    ejercicio_id = Column(Integer, nullable=False)
    objetivo_origen_id = Column(Integer, nullable=False)
    tipo_objetivo = Column(String, nullable=False)
    objetivo_original_snapshot = Column(String, nullable=False)
    contexto = Column(Text)
    formato = Column(Text)
    motivo = Column(Text, nullable=False)


class MapeoExcepcionDestino(Base):
    __tablename__ = "mapeo_excepcion_destinos"
    __table_args__ = (
        UniqueConstraint("excepcion_id", "objetivo_normalizado_id"),
        UniqueConstraint("excepcion_id", "orden"),
        CheckConstraint("orden > 0", name="ck_mapeo_excepcion_destino_orden"),
    )

    id = Column(Integer, primary_key=True)
    excepcion_id = Column(
        Integer,
        ForeignKey("mapeos_objetivo_excepciones.id", ondelete="CASCADE"),
        nullable=False,
    )
    objetivo_normalizado_id = Column(
        Integer, ForeignKey("objetivos_normalizados_v2.id"), nullable=False
    )
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
