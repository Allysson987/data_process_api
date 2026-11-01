from fastapi import FastAPI
from app.api.router import api_router

app = FastAPI()

# Insere a rota com o prefixo global /api/v1
app.include_router(api_router, prefix="/api/v1")