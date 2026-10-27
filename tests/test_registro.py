import pytest
from sqlalchemy import select

from app.models import User

NEW = {"email": "Nueva@Example.com", "password": "contrasena-segura-2026"}


def test_register_creates_account_and_session(client):
    response = client.post("/api/auth/register", json=NEW)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == "nueva@example.com"
    client.headers["X-CSRF-Token"] = body["csrf_token"]
    assert client.get("/api/auth/me").json()["email"] == "nueva@example.com"
    assert client.get("/api/projects").json() == []
    assert client.post("/api/projects", json={"name": "Primero"}).status_code == 201


def test_registered_user_can_log_in_again(client):
    client.post("/api/auth/register", json=NEW)
    client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": client.get("/api/auth/me").json()["csrf_token"]},
    )
    response = client.post(
        "/api/auth/login", json={"email": "nueva@example.com", "password": NEW["password"]}
    )
    assert response.status_code == 200


def test_password_is_hashed(app, client):
    client.post("/api/auth/register", json=NEW)
    with app.state.session_factory() as db:
        user = db.scalar(select(User).where(User.email == "nueva@example.com"))
    assert user.password_hash != NEW["password"]
    assert user.password_hash.startswith("$argon2")


def test_duplicate_email_is_rejected(client):
    assert client.post("/api/auth/register", json=NEW).status_code == 201
    again = client.post("/api/auth/register", json={**NEW, "email": "NUEVA@example.com"})
    assert again.status_code == 409
    assert (
        client.post("/api/auth/register", json={**NEW, "email": "ana@example.com"}).status_code
        == 409
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "no-es-correo", "password": NEW["password"]},
        {"email": NEW["email"], "password": "corta"},
        {"email": NEW["email"], "password": "x" * 129},
        {**NEW, "user_id": 1},
        {"email": NEW["email"]},
    ],
)
def test_invalid_registration(client, payload):
    assert client.post("/api/auth/register", json=payload).status_code == 422


def test_register_requires_allowed_origin(client):
    response = client.post(
        "/api/auth/register", json=NEW, headers={"Origin": "https://evil.example"}
    )
    assert response.status_code == 403


def test_new_account_does_not_see_other_users_data(client):
    from tests.conftest import login

    login(client, "ana")
    project_id = client.post("/api/projects", json={"name": "De Ana"}).json()["id"]
    body = client.post("/api/auth/register", json=NEW).json()
    client.headers["X-CSRF-Token"] = body["csrf_token"]
    assert client.get("/api/projects").json() == []
    assert client.get(f"/api/projects/{project_id}").status_code == 404
