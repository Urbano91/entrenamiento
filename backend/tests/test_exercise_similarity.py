from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.ejercicios import create_ejercicio, similares_ejercicios
from app.db.database import Base
from app.models.models import (
    CategoriaObjetivo,
    Ejercicio,
    EjercicioObjetivoV2,
    Espacio,
    ExerciseEmbedding,
    ExerciseRelation,
    ObjetivoNormalizadoV2,
    TaxonomiaObjetivoVersion,
    Tiempo,
    TipoTarea,
    Usuario,
)
from app.schemas.schemas import EjercicioCreate, EjercicioDraft
from app.services.embeddings import LocalFeatureHashingEmbeddingProvider
from app.services.exercise_similarity import (
    ExerciseSemanticDocument,
    build_structured_representation,
    ensure_exercise_embedding,
    find_similar_exercises,
    representation_hash,
)


class CountingProvider(LocalFeatureHashingEmbeddingProvider):
    def __init__(self):
        super().__init__(dimensions=64)
        self.calls = 0

    def embed(self, texts):
        self.calls += 1
        return super().embed(texts)


@pytest.fixture()
def similarity_db(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'similarity.sqlite'}",
        connect_args={"check_same_thread": False},
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine)
    db = TestingSession()
    version = TaxonomiaObjetivoVersion(
        id=1,
        codigo_version="TEST-V2",
        estado="BORRADOR",
        fecha_creacion="2026-08-12",
        motivo="tests",
        manifiesto_sha256="a" * 64,
        catalogo_sha256="b" * 64,
    )
    category = CategoriaObjetivo(
        id=1, version_id=1, codigo="TEC", nombre="Técnicos", orden=1
    )
    objectives = [
        ObjetivoNormalizadoV2(
            id=1, version_id=1, categoria_id=1, nombre="Pase", orden=1, activo=True
        ),
        ObjetivoNormalizadoV2(
            id=2, version_id=1, categoria_id=1, nombre="Control", orden=2, activo=True
        ),
    ]
    task_type = TipoTarea(id=1, nombre="Rueda de pase")
    space = Espacio(id=1, descripcion_original="10 x 10 metros")
    duration = Tiempo(id=1, descripcion_original="10 minutos")
    user = Usuario(id=1, usuario="coach", password_hash="unused", activo=True)
    db.add_all([version, category, *objectives, task_type, space, duration, user])
    db.flush()
    exercise_a = Ejercicio(
        numero=1,
        codigo="RP1",
        nombre="Rueda de pase con tercer hombre",
        tipo_tarea_id=1,
        jugadores=4,
        espacio_id=1,
        tiempo_id=1,
        desarrollo="Pase, apoyo y devolución a dos toques.",
    )
    exercise_b = Ejercicio(
        numero=2,
        codigo="RP2",
        nombre="Finalización después de pase",
        tipo_tarea_id=1,
        jugadores=4,
        espacio_id=1,
        tiempo_id=1,
        desarrollo="Pase previo y finalización a portería.",
    )
    db.add_all([exercise_a, exercise_b])
    db.flush()
    db.add_all([
        EjercicioObjetivoV2(ejercicio_id=exercise_a.id, objetivo_id=1),
        EjercicioObjetivoV2(ejercicio_id=exercise_a.id, objetivo_id=2),
        EjercicioObjetivoV2(ejercicio_id=exercise_b.id, objetivo_id=1),
    ])
    db.commit()
    yield db, TestingSession, engine
    db.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def make_draft(name="Rueda de pase con tercer hombre"):
    return EjercicioDraft(
        nombre=name,
        descripcion="Pase, apoyo y devolución a dos toques.",
        tipo_tarea_id=1,
        jugadores=4,
        espacio_id=1,
        tiempo_id=1,
        categoria_objetivo_id=1,
        objetivo_ids=[1, 2],
        materiales=["Balones", "4 conos"],
    )


def test_representacion_y_sha256_son_deterministas():
    first = ExerciseSemanticDocument(
        name=" Rueda  de pase ", objectives=("Pase", "Control"), players=4
    )
    second = ExerciseSemanticDocument(
        name="Rueda de pase", objectives=("Control", "Pase"), players=4
    )
    representation_a = build_structured_representation(first)
    representation_b = build_structured_representation(second)
    assert representation_a == representation_b
    assert representation_hash(representation_a) == representation_hash(representation_b)
    assert len(representation_hash(representation_a)) == 64


def test_embedding_nuevo_y_no_regenera_si_hash_no_cambia(similarity_db):
    db, _, _ = similarity_db
    provider = CountingProvider()
    exercise = db.get(Ejercicio, 1)
    stored, generated = ensure_exercise_embedding(db, exercise, provider)
    assert generated is True
    assert stored.source_hash
    assert provider.calls == 1
    same, generated_again = ensure_exercise_embedding(db, exercise, provider)
    assert same.id == stored.id
    assert generated_again is False
    assert provider.calls == 1
    assert db.query(ExerciseEmbedding).count() == 1


def test_busqueda_excluye_ordena_y_no_duplica(similarity_db):
    db, _, _ = similarity_db
    results = find_similar_exercises(
        db,
        make_draft(),
        CountingProvider(),
        top_k=5,
        exclude_exercise_id=2,
    )
    assert [row["exercise_id"] for row in results] == [1]
    assert results == sorted(results, key=lambda row: row["similarity"], reverse=True)
    assert len({row["exercise_id"] for row in results}) == len(results)
    assert results[0]["name"] == "Rueda de pase con tercer hombre"


def test_api_detecta_crea_permite_nuevo_y_registra_variante(similarity_db):
    db, _, _ = similarity_db
    similar = similares_ejercicios(
        make_draft(), exclude_exercise_id=None,
        current_user=SimpleNamespace(id=1), db=db
    )
    assert similar["candidates"][0]["exercise_id"] == 1

    created_payload = make_draft("Nueva rueda de pase").model_dump()
    created = create_ejercicio(
        EjercicioCreate(**created_payload),
        db,
        SimpleNamespace(id=1),
    )
    created_id = created["exercise"].id

    variant_payload = make_draft("Variante de rueda de pase").model_dump()
    variant_payload["variant_of_id"] = 1
    variant = create_ejercicio(
        EjercicioCreate(**variant_payload),
        db,
        SimpleNamespace(id=1),
    )
    assert variant["relation_type"] == "VARIANTE_DE"

    db.expire_all()
    assert db.get(Ejercicio, created_id) is not None
    relation = db.query(ExerciseRelation).one()
    assert relation.target_exercise_id == 1
    assert relation.source_exercise_id == variant["exercise"].id
    assert db.query(EjercicioObjetivoV2).filter(
        EjercicioObjetivoV2.ejercicio_id == created_id
    ).count() == 2


def test_guardado_no_se_bloquea_si_falla_indexacion(similarity_db, monkeypatch):
    db, _, _ = similarity_db

    def unavailable_provider():
        raise RuntimeError("proveedor temporalmente no disponible")

    monkeypatch.setattr(
        "app.api.ejercicios.get_embedding_provider", unavailable_provider
    )
    before = db.query(Ejercicio).count()
    result = create_ejercicio(
        EjercicioCreate(**make_draft("Ejercicio guardable sin proveedor").model_dump()),
        db,
        SimpleNamespace(id=1),
    )
    assert result["exercise"].id is not None
    assert db.query(Ejercicio).count() == before + 1
