"""Ejercicio: implementa el contrato de docs/02-arquitectura.md."""
from fastapi import APIRouter, Depends, HTTPException
from app.security import get_current_user

router = APIRouter(tags=["experiments"], dependencies=[Depends(get_current_user)])

@router.api_route("/projects/{project_id}/experiments", methods=["GET", "POST", "PUT", "DELETE"])
@router.api_route("/experiments/{experiment_id}", methods=["GET", "POST", "PUT", "DELETE"])
def pending():
    raise HTTPException(501, "Etapa pendiente: implementa experiments con el prompt correspondiente.")
