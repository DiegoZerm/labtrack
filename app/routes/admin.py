"""Gestión de cuentas reservada al administrador (ADMIN_EMAILS en .env).

El administrador crea y lista cuentas, pero no accede a los proyectos de otros usuarios:
solo ve cuántos tiene cada uno.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models import Experiment, Project, User
from app.schemas import NewUserInput
from app.security import get_db, is_admin, password_hasher, require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(request: Request, admin=Depends(require_admin), db=Depends(get_db)):
    projects = (
        select(Project.user_id, func.count(Project.id).label("total"))
        .group_by(Project.user_id)
        .subquery()
    )
    experiments = (
        select(Project.user_id, func.count(Experiment.id).label("total"))
        .join(Experiment, Experiment.project_id == Project.id)
        .group_by(Project.user_id)
        .subquery()
    )
    rows = db.execute(
        select(User, projects.c.total, experiments.c.total)
        .outerjoin(projects, projects.c.user_id == User.id)
        .outerjoin(experiments, experiments.c.user_id == User.id)
        .order_by(User.email)
    ).all()
    return [
        {
            "id": user.id,
            "email": user.email,
            "is_admin": is_admin(request, user),
            "projects": project_count or 0,
            "experiments": experiment_count or 0,
        }
        for user, project_count, experiment_count in rows
    ]


@router.post("/users", status_code=201)
def create_user(
    payload: NewUserInput, request: Request, admin=Depends(require_admin), db=Depends(get_db)
):
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Ya existe una cuenta con ese correo.")
    user = User(email=email, password_hash=password_hasher.hash(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Otra petición creó la misma cuenta entre la consulta y el INSERT.
        db.rollback()
        raise HTTPException(409, "Ya existe una cuenta con ese correo.") from None
    return {"id": user.id, "email": user.email, "is_admin": is_admin(request, user)}
