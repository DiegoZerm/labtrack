from tests.conftest import login

EXPERIMENT = {
    "name": "Base",
    "model": "RandomForest",
    "dataset_version": "v1",
    "metric_name": "F1",
    "metric_value": 0.8,
    "notes": "",
}


def add(client, project_id, **changes):
    response = client.post(
        f"/api/projects/{project_id}/experiments", json={**EXPERIMENT, **changes}
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_best_uses_metric_direction(authenticated):
    client = authenticated
    f1 = client.post("/api/projects", json={"name": "Clasificación"}).json()["id"]
    rmse = client.post("/api/projects", json={"name": "Regresión"}).json()["id"]
    empty = client.post("/api/projects", json={"name": "Vacío"}).json()["id"]
    add(client, f1, metric_value=0.81)
    top = add(client, f1, name="Mejor", model="XGBoost", metric_value=0.93)
    add(client, f1, metric_value=0.88)
    add(client, rmse, metric_name="RMSE", metric_value=12.5)
    low = add(client, rmse, name="Menor error", metric_name="RMSE", metric_value=9.1)
    body = client.get("/api/insights").json()
    by_id = {project["id"]: project for project in body["projects"]}
    assert by_id[f1]["experiments"] == 3
    assert by_id[f1]["best"]["id"] == top["id"]
    assert by_id[f1]["higher_is_better"] is True
    assert by_id[rmse]["best"]["id"] == low["id"]
    assert by_id[rmse]["higher_is_better"] is False
    assert by_id[empty] == {"id": empty, "experiments": 0, "last_activity": None, "best": None}
    assert body["highlight"]["id"] in {top["id"], low["id"]}
    assert body["highlight"]["project_name"] in {"Clasificación", "Regresión"}


def test_insights_only_include_own_data(authenticated):
    client = authenticated
    project_id = client.post("/api/projects", json={"name": "De Ana"}).json()["id"]
    add(client, project_id)
    login(client, "luis")
    assert client.get("/api/insights").json() == {"projects": [], "highlight": None}


def test_insights_require_session(client):
    assert client.get("/api/insights").status_code == 401


def test_planned_targets_are_not_results(authenticated):
    client = authenticated
    with_results = client.post("/api/projects", json={"name": "Con resultados"}).json()["id"]
    only_planned = client.post("/api/projects", json={"name": "Solo metas"}).json()["id"]
    done = add(client, with_results, name="Ejecutado", metric_value=0.80)
    add(client, with_results, name="Meta", metric_value=0.95, status="planned")
    add(client, only_planned, name="Meta", metric_value=0.99, status="planned")
    body = client.get("/api/insights").json()
    by_id = {project["id"]: project for project in body["projects"]}
    assert by_id[with_results]["best"]["id"] == done["id"]
    assert by_id[with_results]["experiments"] == 2
    assert by_id[only_planned]["best"] is None
    assert by_id[only_planned]["experiments"] == 1
    assert body["highlight"]["id"] == done["id"]
