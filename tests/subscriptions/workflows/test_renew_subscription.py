from typing import AsyncIterator

import pytest
import pytest_asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner

from subscriptions.workflows.subscriptions import renewal


@pytest_asyncio.fixture()
async def client() -> Client:
    return await Client.connect("localhost:7233", namespace="default")


@pytest_asyncio.fixture()
async def worker(client: Client) -> AsyncIterator[None]:
    async with Worker(
        client,
        task_queue="test-queue",
        workflows=[renewal.RenewSubscriptionWorkflow],
        activities=[renewal.hello_world],
        workflow_runner=SandboxedWorkflowRunner(),
    ):
        yield


@pytest.mark.asyncio
@pytest.mark.usefixtures("worker")
async def test_hello_world(client: Client) -> None:
    result = await client.execute_workflow(
        renewal.RenewSubscriptionWorkflow.run,
        "World",
        id="example_id",
        task_queue="test-queue",
    )

    assert result == "Hello, World!"
