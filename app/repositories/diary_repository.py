
from sqlalchemy.orm import Session

from app.models.models_diary import Diary


class DiaryRepository:

    def __init__(
        self,
        db: Session
    ):

        self.db = db

    def create(
        self,
        diary_data: dict
    ) -> Diary:

        diary = Diary(
            source=diary_data["source"],
            source_id=diary_data["source_id"],
            publication_date=diary_data["publication_date"],
            available_date=diary_data["available_date"],
            update_date=diary_data["update_date"],
            title=diary_data["title"],
            content=diary_data["content"],
            pdf_url=diary_data["pdf_url"]
        )

        self.db.add(diary)

        self.db.commit()

        self.db.refresh(diary)

        return diary
    def exists(
        self,
        source: str,
        source_id: str
    ) -> bool:

        return (
            self.db.query(Diary.id)
            .filter(
                Diary.source == source,
                Diary.source_id == source_id
            )
            .first()
            is not None
        )