from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import exists, select

from app.models import Experiment, Project
from app.schemas import ProjectInput, ProjectOut
from app.security import get_current_user, get_db

router = APIRouter(tags=["projects"])


def owned_project(db, project_id: int, user_id: int) -> Project:
    # Un ID ajeno responde igual que uno inexistente para no revelar que existe.
    project = db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if project is None:
        raise HTTPException(404, "Proyecto no encontrado.")
    return project


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(user=Depends(get_current_user), db=Depends(get_db)):
    return db.scalars(
        select(Project).where(Project.user_id == user.id).order_by(Project.created_at.desc())
    ).all()


@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectInput, user=Depends(get_current_user), db=Depends(get_db)):
    project = Project(**payload.model_dump(), user_id=user.id)
    db.add(project)
    db.commit()
    return project


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    return owned_project(db, project_id, user.id)


@router.put("/projects/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int, payload: ProjectInput, user=Depends(get_current_user), db=Depends(get_db)
):
    project = owned_project(db, project_id, user.id)
    for field, value in payload.model_dump().items():
        setattr(project, field, value)
    db.commit()
    return project


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    project = owned_project(db, project_id, user.id)
    if db.scalar(select(exists().where(Experiment.project_id == project.id))):
        raise HTTPException(409, "El proyecto tiene experimentos. Elimínalos primero.")
    db.delete(project)
    db.commit()
    return Response(status_code=204)
