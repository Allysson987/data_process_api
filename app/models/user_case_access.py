
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.connection import Base


class UserCaseAccess(Base):
    __tablename__ = "user_case_access"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "case_id",
            name="uq_user_case_access",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    granted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    granted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    user = relationship(
        "User",
        back_populates="case_accesses",
        foreign_keys=[user_id],
    )

    case = relationship(
        "Case",
        back_populates="user_accesses",
    )

    granted_by_user = relationship(
        "User",
        foreign_keys=[granted_by],
    )
