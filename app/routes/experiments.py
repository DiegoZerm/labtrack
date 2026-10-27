from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select

from app.models import Experiment, Project
from app.routes.projects import owned_project
from app.schemas import ExperimentInput, ExperimentOut
from app.security import get_current_user, get_db

router = APIRouter(tags=["experiments"])


def owned_experiment(db, experiment_id: int, user_id: int) -> Experiment:
    # La propiedad se comprueba a través del proyecto: Experiment no guarda user_id.
    experiment = db.scalar(
        select(Experiment)
        .join(Project)
        .where(Experiment.id == experiment_id, Project.user_id == user_id)
    )
    if experiment is None:
        raise HTTPException(404, "Experimento no encontrado.")
    return experiment


@router.get("/projects/{project_id}/experiments", response_model=list[ExperimentOut])
def list_experiments(
    project_id: int,
    model: str | None = None,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    owned_project(db, project_id, user.id)
    query = select(Experiment).where(Experiment.project_id == project_id)
    if model:
        query = query.where(Experiment.model == model)
    return db.scalars(query.order_by(Experiment.created_at.desc())).all()


@router.post(
    "/projects/{project_id}/experiments", response_model=ExperimentOut, status_code=201
)
def create_experiment(
    project_id: int, payload: ExperimentInput, user=Depends(get_current_user), db=Depends(get_db)
):
    project = owned_project(db, project_id, user.id)
    experiment = Experiment(**payload.model_dump(), project_id=project.id)
    db.add(experiment)
    db.commit()
    return experiment


@router.get("/experiments/{experiment_id}", response_model=ExperimentOut)
def get_experiment(experiment_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    return owned_experiment(db, experiment_id, user.id)


@router.put("/experiments/{experiment_id}", response_model=ExperimentOut)
def update_experiment(
    experiment_id: int,
    payload: ExperimentInput,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    experiment = owned_experiment(db, experiment_id, user.id)
    for field, value in payload.model_dump().items():
        setattr(experiment, field, value)
    db.commit()
    return experiment


@router.delete("/experiments/{experiment_id}", status_code=204)
def delete_experiment(experiment_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    db.delete(owned_experiment(db, experiment_id, user.id))
    db.commit()
    return Response(status_code=204)
