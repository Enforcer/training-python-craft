from datetime import datetime, timezone
from unittest.mock import Mock, seal

import pytest
import time_machine
from dateutil.relativedelta import relativedelta
from lagom import Container

from subscriptions.auth import Subject
from subscriptions.payments import PaymentsFacade
from subscriptions.plans import PlansFacade, PlanId
from subscriptions.shared.account_id import AccountId
from subscriptions.shared.money import Money
from subscriptions.shared.tenant_id import TenantId
from subscriptions.shared.term import Term
from subscriptions.subscriptions import SubscriptionsAdmin, SubscriptionsViewer
from subscriptions.subscriptions._app._facade import SubscriptionsFacade
from subscriptions.subscriptions._app._subscription_dto import SubscriptionDto


@pytest.fixture()
def payments_facade() -> Mock:
    return Mock(spec_set=PaymentsFacade)


@pytest.fixture()
def plans_facade() -> Mock:
    return Mock(spec_set=PlansFacade)


@pytest.fixture()
def facade(
    container: Container, payments_facade: Mock, plans_facade: Mock
) -> SubscriptionsFacade:
    cloned_container = container.clone()
    # mock or stub?
    cloned_container[PaymentsFacade] = payments_facade
    # mock or stub?
    cloned_container[PlansFacade] = plans_facade
    return cloned_container.resolve(SubscriptionsFacade)


@pytest.mark.parametrize("cost", [Money(1, "USD"), Money(10, "USD")])
def test_triggers_payment_for_a_new_subscription_based_on_plans_response(
    cost: Money, facade: SubscriptionsFacade, plans_facade: Mock, payments_facade: Mock
) -> None:
    plans_facade.calculate_cost.return_value = cost
    seal(plans_facade)
    payments_facade.charge = Mock(return_value=True)
    seal(payments_facade)
    account_id = AccountId(1)

    facade.subscribe(
        subject=Mock(spec_set=Subject, tenant_id=TenantId(1)),
        account_id=account_id,
        plan_id=PlanId(1),
        term=Term.MONTHLY,
        add_ons=[],
    )

    payments_facade.charge.assert_called_once_with(account_id, cost)


def test_sets_inactive_status_for_subscription_which_payment_failed(
    facade: SubscriptionsFacade, plans_facade: Mock, payments_facade: Mock
) -> None:
    plans_facade.calculate_cost.return_value = Money(1, "USD")
    seal(plans_facade)

    payments_facade.charge = Mock(return_value=True)

    tenant_id = TenantId(1)
    account_id = AccountId(1)
    subject = Subject(tenant_id, [SubscriptionsAdmin(), SubscriptionsViewer()])
    subscriptions: list[SubscriptionDto] = []
    new_subscription = facade.subscribe(
        subject=subject,
        account_id=account_id,
        plan_id=PlanId(1),
        term=Term.MONTHLY,
        add_ons=[],
    )
    subscriptions.append(new_subscription)

    month_ago = datetime.now(timezone.utc) - relativedelta(months=1)
    with time_machine.travel(month_ago):
        for _ in range(2):
            subscriptions.append(
                facade.subscribe(
                    subject=subject,
                    account_id=account_id,
                    plan_id=PlanId(1),
                    term=Term.MONTHLY,
                    add_ons=[],
                )
            )

    payments_facade.charge.side_effect = [True, False]
    facade.renew_subscriptions()

    dtos = facade.subscriptions(subject, account_id)
    active_count = [dto.status for dto in dtos].count("active")
    inactive_count = [dto.status for dto in dtos].count("inactive")
    assert active_count == 2
    assert inactive_count == 1
