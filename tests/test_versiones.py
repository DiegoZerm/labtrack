import pytest


@pytest.mark.parametrize(
    ("path", "assets"),
    [
        (
            "/",
            [
                "/static/styles.css",
                "/static/theme.css",
                "/static/app.js",
                "/static/usuarios.js",
                "/static/panel.js",
                "/static/rei.js",
            ],
        ),
        ("/v1", ["/static/v1/styles.css", "/static/v1/app.js"]),
    ],
)
def test_both_versions_are_served_with_csp(client, path, assets):
    response = client.get(path)
    assert response.status_code == 200
    assert "default-src 'self'" in response.headers["content-security-policy"]
    for asset in assets:
        assert asset in response.text
        assert client.get(asset).status_code == 200


def test_versions_link_to_each_other(client):
    assert 'href="/v1"' in client.get("/").text
    assert 'class="cambio-version" href="/"' in client.get("/v1").text


def test_v1_keeps_original_login(client):
    html = client.get("/v1").text
    assert 'id="login-form"' in html
    assert "usuarios.js" not in html


def test_editing_without_optional_fields_keeps_them(authenticated):
    project_id = authenticated.post("/api/projects", json={"name": "P"}).json()["id"]
    base = {
        "name": "E",
        "model": "M",
        "dataset_version": "v1",
        "metric_name": "F1",
        "metric_value": 0.5,
    }
    created = authenticated.post(
        f"/api/projects/{project_id}/experiments", json={**base, "notes": "Conservar"}
    ).json()
    edited = authenticated.put(
        f"/api/experiments/{created['id']}", json={**base, "metric_value": 0.6}
    )
    assert edited.status_code == 200
    assert edited.json()["metric_value"] == 0.6
    assert edited.json()["notes"] == "Conservar"
