"""Mini-library wrapping kombu to provide simple API for sending messages."""

import threading
from typing import Protocol, TypedDict, NewType, Any

from kombu import Connection, Queue  # type: ignore[import-untyped]
from kombu.connection import ConnectionPool  # type: ignore[import-untyped]
from kombu.pools import connections  # type: ignore[import-untyped]


BrokerUrl = NewType("BrokerUrl", str)


class PoolFactory:
    def __init__(self, broker_url: BrokerUrl) -> None:
        self._pool: ConnectionPool | None = None
        self._lock = threading.Lock()
        self._broker_url = broker_url

    def get(self) -> ConnectionPool:
        with self._lock:
            if self._pool is not None:
                return self._pool

            connection = Connection(
                self._broker_url, transport_options={"confirm_publish": True}
            )
            self._pool = connections[connection]
            return self._pool


ANONYMOUS_EXCHANGE = ""


class Publisher:
    def __init__(self, pool_factory: PoolFactory) -> None:
        self._pool_factory = pool_factory

    def publish(
        self,
        queue_name_or_queue: str | Queue,
        message: dict[str, Any],
        headers: dict[str, str] | None = None,
        exchange: str = ANONYMOUS_EXCHANGE,
    ) -> None:
        headers = headers or {}
        if isinstance(queue_name_or_queue, Queue):
            queue = queue_name_or_queue.name
        else:
            queue = queue_name_or_queue

        with self._pool_factory.get().acquire(block=True) as conn:
            Queue(name=queue)(conn).declare()
            producer = conn.Producer(serializer="json", auto_declare=True)
            producer.publish(
                message,
                exchange=exchange,
                routing_key=queue,
                headers=headers,
            )


class DeliveryInfo(TypedDict):
    consumer_tag: str
    delivery_tag: int
    redelivered: bool
    exchange: str
    routing_key: str


class Message(Protocol):
    headers: dict[str, str]
    properties: dict[str, str]
    delivery_info: DeliveryInfo
    acknowledged: bool

    def ack(self) -> None: ...

    def reject(self) -> None: ...
