from hashlib import sha256
from typing import Iterator
from fastapi.testclient import TestClient
import pytest
from _pytest.fixtures import SubRequest
from kombu import Queue  # type: ignore[import-untyped]
from lagom import Container
from sqlalchemy import Engine, create_engine, text

from subscriptions.shared.mqlib import PoolFactory
from subscriptions.shared.sqlalchemy import Base
from subscriptions.main import container as main_container, SessionFactory
from subscriptions.api.app import app
from subscriptions.shared.mqlib.testing import purge as purge_queue


@pytest.fixture()
def setup_db(request: SubRequest) -> Iterator[None]:
    test_name = request.node.name
    db_name = f"test_{sha256(test_name.encode("utf-8")).hexdigest()[:50]}"
    engine = main_container[Engine]
    with engine.connect() as connection:
        connection.execution_options(isolation_level="AUTOCOMMIT")
        connection.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
        connection.execute(text(f"CREATE DATABASE {db_name}"))

    new_url = engine.url.set(database=db_name)

    test_engine = create_engine(new_url, echo=True)
    SessionFactory.configure(bind=test_engine)
    Base.metadata.create_all(test_engine)
    yield
    test_engine.dispose()
    SessionFactory.remove()


@pytest.fixture(scope="session", autouse=True)
def clean_rabbitmq() -> Iterator[None]:
    yield
    pool_factory = main_container.resolve(PoolFactory)
    purge_queue(pool_factory, Queue("payments-events"))


@pytest.fixture()
def client(setup_db: None, clean_rabbitmq: None) -> Iterator[TestClient]:
    # Assumption is that if someone is using api client
    # they'll need test DB
    with TestClient(app) as a_client:
        yield a_client


@pytest.fixture()
def container(setup_db: None) -> Container:
    # Assumption is that if someone is using container
    # they'll need test DB
    return main_container
