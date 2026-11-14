import logging

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings

from app.scheduler.diary_jobs import (
    DiarySyncJob,
    DiaryNationalSyncJob
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


def create_scheduler() -> BlockingScheduler:

    ufs = get_ufs()

    logger.info(
        "UFs configuradas: %s",
        ufs
    )

    scheduler = BlockingScheduler(
        timezone=TIMEZONE
    )

    # Coleta estadual
    if ufs:

        diary_job = DiarySyncJob(ufs)

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
            name="Sincronização diária estadual",

            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
            replace_existing=True
        )

    # Coleta nacional
    national_job = DiaryNationalSyncJob()

    scheduler.add_job(
        func=national_job.execute,

        trigger=IntervalTrigger(
            minutes=INTERVAL_MINUTES,
            start_date=(
                datetime.now(TIMEZONE)
                + timedelta(minutes=5)
            ),
            timezone=TIMEZONE
        ),

        id="daily_national_diary_sync",
        name="Sincronização diária nacional",

        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
        replace_existing=True
    )

    logger.info(
        "Jobs registrados. Intervalo: %s minutos.",
        INTERVAL_MINUTES
    )

    return scheduler