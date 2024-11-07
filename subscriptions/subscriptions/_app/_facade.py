from sqlalchemy.orm import Session

from subscriptions.auth import requires_role, Subject
from subscriptions.payments import PaymentsFacade
from subscriptions.plans import PlansFacade, PlanId, RequestedAddOn
from subscriptions.shared.account_id import AccountId
from subscriptions.shared.tenant_id import TenantId
from subscriptions.shared.term import Term
from subscriptions.subscriptions._app._repository import SubscriptionsRepository
from subscriptions.subscriptions._app._role_objects import (
    SubscriptionsViewer,
    SubscriptionsAdmin,
)
from subscriptions.subscriptions._app._subscription_dto import SubscriptionDto
from subscriptions.subscriptions._domain._subscription_factory import build_new
from subscriptions.subscriptions._domain._subscription_id import SubscriptionId


class SubscriptionsFacade:
    def __init__(
        self,
        session: Session,
        repository: SubscriptionsRepository,
        payments_facade: PaymentsFacade,
        plans_facade: PlansFacade,
    ) -> None:
        self._session = session
        self._repository = repository
        self._payments_facade = payments_facade
        self._plans_facade = plans_facade

    @requires_role(SubscriptionsViewer)
    def subscriptions(
        self, subject: Subject, account_id: AccountId
    ) -> list[SubscriptionDto]:
        subscriptions = self._repository.get_all(subject.tenant_id, account_id)
        return [SubscriptionDto.model_validate(sub) for sub in subscriptions]

    @requires_role(SubscriptionsAdmin)
    def subscribe(
        self,
        subject: Subject,
        account_id: AccountId,
        plan_id: PlanId,
        term: Term,
        add_ons: list[RequestedAddOn],
    ) -> SubscriptionDto:
        cost = self._plans_facade.calculate_cost(
            subject.tenant_id, plan_id, term, add_ons
        )
        charged = self._payments_facade.charge(account_id, cost)
        if not charged:
            raise Exception("Failed to charge!")

        subscription = build_new(account_id, subject.tenant_id, plan_id, term, add_ons)
        self._repository.add(subscription)
        self._session.commit()
        return SubscriptionDto.model_validate(subscription)

    @requires_role(SubscriptionsAdmin)
    def cancel(
        self,
        subject: Subject,
        account_id: AccountId,
        subscription_id: SubscriptionId,
    ) -> None:
        subscription = self._repository.get(
            subject.tenant_id, account_id, subscription_id
        )
        subscription.cancel()
        self._session.commit()

    @requires_role(SubscriptionsAdmin)
    def change_plan(
        self,
        subject: Subject,
        account_id: AccountId,
        new_plan_id: PlanId,
        subscription_id: SubscriptionId,
    ) -> SubscriptionDto:
        subscription = self._repository.get(
            subject.tenant_id, account_id, subscription_id
        )
        if subscription.plan_id == new_plan_id:
            raise Exception("Cannot change to the same plan!")

        old_plan_cost = self._plans_facade.calculate_cost(
            subject.tenant_id,
            PlanId(subscription.plan_id),
            subscription.term,
            subscription.requested_add_ons,
        )
        new_plan_cost = self._plans_facade.calculate_cost(
            subject.tenant_id,
            new_plan_id,
            subscription.term,
            subscription.requested_add_ons,
        )
        if new_plan_cost > old_plan_cost:
            # upgrade
            charged = self._payments_facade.charge(account_id, new_plan_cost)
            if not charged:
                raise Exception("Failed to charge!")

            subscription.upgrade(new_plan_id)
        else:
            # downgrade
            subscription.downgrade(new_plan_id)

        self._session.commit()
        return SubscriptionDto.model_validate(subscription)

    def renew_subscriptions(self) -> None:
        subscriptions = self._repository.get_all_pending_renewal()
        for subscription in subscriptions:
            renewal = subscription.get_renewal()

            cost = self._plans_facade.calculate_cost(
                TenantId(subscription.tenant_id),
                renewal.plan_id,
                renewal.term,
                renewal.requested_add_ons,
            )
            charged = self._payments_facade.charge(
                AccountId(subscription.account_id), cost
            )
            if charged:
                subscription.renewal_successful()
            else:
                subscription.renewal_failed()

        self._session.commit()
