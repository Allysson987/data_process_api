
import logging

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.scheduler.diary_jobs import DiarySyncJob


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    )
)

logger = logging.getLogger(__name__)

INTERVAL_MINUTES = 1440
TIMEZONE = ZoneInfo("America/Recife")


def get_ufs() -> list[str]:

    return [
        uf.strip().upper()
        for uf in settings.DIARY_UFS.split(",")
        if uf.strip()
    ]


def main():

    ufs = get_ufs()

    if not ufs:
        raise RuntimeError(
            "Nenhuma UF configurada em DIARY_UFS."
        )

    logger.info(
        "UFs configuradas: %s",
        ufs
    )

    diary_job = DiarySyncJob(ufs)

    scheduler = BlockingScheduler(
        timezone=TIMEZONE
    )

    scheduler.add_job(
        func=diary_job.execute,
        trigger=IntervalTrigger(
            minutes=INTERVAL_MINUTES,
            start_date=(
                datetime.now(TIMEZONE)
                + timedelta(seconds=15)
            ),
            timezone=TIMEZONE
        ),
        id="daily_diary_sync",
        name="Sincronização diária dos diários",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
        replace_existing=True
    )

    logger.info(
        "Scheduler iniciado. Intervalo: %s minutos.",
        INTERVAL_MINUTES
    )

    try:
        scheduler.start()

    except (KeyboardInterrupt, SystemExit):

        logger.info("Encerrando scheduler...")

        scheduler.shutdown(wait=True)


if __name__ == "__main__":
    main()
