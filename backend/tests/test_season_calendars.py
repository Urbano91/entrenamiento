"""Aislamiento de temporadas sobre una SQLite temporal por cada test."""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app
from app.models.models import (
    Ejercicio, Espacio, PerfilEntrenador, Temporada, Tiempo, TipoTarea, Usuario,
)
from app.scripts.create_user import get_password_hash


@pytest.fixture
def scenario(tmp_path):
    database = tmp_path / "season-calendars.sqlite"
    engine = create_engine(
        f"sqlite:///{database}", connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    session_factory = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    Base.metadata.create_all(bind=engine)
    db = session_factory()
    season_a = Temporada(
        nombre="2030/31", fecha_inicio=date(2030, 7, 1),
        fecha_fin=date(2031, 6, 30),
    )
    user = Usuario(
        usuario="season_user", password_hash=get_password_hash("pass"), activo=True
    )
    task_type = TipoTarea(nombre="Posesión")
    space = Espacio(descripcion_original="20 x 20")
    duration = Tiempo(descripcion_original="10 minutos")
    db.add_all([season_a, user, task_type, space, duration])
    db.flush()
    exercise = Ejercicio(
        numero=9901, codigo="SEASON001", nombre="Rondo global",
        tipo_tarea_id=task_type.id, jugadores=8,
        espacio_id=space.id, tiempo_id=duration.id,
    )
    db.add_all([
        exercise,
        PerfilEntrenador(
            usuario_id=user.id, nombre="Alex", apellidos="Temporada",
            temporada_actual_id=season_a.id,
        ),
    ])
    db.commit()
    values = {
        "season_a_id": season_a.id,
        "exercise_id": exercise.id,
        "session_factory": session_factory,
    }
    db.close()

    def override_get_db():
        test_db = session_factory()
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    response = client.post(
        "/api/auth/login", json={"usuario": "season_user", "password": "pass"}
    )
    assert response.status_code == 200
    values["client"] = client
    yield values
    client.close()
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def create_training(client: TestClient, name: str, training_date="2030-08-10"):
    response = client.post("/api/entrenamientos", json={
        "fecha": training_date,
        "nombre": name,
        "duracion_minutos": 45,
        "observaciones": "Plan de trabajo",
    })
    assert response.status_code == 201
    return response.json()


def create_season_b(client: TestClient):
    response = client.post("/api/temporadas", json={
        "nombre": "2031/32",
        "fecha_inicio": "2031-07-01",
        "fecha_fin": "2032-06-30",
    })
    assert response.status_code == 200
    return response.json()


def calendar(client: TestClient, season_id: int, year=2030, month=8):
    response = client.get("/api/calendario", params={
        "year": year, "month": month, "temporada_id": season_id,
    })
    assert response.status_code == 200
    return response.json()


def test_01_training_appears_only_in_season_a(scenario):
    client = scenario["client"]
    training = create_training(client, "Trabajo en A")
    data = calendar(client, scenario["season_a_id"])
    assert training["temporada_id"] == scenario["season_a_id"]
    assert data["planificacion"]["2030-08-10"]["entrenamientos"][0]["id"] == training["id"]


def test_02_new_season_starts_with_empty_calendar(scenario):
    season_b = create_season_b(scenario["client"])
    data = calendar(scenario["client"], season_b["id"], year=2031)
    assert season_b["activa"] is True
    assert data["planificacion"] == {}


def test_03_season_b_never_contains_training_from_a(scenario):
    client = scenario["client"]
    training_a = create_training(client, "Solo A")
    season_b = create_season_b(client)
    assert calendar(client, season_b["id"], year=2030)["planificacion"] == {}
    ids_a = calendar(client, scenario["season_a_id"])["dias"]["2030-08-10"]
    assert training_a["id"] in [item["id"] for item in ids_a]


def test_04_training_automatically_uses_active_season_b(scenario):
    client = scenario["client"]
    season_b = create_season_b(client)
    training_b = create_training(client, "Trabajo en B", "2031-08-10")
    assert training_b["temporada_id"] == season_b["id"]
    assert "2031-08-10" in calendar(client, season_b["id"], year=2031)["dias"]


def test_05_match_is_isolated_in_active_season_b(scenario):
    client = scenario["client"]
    season_b = create_season_b(client)
    response = client.post("/api/partidos", json={
        "fecha": "2031-08-15", "hora": "18:30", "rival": "Sevilla FC",
        "local_visitante": "local", "observaciones": "Liga",
    })
    assert response.status_code == 201
    assert response.json()["temporada_id"] == season_b["id"]
    matches_b = calendar(client, season_b["id"], year=2031)["planificacion"]
    assert matches_b["2031-08-15"]["partidos"][0]["rival"] == "Sevilla FC"
    assert calendar(client, scenario["season_a_id"], year=2031)["planificacion"] == {}


def test_06_same_day_is_grouped_once(scenario):
    client = scenario["client"]
    create_training(client, "Activación")
    create_training(client, "Posesión")
    data = calendar(client, scenario["season_a_id"])
    assert list(data["planificacion"]) == ["2030-08-10"]
    day = data["planificacion"]["2030-08-10"]
    assert day["resumen_entrenamiento"]["sesiones"] == 2
    agenda = client.get("/api/planificaciones/agenda", params={
        "desde": "2030-08-10", "temporada_id": scenario["season_a_id"],
    }).json()
    assert len(agenda) == 1
    assert agenda[0]["entrenamiento"]["sesiones"] == 2


def test_07_reuse_copies_to_active_b_and_remains_independent(scenario):
    client = scenario["client"]
    original = create_training(client, "Original A")
    added = client.post(f"/api/entrenamientos/{original['id']}/ejercicios", json={
        "ejercicio_id": scenario["exercise_id"], "orden": 0,
    })
    assert added.status_code == 201
    season_b = create_season_b(client)
    copied_response = client.post(
        f"/api/entrenamientos/{original['id']}/reutilizar",
        json={"fecha": "2031-08-12"},
    )
    assert copied_response.status_code == 201
    copied = copied_response.json()
    assert copied["temporada_id"] == season_b["id"]
    assert copied["ejercicios"][0]["ejercicio_id"] == scenario["exercise_id"]
    assert copied["ejercicios"][0]["id"] != added.json()["id"]
    assert client.put(
        f"/api/entrenamientos/{copied['id']}", json={"nombre": "Copia editada"}
    ).status_code == 200
    assert client.get(
        f"/api/entrenamientos/{original['id']}"
    ).json()["nombre"] == "Original A"


def test_08_exercise_library_is_global_and_not_duplicated(scenario):
    client = scenario["client"]
    training_a = create_training(client, "A usa ejercicio")
    assert client.post(f"/api/entrenamientos/{training_a['id']}/ejercicios", json={
        "ejercicio_id": scenario["exercise_id"],
    }).status_code == 201
    create_season_b(client)
    training_b = create_training(client, "B usa ejercicio", "2031-08-10")
    assert client.post(f"/api/entrenamientos/{training_b['id']}/ejercicios", json={
        "ejercicio_id": scenario["exercise_id"],
    }).status_code == 201
    db = scenario["session_factory"]()
    try:
        assert db.query(Ejercicio).count() == 1
    finally:
        db.close()


def test_09_rejects_manual_nonexistent_training_season(scenario):
    response = scenario["client"].post("/api/entrenamientos", json={
        "fecha": "2030-08-20", "nombre": "Inválido", "temporada_id": 999999,
    })
    assert response.status_code == 422


def test_10_rejects_manual_nonexistent_match_season(scenario):
    response = scenario["client"].post("/api/partidos", json={
        "fecha": "2030-08-20", "rival": "Inválido", "temporada_id": 999999,
    })
    assert response.status_code == 422
