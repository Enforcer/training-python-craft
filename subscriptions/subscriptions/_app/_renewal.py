from sqlalchemy.orm import Session

from subscriptions.payments import PaymentsFacade
from subscriptions.plans import PlansFacade
from subscriptions.shared.account_id import AccountId
from subscriptions.shared.tenant_id import TenantId
from subscriptions.subscriptions._app._repository import SubscriptionsRepository
from subscriptions.subscriptions._domain._subscription_id import SubscriptionId


class RenewalService:
    def __init__(
        self,
        plans_facade: PlansFacade,
        payments_facade: PaymentsFacade,
        repository: SubscriptionsRepository,
        session: Session,
    ) -> None:
        self._plans_facade = plans_facade
        self._payments_facade = payments_facade
        self._repository = repository
        self._session = session

    def calculate_cost_and_charge(self, subscription_id: SubscriptionId) -> bool:
        subscription = self._repository.get_by_id(subscription_id)
        renewal = subscription.get_renewal()

        cost = self._plans_facade.calculate_cost(
            TenantId(subscription.tenant_id),
            renewal.plan_id,
            renewal.term,
            renewal.requested_add_ons,
        )
        return self._payments_facade.charge(
            account_id=AccountId(subscription.account_id),
            amount=cost,
        )

    def renew_successful(self, subscription_id: SubscriptionId) -> None:
        subscription = self._repository.get_by_id(subscription_id)
        subscription.renewal_successful()
        self._session.commit()

    def renew_failed(self, subscription_id: SubscriptionId) -> None:
        subscription = self._repository.get_by_id(subscription_id)
        subscription.renewal_failed()
        self._session.commit()
