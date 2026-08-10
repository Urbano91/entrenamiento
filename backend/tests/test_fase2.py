"""
Tests de Fase 2 — Usa base de datos en memoria (SQLite temporal).
No modifica la SQLite de producción.
Aislación: usa dependency_overrides[get_db] en lugar de cambiar DATABASE_URL.
"""
import os
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.models.models import (
    Usuario, PerfilEntrenador, Temporada,
    Entrenamiento, EntrenamientoEjercicio, Ejercicio,
    TipoTarea, Espacio, Tiempo,
)
from app.scripts.create_user import get_password_hash

TEST_DB_URL = "sqlite:///./test_fase2.db"

test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_fase2.db"):
        os.remove("./test_fase2.db")


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def apply_overrides():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="session")
def db():
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="session")
def seed_data(db):
    tipo = TipoTarea(nombre="Rondo")
    espacio = Espacio(descripcion_original="20x20")
    tiempo = Tiempo(descripcion_original="10 min")
    db.add_all([tipo, espacio, tiempo])
    db.flush()

    ejercicio = Ejercicio(
        numero=9001, codigo="TEST001", nombre="Ejercicio Test",
        tipo_tarea_id=tipo.id, jugadores=10,
        espacio_id=espacio.id, tiempo_id=tiempo.id,
    )
    db.add(ejercicio)

    user_a = Usuario(usuario="test_user_a", password_hash=get_password_hash("pass_a"), activo=True)
    user_b = Usuario(usuario="test_user_b", password_hash=get_password_hash("pass_b"), activo=True)
    db.add_all([user_a, user_b])

    temporada = Temporada(nombre="2026/27", fecha_inicio=date(2026, 7, 1), fecha_fin=date(2027, 6, 30))
    db.add(temporada)

    db.commit()
    db.refresh(ejercicio)
    db.refresh(user_a)
    db.refresh(user_b)
    db.refresh(temporada)
    return {"user_a": user_a, "user_b": user_b, "ejercicio": ejercicio, "temporada": temporada}


@pytest.fixture(scope="session")
def client_a(seed_data):
    c = TestClient(app)
    c.post("/api/auth/login", json={"usuario": "test_user_a", "password": "pass_a"})
    return c


@pytest.fixture(scope="session")
def client_b(seed_data):
    c = TestClient(app)
    c.post("/api/auth/login", json={"usuario": "test_user_b", "password": "pass_b"})
    return c


# ─── Tests Perfil ─────────────────────────────────────────────────────────────

def test_perfil_get_sin_perfil(client_a, seed_data):
    res = client_a.get("/api/perfil")
    assert res.status_code == 404


