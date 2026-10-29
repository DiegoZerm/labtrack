import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.models import User
from app.security import password_hasher
from tests.conftest import PASSWORD, login

NEW = {"email": "Nueva@Example.com", "password": "contrasena-segura-2026"}


@pytest.fixture
def admin_client(database_url):
    app = create_app(
        Settings(
            _env_file=None,
            database_url=database_url,
            allowed_origins=["http://testserver"],
            admin_emails=["Admin@Example.com"],
        )
    )
    with app.state.session_factory() as db:
        db.add_all(
            [
                User(email=f"{name}@example.com", password_hash=password_hasher.hash(PASSWORD))
                for name in ["admin", "ana"]
            ]
        )
        db.commit()
    with TestClient(app, headers={"Origin": "http://testserver"}) as client:
        yield client
    app.state.engine.dispose()


def test_session_reports_admin_role(admin_client):
    assert login(admin_client, "admin").json()["is_admin"] is True
    assert admin_client.get("/api/auth/me").json()["is_admin"] is True
    assert login(admin_client, "ana").json()["is_admin"] is False


def test_admin_creates_user_who_can_log_in(admin_client):
    login(admin_client, "admin")
    response = admin_client.post("/api/admin/users", json=NEW)
    assert response.status_code == 201, response.text
    assert response.json()["email"] == "nueva@example.com"
    created = admin_client.post(
        "/api/auth/login", json={"email": "nueva@example.com", "password": NEW["password"]}
    )
    assert created.status_code == 200
    admin_client.headers["X-CSRF-Token"] = created.json()["csrf_token"]
    assert admin_client.get("/api/projects").json() == []


def test_admin_list_shows_counts_but_no_secrets(admin_client):
    login(admin_client, "ana")
    project_id = admin_client.post("/api/projects", json={"name": "De Ana"}).json()["id"]
    login(admin_client, "admin")
    users = {user["email"]: user for user in admin_client.get("/api/admin/users").json()}
    assert users["ana@example.com"]["projects"] == 1
    assert users["admin@example.com"]["is_admin"] is True
    assert all(
        set(user) == {"id", "email", "is_admin", "projects", "experiments"}
        for user in users.values()
    )
    assert admin_client.get(f"/api/projects/{project_id}").status_code == 404


def test_duplicate_and_invalid_users_are_rejected(admin_client):
    login(admin_client, "admin")
    assert admin_client.post("/api/admin/users", json=NEW).status_code == 201
    again = admin_client.post("/api/admin/users", json={**NEW, "email": "NUEVA@example.com"})
    assert again.status_code == 409
    for payload in [
        {"email": "no-es-correo", "password": NEW["password"]},
        {"email": "otra@example.com", "password": "corta"},
        {**NEW, "email": "otra@example.com", "is_admin": True},
    ]:
        assert admin_client.post("/api/admin/users", json=payload).status_code == 422


def test_regular_user_cannot_manage_users(admin_client):
    login(admin_client, "ana")
    assert admin_client.get("/api/admin/users").status_code == 403
    assert admin_client.post("/api/admin/users", json=NEW).status_code == 403


def test_admin_endpoints_require_session_and_csrf(admin_client):
    assert admin_client.get("/api/admin/users").status_code == 401
    login(admin_client, "admin")
    del admin_client.headers["X-CSRF-Token"]
    assert admin_client.post("/api/admin/users", json=NEW).status_code == 403


def test_public_registration_is_gone(admin_client):
    assert admin_client.post("/api/auth/register", json=NEW).status_code in {404, 405}


def test_no_admins_by_default(client):
    assert login(client, "ana").json()["is_admin"] is False
    assert client.get("/api/admin/users").status_code == 403
