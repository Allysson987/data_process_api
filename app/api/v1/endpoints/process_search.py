
import logging

from fastapi import APIRouter, HTTPException, Query

from app.controllers.controller_execution import (
    ControllerExecutionDataJud
)

from app.database.connection import SessionLocal
from app.database.redis_connection import redis_client

from app.models.models_diary import Diary

from app.use_cases.diary_cache_service import (
    DiaryCacheService
)


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


@router.get("/diary/{uf}")
def get_diary_info(
    uf: str,
    limit: int = Query(default=10, ge=1, le=100)
):

    uf = uf.strip().upper()

    if len(uf) != 2 or not uf.isalpha():
        raise HTTPException(
            status_code=400,
            detail="UF inválida."
        )

    # 1. Tenta buscar no Redis
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

    # 2. Cache miss: consulta o Neon
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

        # 3. Atualiza o cache
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


@router.get("/diary/{uf}/status")
def get_diary_status(uf: str):

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


@router.get("/consult_case/{number_case}")
def get_process_info(number_case: str):

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
