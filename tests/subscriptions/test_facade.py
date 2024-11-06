from unittest.mock import Mock

import pytest
from lagom import Container

from subscriptions.payments import PaymentsFacade
from subscriptions.plans import PlansFacade
from subscriptions.subscriptions._facade import SubscriptionsFacade


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


def test_triggers_payment_for_a_new_subscription_based_on_plans_response(
    facade: SubscriptionsFacade,
) -> None:
    pass
