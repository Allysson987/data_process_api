
import logging

from app.controllers.controller_execution import (
    ControllerExecutionDataJud,
    ExecutionAlreadyRunningError
)

from app.use_cases.diary_cache_service import (
    DiaryCacheService
)


logger = logging.getLogger(__name__)


class DiarySyncJob:

    def __init__(self, ufs: list[str]):

        self.ufs = [
            uf.strip().upper()
            for uf in ufs
            if uf.strip()
        ]

        self.controller = ControllerExecutionDataJud()
        self.cache_service = DiaryCacheService()

    def execute(self):

        logger.info(
            "Iniciando ciclo de sincronização: %s",
            self.ufs
        )

        results = []

        for uf in self.ufs:

            try:

                logger.info(
                    "Iniciando sincronização da UF %s",
                    uf
                )

                result = self.controller.consult_diary_rules(
                    uf.lower()
                )

                self.cache_service.invalidate(uf)

                results.append({
                    "uf": uf,
                    "status": "completed",
                    "result": result
                })

                logger.info(
                    "Sincronização concluída para %s",
                    uf
                )

            except ExecutionAlreadyRunningError as error:

                logger.warning(
                    "UF %s já possui uma coleta ativa: %s",
                    uf,
                    error
                )

                results.append({
                    "uf": uf,
                    "status": "already_running"
                })

            except Exception as error:

                logger.exception(
                    "Falha na sincronização da UF %s",
                    uf
                )

                results.append({
                    "uf": uf,
                    "status": "failed",
                    "error": str(error)
                })

        logger.info(
            "Ciclo de sincronização finalizado."
        )

        return results
