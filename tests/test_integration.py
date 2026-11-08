from datetime import date, timedelta
import json

from app.database.connection import SessionLocal
from app.controllers.controller_execution import ControllerExecution


def test_importar_comunica_pje():

    data_end = date.today()
    data_start = data_end - timedelta(days=1)

    db = SessionLocal()

    try:
        controller = ControllerExecution(db)

        result = controller.import_comunica_pje(
            date_start=data_start.isoformat(),
            date_end=data_end.isoformat(),
        )

        print(json.dumps(
            result,
            ensure_ascii=False,
            indent=4,
            default=str,
        ))

    finally:
        db.close()