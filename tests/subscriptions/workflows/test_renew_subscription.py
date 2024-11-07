from datetime import datetime, timezone
from typing import AsyncIterator, Callable
from unittest.mock import patch

import pytest
import pytest_asyncio
import time_machine
from dateutil.relativedelta import relativedelta
from lagom import Container
from temporalio.client import Client
from temporalio.worker import Worker

from subscriptions.accounts import AccountsAdmin
from subscriptions.auth import Subject
from subscriptions.payments import PaymentsFacade
from subscriptions.plans import PlansFacade, PlansViewer, PlansAdmin, PlanId, PlanDto
from subscriptions.shared.account_id import AccountId
from subscriptions.shared.money import Money
from subscriptions.shared.tenant_id import TenantId
from subscriptions.shared.term import Term
from subscriptions.subscriptions import (
    activities,
    SubscriptionsViewer,
    SubscriptionsAdmin,
)
from subscriptions.subscriptions._app._facade import SubscriptionsFacade
from subscriptions.workflows.subscriptions import renewal

pytestmark = [pytest.mark.usefixtures("setup_db")]


@pytest_asyncio.fixture()
async def client() -> Client:
    return await Client.connect("localhost:7233", namespace="default")


@pytest_asyncio.fixture()
async def worker(client: Client) -> AsyncIterator[None]:
    async with Worker(
        client,
        task_queue="test-queue",
        workflows=[renewal.RenewSubscriptionWorkflow],
        activities=[
            activities.charge_for_renewal,
            activities.mark_as_success,
            activities.mark_as_failure,
        ],
    ):
        yield


@pytest.fixture()
def subject() -> Subject:
    return Subject(
        tenant_id=TenantId(1),
        roles=[
            PlansViewer(),
            PlansAdmin(),
            SubscriptionsViewer(),
            SubscriptionsAdmin(),
            AccountsAdmin(),
        ],
    )


@pytest.fixture()
def plan_factory(subject: Subject, container: Container) -> Callable[[], PlanDto]:
    def _factory() -> PlanDto:
        plans = container.resolve(PlansFacade)
        return plans.add(
            subject=subject,
            name="plan",
            description="",
            price=Money(1, "USD"),
            add_ons=[],
        )

    return _factory


@pytest.mark.asyncio
@pytest.mark.usefixtures("worker")
async def test_hello_world(
    client: Client,
    container: Container,
    subject: Subject,
    plan_factory: Callable[[], PlanDto],
) -> None:
    account_id = AccountId(1)
    plan = plan_factory()
    subscriptions = container.resolve(SubscriptionsFacade)

    with patch.object(PaymentsFacade, "charge", return_value=True):
        month_ago = datetime.now(timezone.utc) - relativedelta(months=1)
        with time_machine.travel(month_ago):
            subscription_before = subscriptions.subscribe(
                subject=subject,
                account_id=account_id,
                plan_id=PlanId(plan.id),
                term=Term.MONTHLY,
                add_ons=[],
            )

        await client.execute_workflow(
            renewal.RenewSubscriptionWorkflow.run,
            subscription_before.id,
            id="example_id",
            task_queue="test-queue",
        )

    subscriptions_after = subscriptions.subscriptions(subject, account_id)
    assert len(subscriptions_after) == 1
    subscription_after = subscriptions_after[0]
    assert subscription_before.next_renewal_at is not None
    assert subscription_after.next_renewal_at is not None
    assert subscription_after.next_renewal_at > subscription_before.next_renewal_at
