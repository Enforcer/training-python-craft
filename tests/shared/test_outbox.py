from unittest.mock import patch

from lagom import Container

import pytest
from sqlalchemy.orm import Session

from subscriptions.shared.mqlib import Publisher
from subscriptions.shared.outbox import Outbox, OutboxProcessor


@pytest.fixture()
def session(container: Container) -> Session:
    return container.resolve(Session)


@pytest.fixture()
def outbox(container: Container) -> Outbox:
    return container.resolve(Outbox)


@pytest.fixture()
def outbox_processor(container: Container) -> OutboxProcessor:
    return container.resolve(OutboxProcessor)


def test_processes_messages(
    outbox: Outbox, session: Session, outbox_processor: OutboxProcessor
) -> None:
    outbox.put(queue_name="test", message={"hello": "world"})
    session.commit()

    with patch.object(Publisher, "publish") as publish_mock:
        outbox_processor.run_once()

    publish_mock.assert_called_once_with(
        "test", message={"hello": "world"}
    )
