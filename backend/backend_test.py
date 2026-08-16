import sys
import os
os.environ["SESSION_SECRET"] = "dummy"
from fastapi.testclient import TestClient
from app.main import app
from app.api.auth import get_current_user
from app.models.models import Usuario

def override_get_current_user():
    user = Usuario()
    user.id = 1
    return user

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)
response = client.get("/api/ejercicios?scope=favoritos&page=1&page_size=20")
print("STATUS:", response.status_code)
if response.status_code != 200:
    import json
    print("ERROR:", json.dumps(response.json(), indent=2))
else:
    print("SUCCESS, total:", response.json().get("total"))
    print("SUCCESS, official_total:", response.json().get("official_total"))
