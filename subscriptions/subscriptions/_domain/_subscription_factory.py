from datetime import timezone, datetime

from subscriptions.plans import RequestedAddOn, PlanId
from subscriptions.shared.account_id import AccountId
from subscriptions.shared.tenant_id import TenantId
from subscriptions.shared.term import Term
from subscriptions.subscriptions._domain._renewal_calculation import (
    calculate_next_renewal,
)
from subscriptions.subscriptions._domain._subscription import Subscription


def build_new(
    account_id: AccountId,
    tenant_id: TenantId,
    plan_id: PlanId,
    term: Term,
    requested_add_ons: list[RequestedAddOn],
) -> Subscription:
    now = datetime.now(timezone.utc)
    next_renewal_at = calculate_next_renewal(now, term)
    return Subscription(
        account_id=account_id,
        tenant_id=tenant_id,
        plan_id=plan_id,
        status="active",
        subscribed_at=now,
        next_renewal_at=next_renewal_at,
        term=term,
        canceled_at=None,
        requested_add_ons=requested_add_ons,
    )
