"""Indicadores del panel: mejor resultado por proyecto y último récord del usuario."""

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.models import Experiment, Project
from app.security import get_current_user, get_db

router = APIRouter(tags=["insights"])

# Métricas de error: un valor menor es mejor. Para el resto, mayor es mejor.
LOWER_IS_BETTER = {"RMSE", "MAE", "MSE", "MAPE", "LOSS", "LOG LOSS", "ERROR"}


def higher_is_better(metric_name: str) -> bool:
    return metric_name.strip().upper() not in LOWER_IS_BETTER


def best_of(experiments, metric_name):
    candidates = [e for e in experiments if e.metric_name == metric_name]
    pick = max if higher_is_better(metric_name) else min
    return pick(candidates, key=lambda e: (e.metric_value, e.created_at))


def experiment_view(experiment):
    return {
        "id": experiment.id,
        "name": experiment.name,
        "model": experiment.model,
        "metric_name": experiment.metric_name,
        "metric_value": experiment.metric_value,
        "created_at": experiment.created_at,
    }


@router.get("/insights")
def insights(user=Depends(get_current_user), db=Depends(get_db)):
    rows = db.execute(
        select(Project, Experiment)
        .outerjoin(Experiment, Experiment.project_id == Project.id)
        .where(Project.user_id == user.id)
    ).all()
    by_project = {}
    for project, experiment in rows:
        entry = by_project.setdefault(project.id, {"project": project, "experiments": []})
        if experiment is not None:
            entry["experiments"].append(experiment)

    projects, records = [], []
    for project_id, entry in by_project.items():
        experiments = entry["experiments"]
        if not experiments:
            projects.append(
                {"id": project_id, "experiments": 0, "last_activity": None, "best": None}
            )
            continue
        # La métrica principal es la más usada en el proyecto.
        metric_name = Counter(e.metric_name for e in experiments).most_common(1)[0][0]
        best = best_of(experiments, metric_name)
        records.append((best, entry["project"]))
        projects.append(
            {
                "id": project_id,
                "experiments": len(experiments),
                "last_activity": max(e.created_at for e in experiments),
                "higher_is_better": higher_is_better(metric_name),
                "best": experiment_view(best),
            }
        )

    highlight = None
    if records:
        # El récord más reciente entre los mejores resultados de cada proyecto.
        best, project = max(records, key=lambda record: record[0].created_at)
        highlight = {
            **experiment_view(best),
            "project_id": project.id,
            "project_name": project.name,
        }
    return {"projects": projects, "highlight": highlight}
