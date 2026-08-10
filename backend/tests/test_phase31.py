"""Fase 3.1: agenda diaria, notas y documentos sobre recursos temporales."""

import io
import os
import zipfile
from datetime import date, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app
from app.models.models import (
    Entrenamiento, Partido, PerfilEntrenador, Temporada, Usuario,
)
from app.scripts.create_user import get_password_hash
from app.services.storage import LocalStorageService, get_storage_service


TEST_DB_URL = "sqlite:///./test_phase31.db"
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
def phase31_database(tmp_path_factory):
    storage = LocalStorageService(tmp_path_factory.mktemp("phase31_documents"))
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage_service] = lambda: storage
    yield
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_storage_service, None)
    test_engine.dispose()
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_phase31.db"):
        os.remove("./test_phase31.db")


@pytest.fixture(scope="module")
def seed_data(phase31_database):
    db = TestingSessionLocal()
    season = Temporada(nombre="2029/30")
    user_a = Usuario(
        usuario="phase31_a", password_hash=get_password_hash("pass_a"), activo=True
    )
    user_b = Usuario(
        usuario="phase31_b", password_hash=get_password_hash("pass_b"), activo=True
    )
    db.add_all([season, user_a, user_b])
    db.flush()
    db.add_all([
        PerfilEntrenador(
            usuario_id=user_a.id, nombre="Alicia", apellidos="Díaz",
            temporada_actual_id=season.id,
        ),
        PerfilEntrenador(
            usuario_id=user_b.id, nombre="Berto", apellidos="León",
            temporada_actual_id=season.id,
        ),
    ])
    for index in range(4):
        db.add(Entrenamiento(
            usuario_id=user_a.id, temporada_id=season.id,
            fecha=date(2029, 8, 10), hora=time(8, index * 15),
            nombre=f"Bloque {index + 1}", duracion_minutos=20,
        ))
    db.add(Entrenamiento(
        usuario_id=user_a.id, temporada_id=season.id,
        fecha=date(2029, 8, 11), hora=time(9), nombre="Recuperación",
        duracion_minutos=45,
    ))
    match = Partido(
        usuario_id=user_a.id, temporada_id=season.id,
        fecha=date(2029, 8, 10), hora=time(20), rival="CD Gines",
        local_visitante="local",
    )
    db.add(match)
    db.commit()
    result = {"match_id": match.id, "date": "2029-08-10"}
    db.close()
    return result


@pytest.fixture(scope="module")
def client_a(seed_data):
    client = TestClient(app)
    response = client.post(
        "/api/auth/login", json={"usuario": "phase31_a", "password": "pass_a"}
    )
    assert response.status_code == 200
    return client


@pytest.fixture(scope="module")
def client_b(seed_data):
    client = TestClient(app)
    response = client.post(
        "/api/auth/login", json={"usuario": "phase31_b", "password": "pass_b"}
    )
    assert response.status_code == 200
    return client