def test_perfil_crear(client_a, seed_data):
    res = client_a.put("/api/perfil", json={
        "nombre": "Carlos",
        "apellidos": "González",
        "club_actual": "CD Ejemplo",
        "temporada_actual_id": seed_data["temporada"].id,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["nombre"] == "Carlos"
    assert data["club_actual"] == "CD Ejemplo"


def test_perfil_get_con_perfil(client_a, seed_data):
    res = client_a.get("/api/perfil")
    assert res.status_code == 200
    data = res.json()
    assert data["nombre"] == "Carlos"
    assert data["temporada_actual"]["nombre"] == "2026/27"


def test_perfil_actualizar(client_a, seed_data):
    res = client_a.put("/api/perfil", json={
        "nombre": "Carlos",
        "apellidos": "González",
        "club_actual": "FC Nuevo",
    })
    assert res.status_code == 200
    assert res.json()["club_actual"] == "FC Nuevo"


# ─── Tests Temporadas ─────────────────────────────────────────────────────────

def test_temporadas_get(client_a, seed_data):
    res = client_a.get("/api/temporadas")
    assert res.status_code == 200
    assert any(t["nombre"] == "2026/27" for t in res.json())


def test_temporadas_crear(client_a, seed_data):
    res = client_a.post("/api/temporadas", json={"nombre": "2027/28"})
    assert res.status_code == 200
    assert res.json()["nombre"] == "2027/28"


# ─── Tests Entrenamientos ─────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def entrenamiento_a(client_a, seed_data):
    res = client_a.post("/api/entrenamientos", json={
        "fecha": "2026-08-12",
        "nombre": "Presión tras pérdida",
        "duracion_minutos": 90,
        "objetivo_principal": "Presión",
    })
    assert res.status_code == 201
    return res.json()


def test_entrenamientos_crear(entrenamiento_a):
    assert entrenamiento_a["nombre"] == "Presión tras pérdida"
    assert entrenamiento_a["fecha"] == "2026-08-12"


def test_entrenamientos_listar(client_a, entrenamiento_a):
    res = client_a.get("/api/entrenamientos")
    assert res.status_code == 200
    ids = [e["id"] for e in res.json()]
    assert entrenamiento_a["id"] in ids


def test_entrenamientos_detalle(client_a, entrenamiento_a):
    res = client_a.get(f"/api/entrenamientos/{entrenamiento_a['id']}")
    assert res.status_code == 200
    assert res.json()["nombre"] == "Presión tras pérdida"


def test_entrenamientos_editar(client_a, entrenamiento_a):
    res = client_a.put(f"/api/entrenamientos/{entrenamiento_a['id']}", json={"nombre": "Presión editada"})
    assert res.status_code == 200
    assert res.json()["nombre"] == "Presión editada"


# ─── Tests Ejercicios del entrenamiento ──────────────────────────────────────

@pytest.fixture(scope="session")
def relacion_ejercicio(client_a, entrenamiento_a, seed_data):
    res = client_a.post(f"/api/entrenamientos/{entrenamiento_a['id']}/ejercicios", json={
        "ejercicio_id": seed_data["ejercicio"].id,
        "orden": 0,
    })
    assert res.status_code == 201
    return res.json()


def test_ejercicio_añadido(relacion_ejercicio, seed_data):
    assert relacion_ejercicio["ejercicio_id"] == seed_data["ejercicio"].id
    assert relacion_ejercicio["orden"] == 0


def test_ejercicios_reordenar(client_a, entrenamiento_a, relacion_ejercicio):
    res = client_a.put(
        f"/api/entrenamientos/{entrenamiento_a['id']}/ejercicios/reordenar",
        json=[{"id": relacion_ejercicio["id"], "orden": 5}]
    )
    assert res.status_code == 200


def test_ejercicio_eliminar(client_a, entrenamiento_a, relacion_ejercicio):
    res = client_a.delete(
        f"/api/entrenamientos/{entrenamiento_a['id']}/ejercicios/{relacion_ejercicio['id']}"
    )
    assert res.status_code == 204


# ─── Tests Reutilizar ─────────────────────────────────────────────────────────

def test_reutilizar(client_a, entrenamiento_a):
    # Restaurar nombre
    client_a.put(f"/api/entrenamientos/{entrenamiento_a['id']}", json={"nombre": "Presión tras pérdida"})
    res = client_a.post(f"/api/entrenamientos/{entrenamiento_a['id']}/reutilizar", json={
        "fecha": "2026-08-26",
        "nombre": "Presión tras pérdida (copia)",
    })
    assert res.status_code == 201
    copia = res.json()
    assert copia["id"] != entrenamiento_a["id"]
    assert copia["nombre"] == "Presión tras pérdida (copia)"
    assert copia["fecha"] == "2026-08-26"


def test_reutilizar_original_intacto(client_a, entrenamiento_a):
    res = client_a.get(f"/api/entrenamientos/{entrenamiento_a['id']}")
    assert res.status_code == 200
    data = res.json()
    assert data["nombre"] == "Presión tras pérdida"
    assert data["fecha"] == "2026-08-12"


# ─── Tests Ownership ─────────────────────────────────────────────────────────

def test_ownership_consultar(client_b, entrenamiento_a):
    res = client_b.get(f"/api/entrenamientos/{entrenamiento_a['id']}")
    assert res.status_code == 403


def test_ownership_editar(client_b, entrenamiento_a):
    res = client_b.put(f"/api/entrenamientos/{entrenamiento_a['id']}", json={"nombre": "Hack"})
    assert res.status_code == 403


def test_ownership_eliminar(client_b, entrenamiento_a):
    res = client_b.delete(f"/api/entrenamientos/{entrenamiento_a['id']}")
    assert res.status_code == 403


def test_ownership_reutilizar(client_b, entrenamiento_a):
    res = client_b.post(
        f"/api/entrenamientos/{entrenamiento_a['id']}/reutilizar",
        json={"fecha": "2026-09-01"}
    )
    assert res.status_code == 403


# ─── Tests Calendario ─────────────────────────────────────────────────────────

def test_calendario_entrenamiento_aparece(client_a, entrenamiento_a):
    res = client_a.get("/api/calendario", params={"year": 2026, "month": 8})
    assert res.status_code == 200
    data = res.json()
    assert "2026-08-12" in data["dias"]


def test_calendario_usuario_correcto(client_b, entrenamiento_a):
    res = client_b.get("/api/calendario", params={
        "year": 2026,
        "month": 8,
        "temporada_id": entrenamiento_a["temporada_id"],
    })
    assert res.status_code == 200
    data = res.json()
    dias = data["dias"]
    if "2026-08-12" in dias:
        ids = [e["id"] for e in dias["2026-08-12"]]
        assert entrenamiento_a["id"] not in ids


# ─── Test eliminar entrenamiento ──────────────────────────────────────────────

def test_entrenamientos_eliminar(client_a, entrenamiento_a):
    res = client_a.delete(f"/api/entrenamientos/{entrenamiento_a['id']}")
    assert res.status_code == 204
    res2 = client_a.get(f"/api/entrenamientos/{entrenamiento_a['id']}")
    assert res2.status_code == 404
