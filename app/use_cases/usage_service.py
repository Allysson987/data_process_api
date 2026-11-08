
from sqlalchemy.orm import Session

from app.models.usage_history import UsageHistory


def record_usage(
    db: Session,
    user_id,
    resource: str,
    action: str,
    resource_id: str | None = None,
    execution_time_ms: int | None = None,
    details: str | None = None,
):
    history = UsageHistory(
        user_id=user_id,
        resource=resource,
        action=action,
        resource_id=resource_id,
        execution_time_ms=execution_time_ms,
        details=details,
    )

    db.add(history)
    db.commit()

    return history
