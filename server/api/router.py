"""Main API router that combines all endpoint routers."""

from fastapi import APIRouter

from server.api.documents import router as documents_router
from server.api.generation import router as generation_router
from server.api.profiles import router as profiles_router
from server.api.settings import router as settings_router

api_router = APIRouter(prefix="/api")

# Register sub-routers
api_router.include_router(profiles_router, prefix="/profiles", tags=["profiles"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(generation_router, prefix="/documents", tags=["generation"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
