from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Date,
    DateTime,
    Text
)

from app.database.connection import Base


class Diary(Base):

    __tablename__ = "diaries"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    source = Column(String(50))

    source_id = Column(String(100))

    publication_date = Column(Date)

    available_date = Column(Date)

    update_date = Column(DateTime)

    title = Column(String(255))

    content = Column(Text)

    pdf_url = Column(Text)