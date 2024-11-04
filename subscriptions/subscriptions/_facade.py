from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from subscriptions.auth import requires_role, Subject
from subscriptions.payments import PaymentsFacade
from subscriptions.plans import PlansFacade, PlanId, RequestedAddOn
from subscriptions.shared.account_id import AccountId
from subscriptions.shared.tenant_id import TenantId
from subscriptions.shared.term import Term
from subscriptions.subscriptions._role_objects import (
    SubscriptionsViewer,
    SubscriptionsAdmin,
)
from subscriptions.subscriptions._subscription import Subscription
from subscriptions.subscriptions._subscription_dto import SubscriptionDto
from subscriptions.subscriptions._subscription_factory import build_new
from subscriptions.subscriptions._subscription_id import SubscriptionId


class SubscriptionsFacade:
    def __init__(
        self,
        session: Session,
        payments_facade: PaymentsFacade,
        plans_facade: PlansFacade,
    ) -> None:
        self._session = session
        self._payments_facade = payments_facade
        self._plans_facade = plans_facade

    @requires_role(SubscriptionsViewer)
    def subscriptions(
        self, subject: Subject, account_id: AccountId
    ) -> list[SubscriptionDto]:
        stmt = select(Subscription).filter(
            Subscription.account_id == account_id,
            Subscription.tenant_id == subject.tenant_id,
        )
        subscriptions = self._session.execute(stmt).scalars().all()
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
        self._session.add(subscription)
        self._session.commit()
        return SubscriptionDto.model_validate(subscription)

    def cancel(
        self,
        account_id: AccountId,
        tenant_id: TenantId,
        subscription_id: SubscriptionId,
    ) -> None:
        stmt = select(Subscription).filter(
            Subscription.account_id == account_id,
            Subscription.tenant_id == tenant_id,
            Subscription.id == subscription_id,
        )
        subscription = self._session.execute(stmt).scalars().one()
        subscription.cancel()
        self._session.commit()

    def change_plan(
        self,
        subject: Subject,
        account_id: AccountId,
        new_plan_id: PlanId,
        subscription_id: SubscriptionId,
    ) -> SubscriptionDto:
        stmt = select(Subscription).filter(
            Subscription.account_id == account_id,
            Subscription.tenant_id == subject.tenant_id,
            Subscription.id == subscription_id,
        )
        subscription = self._session.execute(stmt).scalars().one()
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
        now = datetime.now(timezone.utc)
        stmt = select(Subscription).filter(
            Subscription.next_renewal_at <= now,
            Subscription.status == "active",
        )
        subscriptions = self._session.execute(stmt).scalars().all()
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
