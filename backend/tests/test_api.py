import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.api import ejercicios as ejercicios_api
from app.db.database import SessionLocal
from app.models.models import Usuario
from app.scripts.create_user import get_password_hash

client = TestClient(app)

@pytest.fixture(scope="module")
def api_client():
    # Login antes de ejecutar tests de API protegidos
    db = SessionLocal()
    user = db.query(Usuario).filter(Usuario.usuario == "apitestuser").first()
    if not user:
        user = Usuario(usuario="apitestuser", password_hash=get_password_hash("testpass"), activo=True)
        db.add(user)
        db.commit()
    db.close()
    
    client.post("/api/auth/login", json={"usuario": "apitestuser", "password": "testpass"})
    yield client

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200

def test_ejercicios_listado(api_client):
    res = api_client.get("/api/ejercicios")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data

def test_ejercicios_busqueda_codigo(api_client):
    res = api_client.get("/api/ejercicios", params={"q": "A"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) >= 1

def test_ejercicios_filtro_tipo(api_client):
    res = api_client.get("/api/ejercicios", params={"tipo": "Rondo"})
    assert res.status_code == 200
    for item in res.json()["items"]:
        assert item["tipo"]["nombre"] == "Rondo"

def test_catalogos(api_client):
    for cat in ["tipos", "objetivos"]:
        res = api_client.get(f"/api/{cat}")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

def test_detalle_ejercicio(api_client):
    res = api_client.get("/api/ejercicios")
    ej_id = res.json()["items"][0]["id"]
    det = api_client.get(f"/api/ejercicios/{ej_id}")
    assert det.status_code == 200
    assert "desarrollo" in det.json()


def test_biblioteca_visual_completa_existe():
    animations_dir = Path(__file__).resolve().parents[2] / "animations"
    expected_ids = {str(exercise_id) for exercise_id in range(1, 115)}
    assert {path.parent.name for path in animations_dir.glob("*/animacion.webm")} == expected_ids
    assert {path.parent.name for path in animations_dir.glob("*/portada.webp")} == expected_ids
    for exercise_id in range(1, 115):
        exercise_dir = animations_dir / str(exercise_id)
        assert (exercise_dir / "animacion.webm").stat().st_size > 0
        cover = exercise_dir / "portada.webp"
        assert cover.stat().st_size > 0
        assert cover.read_bytes()[:4] == b"RIFF"


def test_animacion_disponible_y_marcada(api_client):
    items = []
    for page in (1, 2):
        listing = api_client.get("/api/ejercicios", params={"page": page, "page_size": 100})
        assert listing.status_code == 200
        items.extend(listing.json()["items"])
    assert len(items) == 114
    assert all(item["tiene_portada"] and item["tiene_animacion"] for item in items)

    detail = api_client.get("/api/ejercicios/73")
    assert detail.status_code == 200
    assert detail.json()["tiene_animacion"] is True

    response = api_client.get("/api/ejercicios/73/animacion")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("video/webm")
    assert response.content[:4] == b"\x1aE\xdf\xa3"

    cover = api_client.get("/api/ejercicios/73/portada")
    assert cover.status_code == 200
    assert cover.headers["content-type"].startswith("image/webp")
    assert cover.content[:4] == b"RIFF"


def test_animacion_ausente_mantiene_portada(api_client, monkeypatch, tmp_path):
    source_cover = Path(__file__).resolve().parents[2] / "animations" / "1" / "portada.webp"
    exercise_dir = tmp_path / "1"
    exercise_dir.mkdir()
    (exercise_dir / "portada.webp").write_bytes(source_cover.read_bytes())
    monkeypatch.setattr(ejercicios_api, "ANIMATIONS_DIR", tmp_path)

    detail = api_client.get("/api/ejercicios/1")
    assert detail.status_code == 200
    assert detail.json()["tiene_portada"] is True
    assert detail.json()["tiene_animacion"] is False
    assert api_client.get("/api/ejercicios/1/animacion").status_code == 404
    assert api_client.get("/api/ejercicios/1/portada").status_code == 200


def test_animacion_id_invalido_404(api_client):
    assert api_client.get("/api/ejercicios/999999/animacion").status_code == 404
    assert api_client.get("/api/ejercicios/999999/portada").status_code == 404
