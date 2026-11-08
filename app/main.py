from fastapi import FastAPI
from app.api.router import api_router

app = FastAPI(
    title="Data Process API",
    description="""
    API responsável pelo processamento e gerenciamento de dados.

    ## Funcionalidades
    - Autenticação e autorização
    - Gerenciamento de usuários
    - Controle de acesso
    - Processamento de dados
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(api_router, prefix="/api")