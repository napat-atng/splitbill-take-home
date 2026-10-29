from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionDep
from app.repositories.health import check_connection
from app.schemas import ErrorRead

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("/health")
def health() -> HealthResponse:
    """Process liveness only; database readiness is not checked."""
    return HealthResponse()


@router.get("/ready", responses={503: {"description": "Database unavailable", "model": ErrorRead}})
def readiness(session: SessionDep) -> HealthResponse:
    try:
        check_connection(session)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return HealthResponse()
