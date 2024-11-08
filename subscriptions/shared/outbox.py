import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, select
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
    BATCH_SIZE = 100

    def __init__(self, session: Session, publisher: Publisher) -> None:
        self._session = session
        self._publisher = publisher

    def run_once(self) -> None:
        self._session.rollback()
        with self._session.begin():
            stmt = (
                select(OutboxEntry)
                .with_for_update(skip_locked=True)
                .filter(OutboxEntry.retries_left >= 0)
                .order_by(OutboxEntry.when_created)
                .limit(self.BATCH_SIZE)
            )
            entries = self._session.execute(stmt).scalars().all()
            for entry in entries:
                try:
                    self._publisher.publish(entry.queue, message=entry.data)
                except Exception:
                    entry.retries_left -= 1
                    logging.exception(
                        "Error while publishing OutboxEntry #%d", entry.id
                    )
                else:
                    self._session.delete(entry)

            self._session.commit()


class OutboxEntry(Base):
    __tablename__ = "outbox_entries"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    queue: Mapped[str]
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    retries_left: Mapped[int]
    when_created: Mapped[datetime] = mapped_column(DateTime(timezone=True))
