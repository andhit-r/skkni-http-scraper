from fastapi import APIRouter
from app.api.v1.endpoints.skkni import router as skkni_router

api_router = APIRouter()
api_router.include_router(skkni_router)
