from sqlalchemy import func, select

from app.cli import add_user
from app.models import Experiment, Project, User
from app.showcase import CATALOG, seed_showcase
from tests.conftest import PASSWORD, login


def test_showcase_is_idempotent_and_isolated(app, client):
    with app.state.session_factory() as db:
        first = seed_showcase(db, PASSWORD, add_user)
        db.commit()
        second = seed_showcase(db, PASSWORD, add_user)
        db.commit()
        assert first["projects"] == sum(len(projects) for projects in CATALOG.values())
        assert first["experiments"] > 100
        assert second == {"users": 0, "projects": 0, "experiments": 0}
        assert db.scalar(select(func.count()).select_from(User)) == len(CATALOG)
        assert db.scalar(select(func.count()).select_from(Experiment)) == first["experiments"]
        projects = db.scalars(select(Project)).all()
    assert all(project.created_at is not None for project in projects)
    login(client, "luis")
    names = {project["name"] for project in client.get("/api/projects").json()}
    assert names == {project[0] for project in CATALOG["luis@example.com"]}
    summary = client.get("/api/summary").json()
    assert summary["projects"] == len(CATALOG["luis@example.com"])
