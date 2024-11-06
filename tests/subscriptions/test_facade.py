import pytest
from lagom import Container

from subscriptions.payments import PaymentsFacade
from subscriptions.plans import PlansFacade
from subscriptions.subscriptions._facade import SubscriptionsFacade


@pytest.fixture()
def facade(container: Container) -> SubscriptionsFacade:
    cloned_container = container.clone()
    # Replacing dependencies using container
    # stub or mock?
    cloned_container[PaymentsFacade] = object()  # type: ignore
    # stub or mock?
    cloned_container[PlansFacade] = object()  # type: ignore
    return cloned_container.resolve(SubscriptionsFacade)


def test_tbd(facade: SubscriptionsFacade) -> None:
    pass
