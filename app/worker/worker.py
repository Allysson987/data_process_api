import logging

from app.scheduler.scheduler import create_scheduler


logging.basicConfig(
    level=logging.INFO,

    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )
)

logger = logging.getLogger(__name__)


def main():

    scheduler = create_scheduler()

    logger.info(
        "Worker de sincronização iniciado."
    )

    try:

        scheduler.start()

    except (KeyboardInterrupt, SystemExit):

        logger.info(
            "Solicitação de encerramento recebida."
        )

        if scheduler.running:

            scheduler.shutdown(
                wait=True
            )

    except Exception:

        logger.exception(
            "Erro fatal no worker."
        )

        raise


if __name__ == "__main__":

    main()