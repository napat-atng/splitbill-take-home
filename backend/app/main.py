from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.groups import router as groups_router
from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-User", "Idempotency-Key"],
)
register_error_handlers(app)
app.include_router(health_router)
app.include_router(groups_router)
