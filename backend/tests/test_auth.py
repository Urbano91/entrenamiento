import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, engine, SessionLocal
from app.models.models import Usuario
from app.scripts.create_user import get_password_hash

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    db = SessionLocal()
    user = db.query(Usuario).filter(Usuario.usuario == "testuser").first()
    if not user:
        user = Usuario(usuario="testuser", password_hash=get_password_hash("testpass"), activo=True)
        db.add(user)
        db.commit()
    yield
    # Limpiar solo el testuser si es necesario 
    pass

def test_login_correcto(setup_db):
    response = client.post("/api/auth/login", json={"usuario": "testuser", "password": "testpass"})
    assert response.status_code == 200
    assert "session" in response.cookies

def test_login_incorrecto(setup_db):
    response = client.post("/api/auth/login", json={"usuario": "testuser", "password": "wrong"})
    assert response.status_code == 401
    assert "session" not in response.cookies

def test_ruta_protegida_sin_sesion():
    new_client = TestClient(app)
    response = new_client.get("/api/ejercicios")
    assert response.status_code == 401

def test_logout(setup_db):
    client.post("/api/auth/login", json={"usuario": "testuser", "password": "testpass"})
    response = client.post("/api/auth/logout")
    assert response.status_code == 200

def test_auth_me(setup_db):
    client.post("/api/auth/login", json={"usuario": "testuser", "password": "testpass"})
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["usuario"] == "testuser"
    assert "password_hash" not in data
    assert "password" not in data
