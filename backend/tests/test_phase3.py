"""Tests de Fase 3 sobre SQLite temporal; nunca usan la base de producción."""

import os
from datetime import date, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.api.auth import get_current_user
from app.db.database import Base, get_db
from app.main import app
from app.models.models import (
    Entrenamiento, Espacio, PerfilEntrenador, Temporada, Tiempo, TipoTarea,
    Usuario,
)
from app.scripts.create_user import get_password_hash


TEST_DB_URL = "sqlite:///./test_phase3.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@event.listens_for(test_engine, "connect")
def enable_test_foreign_keys(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def phase3_database():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)
    test_engine.dispose()
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_phase3.db"):
        os.remove("./test_phase3.db")


@pytest.fixture(scope="module")
def seed_data(phase3_database):
    db = TestingSessionLocal()
    season = Temporada(
        nombre="2028/29", fecha_inicio=date(2028, 7, 1),
        fecha_fin=date(2029, 6, 30),
    )
    tipo = TipoTarea(nombre="Rondo")
    espacio = Espacio(descripcion_original="20 x 20")
    tiempo = Tiempo(descripcion_original="10 minutos")
    user_a = Usuario(
        usuario="phase3_a", password_hash=get_password_hash("pass_a"), activo=True
    )
    user_b = Usuario(
        usuario="phase3_b", password_hash=get_password_hash("pass_b"), activo=True
    )
    db.add_all([season, tipo, espacio, tiempo, user_a, user_b])
    db.flush()
    db.add_all([
        PerfilEntrenador(
            usuario_id=user_a.id, nombre="Ana", apellidos="López",
            temporada_actual_id=season.id,
        ),
        PerfilEntrenador(
            usuario_id=user_b.id, nombre="Bruno", apellidos="Ruiz",
            temporada_actual_id=season.id,
        ),
    ])
    for index in range(5):
        db.add(Entrenamiento(
            usuario_id=user_a.id,
            temporada_id=season.id,
            fecha=date(2028, 8, 18),
            hora=time(8 + (index * 15) // 60, (index * 15) % 60),
            nombre=f"Tarea {index + 1}",
            duracion_minutos=15,
            objetivo_principal="Amplitud",
        ))
    db.add(Entrenamiento(
        usuario_id=user_a.id,
        temporada_id=season.id,
        fecha=date(2028, 8, 19),
        hora=time(10, 0),
        nombre="Sesión única",
        duracion_minutos=60,
        objetivo_principal="Finalización",
    ))
    db.commit()
    result = {"season_id": season.id, "user_a_id": user_a.id, "user_b_id": user_b.id}
    db.close()
    return result


@pytest.fixture(scope="module")
def client_a(seed_data):
    client = TestClient(app)
    response = client.post(
        "/api/auth/login", json={"usuario": "phase3_a", "password": "pass_a"}
    )
    assert response.status_code == 200
    return client


@pytest.fixture(scope="module")
def client_b(seed_data):
    client = TestClient(app)
    response = client.post(
        "/api/auth/login", json={"usuario": "phase3_b", "password": "pass_b"}
    )
    assert response.status_code == 200
    return client


@pytest.fixture(scope="module")
def partido(client_a, seed_data):
    response = client_a.post("/api/partidos", json={
        "fecha": "2028-08-18",
        "hora": "20:00",
        "rival": "CD Gines",
        "local_visitante": "local",
        "campo": "Campo Municipal",
        "observaciones": "Preparar calentamiento específico.",
    })
    assert response.status_code == 201
    return response.json()


def test_crear_partido(partido, seed_data):
    assert partido["rival"] == "CD Gines"
    assert partido["hora"] == "20:00:00"
    assert partido["temporada_id"] == seed_data["season_id"]


def test_obtener_partido(client_a, partido):
    response = client_a.get(f"/api/partidos/{partido['id']}")
    assert response.status_code == 200
    assert response.json()["campo"] == "Campo Municipal"


def test_modificar_partido(client_a, partido):
    response = client_a.put(f"/api/partidos/{partido['id']}", json={
        "hora": "20:30", "campo": "Estadio principal", "local_visitante": "visitante"
    })
    assert response.status_code == 200
    assert response.json()["hora"] == "20:30:00"
    assert response.json()["local_visitante"] == "visitante"


def test_ownership_partido(client_b, partido):
    partido_id = partido["id"]
    assert client_b.get(f"/api/partidos/{partido_id}").status_code == 403
    assert client_b.put(
        f"/api/partidos/{partido_id}", json={"rival": "Alterado"}
    ).status_code == 403
    assert client_b.delete(f"/api/partidos/{partido_id}").status_code == 403


def test_no_permitir_temporada_inexistente(client_a):
    response = client_a.post("/api/partidos", json={
        "fecha": "2028-08-20", "rival": "CF Prueba", "temporada_id": 999999
    })
    assert response.status_code == 422


def test_calendario_entrenamientos_agrupables_por_fecha(client_a):
    response = client_a.get("/api/calendario", params={"year": 2028, "month": 8})
    assert response.status_code == 200
    day = response.json()["planificacion"]["2028-08-18"]
    assert len(day["entrenamientos"]) == 5
    assert day["resumen_entrenamiento"] == {
        "entrenamientos_planificados": 1, "sesiones": 5,
        "duracion_total": 75, "num_ejercicios_total": 0,
    }
    assert [item["nombre"] for item in day["entrenamientos"]] == [
        "Tarea 1", "Tarea 2", "Tarea 3", "Tarea 4", "Tarea 5"
    ]
    assert all("hora" not in item for item in day["entrenamientos"])


def test_dia_con_un_entrenamiento(client_a):
    day = client_a.get(
        "/api/calendario", params={"year": 2028, "month": 8}
    ).json()["planificacion"]["2028-08-19"]
    assert day["resumen_entrenamiento"]["entrenamientos_planificados"] == 1
    assert day["resumen_entrenamiento"]["sesiones"] == 1
    assert day["resumen_entrenamiento"]["duracion_total"] == 60
    assert day["entrenamientos"][0]["nombre"] == "Sesión única"


def test_cinco_sesiones_son_un_entrenamiento_planificado(client_a):
    data = client_a.get(
        "/api/calendario", params={"year": 2028, "month": 8}
    ).json()
    planned_days = [key for key in data["planificacion"] if key == "2028-08-18"]
    assert planned_days == ["2028-08-18"]
    summary = data["planificacion"]["2028-08-18"]["resumen_entrenamiento"]
    assert summary["entrenamientos_planificados"] == 1
    assert summary["sesiones"] == 5


def test_calendario_devuelve_partidos(client_a, partido):
    data = client_a.get(
        "/api/calendario", params={"year": 2028, "month": 8}
    ).json()
    matches = data["planificacion"]["2028-08-18"]["partidos"]
    assert len(matches) == 1
    assert matches[0]["id"] == partido["id"]


def test_dia_contiene_entrenamientos_y_partido(client_a):
    day = client_a.get(
        "/api/calendario", params={"year": 2028, "month": 8}
    ).json()["planificacion"]["2028-08-18"]
    assert day["resumen_entrenamiento"]["entrenamientos_planificados"] == 1
    assert day["resumen_entrenamiento"]["sesiones"] == 5
    assert len(day["partidos"]) == 1


def test_eliminar_partido(client_a, partido):
    partido_id = partido["id"]
    assert client_a.delete(f"/api/partidos/{partido_id}").status_code == 204
    assert client_a.get(f"/api/partidos/{partido_id}").status_code == 404
