
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Iniciando Data Process API.")

    try:
        yield

    finally:
        logger.info("Encerrando Data Process API.")


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
    lifespan=lifespan,
)


# Origens autorizadas a consumir a API
origins = [
    "http://localhost:3000",
    "https://front-data-process-api.onrender.com"
]


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS"
    ],
    allow_headers=[
        "Authorization",
        "Content-Type"
    ],
)


# Rotas da aplicação
app.include_router(
    api_router,
    prefix="/api",
)
