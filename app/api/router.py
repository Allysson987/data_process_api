from fastapi import APIRouter
from app.api.v1.endpoints import users, auth, processes  # Seus arquivos de rotas

# Cria o roteador principal da API
api_router = APIRouter()

# Agrupa e adiciona os sub-roteadores com seus respectivos prefixos e tags

api_router.include_router(processes.router, prefix="/sincronizacao", tags=["Sincronizacao"])