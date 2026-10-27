import pytest


@pytest.mark.parametrize(
    ("path", "assets"),
    [
        ("/", ["/static/styles.css", "/static/theme.css", "/static/app.js", "/static/registro.js"]),
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


def test_v1_keeps_original_login_without_signup(client):
    html = client.get("/v1").text
    assert 'id="login-form"' in html
    assert "register-form" not in html
