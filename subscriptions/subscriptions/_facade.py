from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from subscriptions.payments import PaymentsFacade
from subscriptions.plans import PlansFacade, PlanId, RequestedAddOn
from subscriptions.shared.account_id import AccountId
from subscriptions.shared.tenant_id import TenantId
from subscriptions.shared.term import Term
from subscriptions.subscriptions._subscription import Subscription, PendingChange
from subscriptions.subscriptions._subscription_dto import SubscriptionDto
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

    def subscriptions(
        self, account_id: AccountId, tenant_id: TenantId
    ) -> list[SubscriptionDto]:
        stmt = select(Subscription).filter(
            Subscription.account_id == account_id,
            Subscription.tenant_id == tenant_id,
        )
        subscriptions = self._session.execute(stmt).scalars().all()
        return [SubscriptionDto.model_validate(sub) for sub in subscriptions]

    def subscribe(
        self,
        account_id: AccountId,
        tenant_id: TenantId,
        plan_id: PlanId,
        term: Term,
        add_ons: list[RequestedAddOn],
    ) -> SubscriptionDto:
        cost = self._plans_facade.calculate_cost(tenant_id, plan_id, term, add_ons)
        charged = self._payments_facade.charge(account_id, cost)
        if not charged:
            raise Exception("Failed to charge!")

        now = datetime.now(timezone.utc)
        next_renewal_delta = (
            relativedelta(months=1) if term == Term.MONTHLY else relativedelta(years=1)
        )
        next_renewal_at = now + next_renewal_delta
        subscription = Subscription(
            account_id=account_id,
            tenant_id=tenant_id,
            plan_id=plan_id,
            status="active",
            subscribed_at=now,
            next_renewal_at=next_renewal_at,
            term=term,
            canceled_at=None,
            requested_add_ons=add_ons,
        )
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
        subscription.status = "canceled"
        subscription.canceled_at = datetime.now(timezone.utc)
        self._session.commit()

    def change_plan(
        self,
        account_id: AccountId,
        tenant_id: TenantId,
        new_plan_id: PlanId,
        subscription_id: SubscriptionId,
    ) -> SubscriptionDto:
        stmt = select(Subscription).filter(
            Subscription.account_id == account_id,
            Subscription.tenant_id == tenant_id,
            Subscription.id == subscription_id,
        )
        subscription = self._session.execute(stmt).scalars().one()
        if subscription.plan_id == new_plan_id:
            raise Exception("Cannot change to the same plan!")

        old_plan_cost = self._plans_facade.calculate_cost(
            tenant_id,
            PlanId(subscription.plan_id),
            subscription.term,
            subscription.requested_add_ons,
        )
        new_plan_cost = self._plans_facade.calculate_cost(
            tenant_id,
            new_plan_id,
            subscription.term,
            subscription.requested_add_ons,
        )
        if new_plan_cost > old_plan_cost:
            # upgrade
            charged = self._payments_facade.charge(account_id, new_plan_cost)
            if not charged:
                raise Exception("Failed to charge!")

            subscription.plan_id = new_plan_id
            now = datetime.now(timezone.utc)
            subscription.subscribed_at = now
            next_renewal_delta = (
                relativedelta(months=1)
                if subscription.term == Term.MONTHLY
                else relativedelta(years=1)
            )
            next_renewal_at = now + next_renewal_delta
            subscription.next_renewal_at = next_renewal_at
        else:
            # downgrade
            subscription.pending_change = PendingChange(new_plan_id=new_plan_id)

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
            if subscription.pending_change is not None:
                plan_id = PlanId(subscription.pending_change.new_plan_id)
                subscription.plan_id = subscription.pending_change.new_plan_id
                subscription.pending_change = None
            else:
                plan_id = PlanId(subscription.plan_id)

            cost = self._plans_facade.calculate_cost(
                TenantId(subscription.tenant_id),
                plan_id,
                subscription.term,
                subscription.requested_add_ons,
            )
            charged = self._payments_facade.charge(
                AccountId(subscription.account_id), cost
            )
            if not charged:
                subscription.status = "inactive"
            else:
                next_renewal_delta = (
                    relativedelta(months=1)
                    if subscription.term == Term.MONTHLY
                    else relativedelta(years=1)
                )
                subscription.next_renewal_at = now + next_renewal_delta

        self._session.commit()
