
from datetime import datetime, timezone
from uuid import uuid4
import logging

from app.use_cases.datajud_service import DataJudService
from app.utils.diary_rules import RulesDiary

from app.database.connection import SessionLocal
from app.database.redis_connection import redis_client
from app.repositories.diary_repository import DiaryRepository


logger = logging.getLogger(__name__)


class ExecutionAlreadyRunningError(Exception):
    """Indica que já existe uma coleta ativa para a UF."""


class ControllerExecutionDataJud:

    LOCK_TTL = 86400
    STATUS_TTL = 86400

    RELEASE_LOCK_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    end
    return 0
    """

    RENEW_LOCK_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("expire", KEYS[1], ARGV[2])
    end
    return 0
    """

    def __init__(self):
        self.data_jud_service = DataJudService()
        self.diary_rules = RulesDiary()

    def consult_process_data_jud(self, number_case: str):

        return self.data_jud_service.get_process_info(
            number_case
        )

    def consult_diary_rules(self, uf: str):

        if redis_client is None:
            raise RuntimeError("Redis não está configurado.")

        uf = uf.strip().lower()

        collector = self.diary_rules.get_provider(uf)

        lock_key = f"diary:lock:{uf.upper()}"
        status_key = f"diary:status:{uf.upper()}"

        execution_token = str(uuid4())

        acquired = redis_client.set(
            lock_key,
            execution_token,
            nx=True,
            ex=self.LOCK_TTL
        )

        if not acquired:
            raise ExecutionAlreadyRunningError(
                f"Já existe uma coleta em andamento para {uf.upper()}."
            )

        saved_count = 0

        try:

            started_at = datetime.now(
                timezone.utc
            ).isoformat()

            redis_client.hset(
                status_key,
                mapping={
                    "source": uf.upper(),
                    "status": "running",
                    "saved_count": 0,
                    "current_source_id": "",
                    "started_at": started_at,
                    "updated_at": started_at,
                    "error": ""
                }
            )

            redis_client.expire(
                status_key,
                self.STATUS_TTL
            )

            for diary_data in collector.build_diary():

                # Valida o retorno do coletor.
                if not isinstance(diary_data, dict):
                    raise TypeError(
                        "O coletor retornou um tipo inválido. "
                        f"Esperado dict, recebido {type(diary_data).__name__}. "
                        f"Conteúdo: {str(diary_data)[:300]}"
                    )

                db = SessionLocal()

                try:

                    repository = DiaryRepository(db)

                    repository.create(diary_data)

                    saved_count += 1

                    lock_renewed = redis_client.eval(
                        self.RENEW_LOCK_SCRIPT,
                        1,
                        lock_key,
                        execution_token,
                        self.LOCK_TTL
                    )

                    if not lock_renewed:
                        raise RuntimeError(
                            "O bloqueio Redis foi perdido durante a coleta."
                        )

                    updated_at = datetime.now(
                        timezone.utc
                    ).isoformat()

                    redis_client.hset(
                        status_key,
                        mapping={
                            "status": "running",
                            "saved_count": saved_count,
                            "current_source_id": str(
                                diary_data.get("source_id", "")
                            ),
                            "updated_at": updated_at
                        }
                    )

                    redis_client.expire(
                        status_key,
                        self.STATUS_TTL
                    )

                    logger.info(
                        "Diário salvo: %s",
                        diary_data.get("source_id")
                    )

                except Exception:
                    db.rollback()
                    logger.exception(
                        "Erro ao persistir diário: %s",
                        diary_data.get("source_id")
                    )
                    raise

                finally:
                    db.close()

            finished_at = datetime.now(
                timezone.utc
            ).isoformat()

            redis_client.hset(
                status_key,
                mapping={
                    "status": "completed",
                    "saved_count": saved_count,
                    "finished_at": finished_at,
                    "updated_at": finished_at
                }
            )

            redis_client.expire(
                status_key,
                self.STATUS_TTL
            )

            return {
                "source": uf.upper(),
                "saved_count": saved_count,
                "status": "completed"
            }

        except Exception as error:

            failed_at = datetime.now(
                timezone.utc
            ).isoformat()

            try:
                redis_client.hset(
                    status_key,
                    mapping={
                        "status": "failed",
                        "saved_count": saved_count,
                        "error": str(error)[:1000],
                        "updated_at": failed_at
                    }
                )

                redis_client.expire(
                    status_key,
                    self.STATUS_TTL
                )

            except Exception:
                logger.exception(
                    "Não foi possível atualizar o status no Redis."
                )

            logger.exception(
                "Falha durante a coleta da UF %s",
                uf.upper()
            )

            raise

        finally:

            try:
                redis_client.eval(
                    self.RELEASE_LOCK_SCRIPT,
                    1,
                    lock_key,
                    execution_token
                )

            except Exception:
                logger.exception(
                    "Não foi possível liberar o bloqueio Redis da UF %s.",
                    uf.upper()
                )
