from fastapi import APIRouter
from app.api.v1.endpoints import process_search

# Cria o roteador principal da API
api_router = APIRouter()

# Agrupa e adiciona os sub-roteadores com seus respectivos prefixos e tags

api_router.include_router(process_search.router, prefix="/consult_case", tags=["Consult Cases"])