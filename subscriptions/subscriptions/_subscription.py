from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from subscriptions.plans import RequestedAddOn, PlanId
from subscriptions.shared.sqlalchemy import Base, AsJSON
from subscriptions.shared.term import Term
from subscriptions.subscriptions._renewal_calculation import calculate_next_renewal


@dataclass(frozen=True)
class PendingChange:
    new_plan_id: int


@dataclass(frozen=True)
class Renewal:
    plan_id: PlanId
    term: Term
    requested_add_ons: list[RequestedAddOn]


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
    requested_add_ons: Mapped[list[RequestedAddOn]] = mapped_column(
        AsJSON[list[RequestedAddOn]], default_factory=list
    )

    def cancel(self) -> None:
        if self.status == "canceled":
            return

        self.status = "canceled"
        self.canceled_at = datetime.now(timezone.utc)

    def get_renewal(self) -> Renewal:
        if self.pending_change is not None:
            plan_id = PlanId(self.pending_change.new_plan_id)
        else:
            plan_id = PlanId(self.plan_id)

        return Renewal(
            plan_id,
            self.term,
            self.requested_add_ons,
        )

    def renewal_failed(self) -> None:
        self.status = "inactive"

    def renewal_successful(self) -> None:
        now = datetime.now(timezone.utc)
        self.next_renewal_at = calculate_next_renewal(now, self.term)
        if self.pending_change is not None:
            self.plan_id = self.pending_change.new_plan_id
            self.pending_change = None

    def upgrade(self, new_plan_id: PlanId) -> None:
        self.plan_id = int(new_plan_id)
        now = datetime.now(timezone.utc)
        self.subscribed_at = now
        next_renewal_at = calculate_next_renewal(now, self.term)
        self.next_renewal_at = next_renewal_at

    def downgrade(self, new_plan_id: PlanId) -> None:
        self.pending_change = PendingChange(new_plan_id=new_plan_id)