@pytest.fixture(scope="module")
def daily_document(client_a, seed_data):
    response = client_a.post(
        f"/api/planificaciones/{seed_data['date']}/documentos",
        files={"archivo": ("microciclo.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()


def _xlsx_bytes() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("xl/workbook.xml", "<workbook />")
    return output.getvalue()


def test_agenda_agrupa_varios_entrenamientos_del_mismo_dia(client_a):
    response = client_a.get(
        "/api/planificaciones/agenda", params={"desde": "2029-08-10", "limite": 10}
    )
    assert response.status_code == 200
    agenda = response.json()
    assert [item["fecha"] for item in agenda] == ["2029-08-10", "2029-08-11"]
    assert agenda[0]["entrenamiento"] == {
        "cantidad": 1, "sesiones": 4, "duracion_total": 80,
    }


def test_dia_aparece_una_sola_vez_y_enlace_correcto(client_a):
    agenda = client_a.get(
        "/api/planificaciones/agenda", params={"desde": "2029-08-10"}
    ).json()
    assert sum(item["fecha"] == "2029-08-10" for item in agenda) == 1
    assert agenda[0]["url_calendario"] == "/calendario?fecha=2029-08-10"


def test_dia_puede_contener_entrenamiento_y_partido(client_a):
    day = client_a.get(
        "/api/planificaciones/agenda", params={"desde": "2029-08-10"}
    ).json()[0]
    assert day["entrenamiento"]["cantidad"] == 1
    assert day["entrenamiento"]["sesiones"] == 4
    assert day["partidos"][0]["rival"] == "CD Gines"


def test_crear_y_listar_documento(daily_document, client_a, seed_data):
    assert daily_document["nombre_original"] == "microciclo.pdf"
    assert daily_document["tipo_mime"] == "application/pdf"
    listed = client_a.get(
        f"/api/planificaciones/{seed_data['date']}/documentos"
    ).json()
    assert [item["id"] for item in listed] == [daily_document["id"]]


def test_documento_asociado_a_planificacion(daily_document, client_a, seed_data):
    context = client_a.get(
        f"/api/planificaciones/{seed_data['date']}"
    ).json()
    assert context["id"] == daily_document["planificacion_id"]
    assert context["documentos"][0]["partido_id"] is None


def test_descargar_documento(client_a, daily_document):
    response = client_a.get(daily_document["download_url"])
    assert response.status_code == 200
    assert response.content == b"%PDF-1.4\n%%EOF"
    assert "microciclo.pdf" in response.headers["content-disposition"]


def test_documento_excel_y_documento_partido(client_a, seed_data):
    response = client_a.post(
        f"/api/planificaciones/{seed_data['date']}/documentos",
        data={"partido_id": str(seed_data["match_id"])},
        files={
            "archivo": (
                "convocatoria.xlsx", _xlsx_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 201
    assert response.json()["partido_id"] == seed_data["match_id"]
    match_documents = client_a.get(
        f"/api/planificaciones/{seed_data['date']}/documentos",
        params={"partido_id": seed_data["match_id"]},
    ).json()
    assert len(match_documents) == 1


def test_subir_imagen_pizarra(client_a, seed_data):
    response = client_a.post(
        f"/api/planificaciones/{seed_data['date']}/documentos",
        files={
            "archivo": (
                "pizarra.png", b"\x89PNG\r\n\x1a\ncontenido", "image/png"
            )
        },
    )
    assert response.status_code == 201
    assert response.json()["tipo_mime"] == "image/png"


def test_no_confiar_solo_en_extension(client_a, seed_data):
    response = client_a.post(
        f"/api/planificaciones/{seed_data['date']}/documentos",
        files={"archivo": ("falso.pdf", b"esto no es pdf", "application/pdf")},
    )
    assert response.status_code == 415


def test_ownership_documentos(client_b, daily_document):
    document_id = daily_document["id"]
    assert client_b.get(f"/api/documentos/{document_id}/descargar").status_code == 403
    assert client_b.delete(f"/api/documentos/{document_id}").status_code == 403


def test_crear_nota(client_a, seed_data):
    response = client_a.put(
        f"/api/planificaciones/{seed_data['date']}/nota",
        json={"contenido": "El equipo trabajó bien la presión."},
    )
    assert response.status_code == 200
    assert response.json()["nota"] == "El equipo trabajó bien la presión."


def test_editar_nota(client_a, seed_data):
    response = client_a.put(
        f"/api/planificaciones/{seed_data['date']}/nota",
        json={"contenido": "Mejorar la salida bajo presión."},
    )
    assert response.status_code == 200
    assert response.json()["nota"] == "Mejorar la salida bajo presión."


def test_eliminar_nota(client_a, seed_data):
    assert client_a.delete(
        f"/api/planificaciones/{seed_data['date']}/nota"
    ).status_code == 204
    assert client_a.get(
        f"/api/planificaciones/{seed_data['date']}"
    ).json()["nota"] is None


def test_eliminar_documento(client_a, daily_document):
    document_id = daily_document["id"]
    assert client_a.delete(f"/api/documentos/{document_id}").status_code == 204
    assert client_a.get(f"/api/documentos/{document_id}/descargar").status_code == 404
