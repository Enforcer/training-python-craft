from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from subscriptions.shared.account_id import AccountId
from subscriptions.shared.tenant_id import TenantId
from subscriptions.subscriptions._subscription import Subscription
from subscriptions.subscriptions._subscription_id import SubscriptionId


class SubscriptionsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all(
        self, tenant_id: TenantId, account_id: AccountId
    ) -> Sequence[Subscription]:
        stmt = select(Subscription).filter(
            Subscription.account_id == account_id,
            Subscription.tenant_id == tenant_id,
        )
        return self._session.execute(stmt).scalars().all()

    def get_all_pending_renewal(self) -> Sequence[Subscription]:
        now = datetime.now(timezone.utc)
        stmt = select(Subscription).filter(
            Subscription.next_renewal_at <= now,
            Subscription.status == "active",
        )
        return self._session.execute(stmt).scalars().all()

    def add(self, subscription: Subscription) -> None:
        self._session.add(subscription)

    def get(
        self,
        tenant_id: TenantId,
        account_id: AccountId,
        subscription_id: SubscriptionId,
    ) -> Subscription:
        stmt = select(Subscription).filter(
            Subscription.account_id == account_id,
            Subscription.tenant_id == tenant_id,
            Subscription.id == subscription_id,
        )
        return self._session.execute(stmt).scalars().one()
