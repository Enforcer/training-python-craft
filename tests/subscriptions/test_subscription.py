from datetime import timezone, datetime

import pytest
from dateutil.relativedelta import relativedelta

from subscriptions.shared.term import Term
from subscriptions.subscriptions._subscription import Subscription


@pytest.fixture()
def subscription() -> Subscription:
    now = datetime.now(timezone.utc)
    month_from_now = now + relativedelta(months=1)
    return Subscription(
        account_id=1,
        tenant_id=1,
        plan_id=1,
        status="active",
        subscribed_at=datetime.now(timezone.utc),
        next_renewal_at=month_from_now,
        term=Term.MONTHLY,
        canceled_at=None,
    )


def test_cancelling_subscription_changes_status(subscription: Subscription) -> None:
    subscription.cancel()

    assert subscription.status == "canceled"
    assert subscription.canceled_at is not None


def test_cancelling_canceled_subscription_changes_nothing(
    subscription: Subscription,
) -> None:
    subscription.cancel()
    canceled_at = subscription.canceled_at

    subscription.cancel()

    assert subscription.status == "canceled"
    assert subscription.canceled_at == canceled_at
