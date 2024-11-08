from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column, Mapped, Session

from subscriptions.shared.mqlib import Publisher
from subscriptions.shared.sqlalchemy import Base


class Outbox:
    def __init__(self, session: Session) -> None:
        self._session = session

    def put(self, queue_name: str, message: dict[str, Any]) -> None:
        self._session.add(
            OutboxEntry(
                queue=queue_name,
                data=message,
                retries_left=3,
                when_created=datetime.now(timezone.utc),
            )
        )


class OutboxProcessor:
    def __init__(self, session: Session, publisher: Publisher) -> None:
        self._session = session
        self._publisher = publisher

    def run_once(self) -> None:
        with self._session.begin():
            pass


class OutboxEntry(Base):
    __tablename__ = "outbox_entries"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    queue: Mapped[str]
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    retries_left: Mapped[int]
    when_created: Mapped[datetime] = mapped_column(DateTime(timezone=True))
