
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.connection import Base


class UsageHistory(Base):
    __tablename__ = "usage_history"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    resource = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)

    resource_id = Column(String(100), nullable=True)

    execution_time_ms = Column(Integer, nullable=True)

    details = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user = relationship(
        "User",
        back_populates="usage_history",
    )
