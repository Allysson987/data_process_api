
import logging

from fastapi import APIRouter, HTTPException, Query, Depends, Path

from app.controllers.controller_execution import (
    ControllerExecutionDataJud
)

from app.database.connection import SessionLocal
from app.database.redis_connection import redis_client

from app.models.models_diary import Diary

from app.use_cases.diary_cache_service import (
    DiaryCacheService
)

from app.core.dependencies import get_current_user
from app.models.user import User
from app.use_cases.rate_limit import rate_limit


logger = logging.getLogger(__name__)

router = APIRouter()

consult = ControllerExecutionDataJud()
cache_service = DiaryCacheService()


def serialize_diary(diary: Diary) -> dict:
    return {
        "id": diary.id,
        "source": diary.source,
        "source_id": diary.source_id,
        "publication_date": (
            diary.publication_date.isoformat()
            if diary.publication_date
            else None
        ),
        "available_date": (
            diary.available_date.isoformat()
            if diary.available_date
            else None
        ),
        "update_date": (
            diary.update_date.isoformat()
            if diary.update_date
            else None
        ),
        "title": diary.title,
        "content": diary.content,
        "pdf_url": diary.pdf_url
    }


@router.get(
    "/diary/{uf}",
    tags=["Diários Oficiais"],
    summary="Consultar diários oficiais por estado",
    description="""
    Consulta os diários oficiais de um estado brasileiro.

    **Funcionamento:**
    - Recebe a sigla da Unidade Federativa (UF).
    - Consulta primeiro o Redis para verificar se os dados estão em cache.
    - Caso não existam dados em cache, consulta o banco PostgreSQL.
    - Os resultados são armazenados no Redis para otimizar consultas futuras.

    **Autenticação:** exige token JWT válido.

    **Limite:** 30 requisições por minuto por usuário.
    """,
    response_description="Lista de diários oficiais encontrados para a UF informada.",
    responses={
        200: {
            "description": "Consulta realizada com sucesso."
        },
        400: {
            "description": "Sigla da UF inválida."
        },
        401: {
            "description": "Token de autenticação ausente ou inválido."
        },
        429: {
            "description": "Limite de requisições excedido."
        },
        500: {
            "description": "Erro interno ao consultar os diários."
        }
    },
    dependencies=[
        Depends(get_current_user),
        Depends(rate_limit(30, 60, "user"))
    ]
)
def get_diary_info(
    uf: str = Path(
        description="Sigla da Unidade Federativa.",
        min_length=2,
        max_length=2,
        examples=["PE", "SP", "RJ"]
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Quantidade máxima de diários retornados.",
        examples=[10, 50]
    )
):
    uf = uf.strip().upper()

    if len(uf) != 2 or not uf.isalpha():
        raise HTTPException(
            status_code=400,
            detail="UF inválida."
        )

    cached_data = cache_service.get(
        uf,
        limit
    )

    if cached_data is not None:
        return {
            "status": "sucesso",
            "source": "redis",
            "info": cached_data
        }

    db = SessionLocal()

    try:
        source = f"TJ{uf}"

        diaries = (
            db.query(Diary)
            .filter(Diary.source == source)
            .order_by(
                Diary.publication_date.desc()
            )
            .limit(limit)
            .all()
        )

        result = [
            serialize_diary(diary)
            for diary in diaries
        ]

        cache_service.set(
            uf,
            limit,
            result
        )

        return {
            "status": "sucesso",
            "source": "neon",
            "info": result
        }

    except Exception as error:
        logger.exception(
            "Falha ao consultar diários da UF %s",
            uf
        )

        raise HTTPException(
            status_code=500,
            detail="Erro ao consultar os diários."
        ) from error

    finally:
        db.close()


@router.get(
    "/diary/{uf}/status",
    tags=["Diários Oficiais"],
    summary="Consultar status da sincronização dos diários",
    description="""
    Consulta o estado atual da sincronização dos diários oficiais de uma UF.

    **Funcionamento:**
    - Consulta as informações de sincronização armazenadas no Redis.
    - Retorna `not_started` quando não existe registro de sincronização.
    - Retorna as informações disponíveis quando existe um registro.

    **Autenticação:** exige token JWT válido.

    **Limite:** 60 requisições por minuto por usuário.
    """,
    response_description="Estado atual da sincronização dos diários da UF.",
    responses={
        200: {
            "description": "Status consultado com sucesso."
        },
        400: {
            "description": "Sigla da UF inválida."
        },
        401: {
            "description": "Token de autenticação ausente ou inválido."
        },
        429: {
            "description": "Limite de requisições excedido."
        },
        503: {
            "description": "Redis indisponível ou falha na consulta."
        }
    },
    dependencies=[
        Depends(get_current_user),
        Depends(rate_limit(60, 60, "user"))
    ]
)
def get_diary_status(
    uf: str = Path(
        description="Sigla da Unidade Federativa.",
        min_length=2,
        max_length=2,
        examples=["PE", "SP", "RJ"]
    )
):
    uf = uf.strip().upper()

    if len(uf) != 2 or not uf.isalpha():
        raise HTTPException(
            status_code=400,
            detail="UF inválida."
        )

    if redis_client is None:
        raise HTTPException(
            status_code=503,
            detail="Redis não está configurado."
        )

    try:
        status = redis_client.hgetall(
            f"diary:status:{uf}"
        )

        if not status:
            return {
                "status": "not_started",
                "uf": uf,
                "message": (
                    "Nenhuma sincronização registrada."
                )
            }

        return {
            "uf": uf,
            "info": status
        }

    except Exception as error:
        logger.exception(
            "Falha ao consultar status da UF %s",
            uf
        )

        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar o status."
        ) from error


@router.get(
    "/consult_case/{number_case}",
    tags=["Consulta Processual"],
    summary="Consultar informações de um processo judicial",
    description="""
    Realiza uma consulta processual utilizando o número do processo.

    **Funcionamento:**
    - Recebe o número de identificação do processo judicial.
    - Encaminha a consulta ao controlador DataJud.
    - Retorna as informações obtidas pela consulta.

    **Autenticação:** exige token JWT válido.

    **Limite:** 10 requisições por minuto por usuário.
    """,
    response_description="Dados processuais retornados pela consulta DataJud.",
    responses={
        200: {
            "description": "Consulta processual realizada com sucesso."
        },
        400: {
            "description": "Número do processo inválido ou parâmetro incorreto."
        },
        401: {
            "description": "Token de autenticação ausente ou inválido."
        },
        429: {
            "description": "Limite de requisições excedido."
        },
        500: {
            "description": "Erro interno ao consultar o processo."
        }
    },
    dependencies=[
        Depends(get_current_user),
        Depends(rate_limit(10, 60, "user"))
    ]
)
def get_process_info(
    number_case: str = Path(
        description="Número CNJ do processo judicial.",
        min_length=20,
        max_length=25,
        examples=["0000000-00.0000.0.00.0000"]
    )
):
    try:
        result = consult.consult_process_data_jud(
            number_case
        )

        return {
            "status": "sucesso",
            "info": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        logger.exception(
            "Falha ao consultar processo %s",
            number_case
        )

        raise HTTPException(
            status_code=500,
            detail="Erro ao consultar o processo."
        ) from error
