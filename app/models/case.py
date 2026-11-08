
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    case_number = Column(String(50), unique=True, nullable=False)

    court = Column(String(255), nullable=True)
    case_class = Column(String(255), nullable=True)
    subject = Column(Text, nullable=True)

    is_sealed = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    is_public = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    last_update_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user_accesses = relationship(
        "UserCaseAccess",
        back_populates="case",
        cascade="all, delete-orphan",
    )
