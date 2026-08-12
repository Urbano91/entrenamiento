"""API aditiva de taxonomía V2 sobre la SQLite ya migrada."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.auth import get_current_user
from app.db.database import engine
from app.main import app


DATABASE_PATH = Path(__file__).resolve().parents[2] / "database" / "futbol_entrenamiento.sqlite"
CATEGORY_COUNTS = {
    "TEC": 16,
    "TO": 27,
    "TD": 16,
    "TRA": 12,
    "MOD": 7,
    "FIS": 9,
    "CP": 5,
    "COG": 2,
}


def file_hash() -> str:
    return hashlib.sha256(DATABASE_PATH.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def api_client():
    before = file_hash()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1)
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_current_user, None)
    assert file_hash() == before, "Las pruebas GET modificaron físicamente SQLite"


def paginated_ids(client: TestClient, params: dict) -> tuple[list[int], int]:
    page_size = 17
    first = client.get(
        "/api/ejercicios", params={**params, "page": 1, "page_size": page_size}
    )
    assert first.status_code == 200, first.text
    first_data = first.json()
    assert first_data["total_pages"] == (
        first_data["total"] + page_size - 1
    ) // page_size

    ids = [item["id"] for item in first_data["items"]]
    for page in range(2, first_data["total_pages"] + 1):
        response = client.get(
            "/api/ejercicios",
            params={**params, "page": page, "page_size": page_size},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["total"] == first_data["total"]
        assert data["total_pages"] == first_data["total_pages"]
        ids.extend(item["id"] for item in data["items"])

    assert len(ids) == first_data["total"]
    assert len(ids) == len(set(ids))
    assert ids == sorted(ids)
    return ids, first_data["total"]


def test_categorias_v2(api_client):
    response = api_client.get("/api/taxonomia/categorias")
    assert response.status_code == 200
    categories = response.json()
    assert len(categories) == 8
    assert [category["codigo"] for category in categories] == list(CATEGORY_COUNTS)
    assert [category["orden"] for category in categories] == list(range(1, 9))


def test_objetivos_v2_y_distribucion(api_client):
    response = api_client.get("/api/taxonomia/objetivos")
    assert response.status_code == 200
    objectives = response.json()
    assert len(objectives) == 94
    assert len({objective["id"] for objective in objectives}) == 94

    categories = api_client.get("/api/taxonomia/categorias").json()
    observed = {}
    for category in categories:
        by_query = api_client.get(
            "/api/taxonomia/objetivos",
            params={"categoria_id": category["id"]},
        )
        by_path = api_client.get(
            f"/api/taxonomia/categorias/{category['id']}/objetivos"
        )
        assert by_query.status_code == 200
        assert by_path.status_code == 200
        assert by_query.json() == by_path.json()
        observed[category["codigo"]] = len(by_path.json())
        assert all(
            objective["categoria_id"] == category["id"]
            for objective in by_path.json()
        )

    assert observed == CATEGORY_COUNTS
    assert sum(observed.values()) == 94


def test_detalle_objetivo_v2(api_client):
    objective = api_client.get("/api/taxonomia/objetivos").json()[0]
    response = api_client.get(f"/api/taxonomia/objetivos/{objective['id']}")
    assert response.status_code == 200
    assert response.json() == objective
    assert api_client.get("/api/taxonomia/objetivos/999999").status_code == 404
    assert (
        api_client.get("/api/taxonomia/categorias/999999/objetivos").status_code
        == 404
    )


def test_filtro_por_cada_objetivo_v2_sin_duplicados(api_client):
    objectives = api_client.get("/api/taxonomia/objetivos").json()
    objectives_with_exercises = 0
    for objective in objectives:
        ids, total = paginated_ids(
            api_client, {"objetivo_v2_id": objective["id"]}
        )
        if total:
            objectives_with_exercises += 1
            assert ids
    assert objectives_with_exercises == 94


def test_filtro_por_cada_categoria_v2_sin_duplicados(api_client):
    categories = api_client.get("/api/taxonomia/categorias").json()
    for category in categories:
        ids, total = paginated_ids(
            api_client, {"categoria_v2_id": category["id"]}
        )
        assert total > 0
        assert ids


def test_paginacion_general_no_repite_ejercicios(api_client):
    ids, total = paginated_ids(api_client, {})
    assert total == 114
    assert len(ids) == 114


def test_filtros_v2_combinados_requieren_el_mismo_destino(api_client):
    objective = api_client.get("/api/taxonomia/objetivos").json()[0]
    matching_ids, _ = paginated_ids(
        api_client,
        {
            "objetivo_v2_id": objective["id"],
            "categoria_v2_id": objective["categoria_id"],
        },
    )
    objective_ids, _ = paginated_ids(
        api_client, {"objetivo_v2_id": objective["id"]}
    )
    assert matching_ids == objective_ids

    other_category = next(
        category
        for category in api_client.get("/api/taxonomia/categorias").json()
        if category["id"] != objective["categoria_id"]
    )
    mismatched_ids, total = paginated_ids(
        api_client,
        {
            "objetivo_v2_id": objective["id"],
            "categoria_v2_id": other_category["id"],
        },
    )
    assert total == 0
    assert mismatched_ids == []


def test_filtro_multiseleccion_objetivos_v2_aplica_or_sin_duplicados(api_client):
    objectives = api_client.get("/api/taxonomia/objetivos").json()
    control = next(objective for objective in objectives if objective["nombre"] == "Control")
    pase = next(objective for objective in objectives if objective["nombre"] == "Pase")
    assert control["categoria_id"] == pase["categoria_id"]

    control_ids, _ = paginated_ids(
        api_client, {"objetivo_v2_id": control["id"]}
    )
    pase_ids, _ = paginated_ids(api_client, {"objetivo_v2_id": pase["id"]})
    combined_ids, combined_total = paginated_ids(
        api_client,
        {
            "objetivo_v2_ids": [control["id"], pase["id"]],
            "categoria_v2_id": control["categoria_id"],
        },
    )

    expected = sorted(set(control_ids) | set(pase_ids))
    assert combined_ids == expected
    assert combined_total == len(expected)


def test_trazabilidad_respeta_excepciones_y_roles(api_client):
    response = api_client.get("/api/taxonomia/ejercicios/39/objetivos")
    assert response.status_code == 200
    traces = response.json()
    assert traces
    assert all(trace["objetivo_original"] for trace in traces)
    assert all(trace["rol_historico"] for trace in traces)

    change_of_chip = [
        trace for trace in traces if trace["objetivo_origen_id"] == 39
    ]
    assert {trace["alcance"] for trace in change_of_chip} == {"excepcion"}
    assert {trace["objetivo_nombre"] for trace in change_of_chip} == {
        "Transición inmediata",
        "Ajuste posicional tras transición",
    }
    assert {trace["rol_historico"] for trace in change_of_chip} == {
        "principal",
        "defensivo",
    }
    assert api_client.get("/api/taxonomia/ejercicios/999999/objetivos").status_code == 404


def test_catalogo_y_filtro_historicos_siguen_compatibles(api_client):
    response = api_client.get("/api/objetivos")
    assert response.status_code == 200
    historical_objectives = response.json()
    assert len(historical_objectives) == 129

    selected = next(
        objective
        for objective in historical_objectives
        if objective["nombre_normalizado"] == "Presión"
    )
    api_ids, total = paginated_ids(
        api_client, {"objetivo": selected["nombre_normalizado"]}
    )
    with engine.connect() as connection:
        expected_ids = connection.execute(
            text(
                "SELECT DISTINCT eo.ejercicio_id FROM ejercicio_objetivo eo "
                "WHERE eo.objetivo_id = :objective_id ORDER BY eo.ejercicio_id"
            ),
            {"objective_id": selected["id"]},
        ).scalars().all()
    assert total > 0
    assert api_ids == expected_ids


def test_metricas_historicas_siguen_intactas():
    with engine.connect() as connection:
        assert connection.execute(text(
            "SELECT COUNT(*) FROM ejercicios e WHERE NOT EXISTS ("
            "SELECT 1 FROM exercise_ownership own WHERE own.ejercicio_id=e.id)"
        )).scalar_one() == 114
        assert connection.execute(text("SELECT COUNT(*) FROM objetivos")).scalar_one() == 129
        assert connection.execute(text("SELECT COUNT(*) FROM ejercicio_objetivo")).scalar_one() == 709
        assert connection.execute(
            text(
                "SELECT COUNT(*) FROM (SELECT DISTINCT ejercicio_id, objetivo_id "
                "FROM ejercicio_objetivo) AS pares"
            )
        ).scalar_one() == 577
        assert connection.execute(
            text("SELECT COUNT(DISTINCT objetivo_original) FROM ejercicio_objetivo")
        ).scalar_one() == 191
