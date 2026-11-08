from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.process_search import router as process_router


api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(process_router)