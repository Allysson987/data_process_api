
from app.use_cases.datajud_service import DataJudService
from app.utils.diary_rules import RulesDiary

from app.database.connection import SessionLocal
from app.repositories.diary_repository import DiaryRepository


class ControllerExecutionDataJud:

    def __init__(self):

        self.data_jud_service = DataJudService()
        self.diary_rules = RulesDiary()

    def consult_process_data_jud(
        self,
        number_case: str
    ):

        return self.data_jud_service.get_process_info(
            number_case
        )

    def consult_diary_rules(
        self,
        uf: str
    ):

        collector = self.diary_rules.get_provider(uf)

        saved_count = 0

        for diary_data in collector.build_diary():

            db = SessionLocal()

            try:

                repository = DiaryRepository(db)

                repository.create(diary_data)

                saved_count += 1

                print(
                    f"Diário salvo: {diary_data['source_id']}",
                    flush=True
                )

            except Exception:

                db.rollback()
                raise

            finally:

                db.close()

        return {
            "source": uf.upper(),
            "saved_count": saved_count
        }
