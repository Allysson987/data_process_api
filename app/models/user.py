
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


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    name = Column(String(255), nullable=False)
    email_hash = Column(String(64), unique=True, nullable=False)
    email_encrypted = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=False)

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    is_admin = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

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

    case_accesses = relationship(
        "UserCaseAccess",
        back_populates="user",
        foreign_keys="UserCaseAccess.user_id",
        cascade="all, delete-orphan",
    )

    access_logs = relationship(
        "AccessLog",
        back_populates="user",
    )

    usage_history = relationship(
        "UsageHistory",
        back_populates="user",
    )
