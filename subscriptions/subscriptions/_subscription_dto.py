from datetime import datetime

from pydantic import BaseModel, ConfigDict

from subscriptions.shared.term import Term


class PendingChangeDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    new_plan_id: int


class SubscriptionDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    status: str
    subscribed_at: datetime
    next_renewal_at: datetime | None
    term: Term
    canceled_at: datetime | None
    pending_change: PendingChangeDto | None
