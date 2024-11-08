from typing import Any, cast

from subscriptions.shared.mqlib import _mqlib as mqlib
from kombu import Queue  # type: ignore[import-untyped]


def purge(pool_factory: mqlib.PoolFactory, queue: Queue) -> None:
    with pool_factory.get().acquire(block=True) as conn:
        queue(conn).purge()


def next_message(
    pool_factory: mqlib.PoolFactory, queue: Queue, timeout: int = 5
) -> dict[str, Any]:
    with pool_factory.get().acquire(block=True) as conn:
        messages = []
        with conn.Consumer(
            queue, callbacks=[lambda body, message: messages.append((body, message))]
        ):
            conn.drain_events(timeout=timeout)

        body, message = messages[0]
        message.ack()  # To remove from queue
        return cast(dict[str, Any], body)
