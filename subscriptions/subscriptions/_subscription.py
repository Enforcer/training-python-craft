from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from subscriptions.shared.sqlalchemy import Base, AsJSON
from subscriptions.shared.term import Term


@dataclass(frozen=True)
class PendingChange:
    new_plan_id: int


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    account_id: Mapped[int]
    tenant_id: Mapped[int]
    plan_id: Mapped[int]
    status: Mapped[str]
    subscribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    next_renewal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    term: Mapped[Term]
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pending_change: Mapped[PendingChange | None] = mapped_column(
        AsJSON[PendingChange], default=None
    )
