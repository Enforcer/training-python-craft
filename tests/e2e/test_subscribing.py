from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator
from unittest.mock import patch, Mock, seal

import pytest
import time_machine
from sqlalchemy import create_engine, text
from stripe import (
    CardError,
    CustomerService,
    SetupIntentService,
    PaymentMethodService,
    PaymentIntentService,
)

from subscriptions.api import jwt
from subscriptions.api.app import app
from subscriptions.api.jwt import Payload
from subscriptions.main import Session, engine
from fastapi.testclient import TestClient

from subscriptions.payments import PaymentsFacade
from subscriptions.plans import PlansFacade
from subscriptions.shared.sqlalchemy import Base
from subscriptions.shared.term import Term
from subscriptions.subscriptions._facade import SubscriptionsFacade


@pytest.fixture(autouse=True)
def setup_db(tmpdir: Path) -> None:
    with engine.connect() as connection:
        connection.execution_options(isolation_level="AUTOCOMMIT")
        connection.execute(text("DROP DATABASE IF EXISTS tests"))
        connection.execute(text("CREATE DATABASE tests"))

    new_url = engine.url.set(database="tests")

    test_engine = create_engine(new_url, echo=True)
    Session.configure(bind=test_engine)
    Base.metadata.create_all(test_engine)


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(app) as a_client:
        yield a_client


def auth_header(tenant_id: int) -> str:
    payload = Payload(user_id=1, tenant_id=tenant_id, roles=["admin"])
    token = jwt.encode(payload)
    return f"JWT {token}"


def test_subscribing(client: TestClient) -> None:
    headers = {"Authorization": auth_header(1)}

    client.post(
        "/plans",
        json={"name": "plan1", "price": 10.0, "description": "desc1"},
        headers=headers,
    )
    client.post(
        "/plans",
        json={"name": "plan2", "price": 10.0, "description": "desc1"},
        headers=headers,
    )
    client.post(
        "/plans",
        json={"name": "plan3", "price": 20.0, "description": "desc1"},
        headers=headers,
    )
    api_response = client.get("/plans", headers=headers)
    assert api_response.status_code == 200
    assert len(plans_response := api_response.json()) == 3

    client.delete(f"/plans/{plans_response[0]['id']}", headers=headers)
    api_response = client.get("/plans", headers=headers)
    assert api_response.status_code == 200
    assert len(api_response.json()) == 2

    stripe_customer_mock = Mock(id="cus_123")
    stripe_setup_intent_mock = Mock(id="si_123")
    seal(stripe_customer_mock)
    seal(stripe_setup_intent_mock)
    with patch.object(CustomerService, "create", return_value=stripe_customer_mock):
        with patch.object(
            SetupIntentService, "create", return_value=stripe_setup_intent_mock
        ):
            open_account_response = client.post("/accounts", headers=headers)
    assert open_account_response.status_code == 200
    account_id = open_account_response.json()["account_id"]

    methods_list_mock = Mock(data=[Mock(id="pm_123")])
    payment_intent_mock = Mock(id="pi_123")
    seal(methods_list_mock)
    with patch.object(PaymentMethodService, "list", return_value=methods_list_mock):
        exc = CardError("", "", "authentication_required")  # type: ignore
        exc.error = Mock(payment_intent={"id": "pi_122_failed"})
        with patch.object(PaymentIntentService, "create", side_effect=exc):
            subscribe_response = client.post(
                "/subscriptions",
                json={
                    "account_id": account_id,
                    "plan_id": plans_response[1]["id"],
                    "term": Term.YEARLY,
                },
                headers=headers,
            )
            assert subscribe_response.status_code == 500

        with patch.object(
            PaymentIntentService, "create", return_value=payment_intent_mock
        ):
            subscribe_response = client.post(
                "/subscriptions",
                json={
                    "account_id": account_id,
                    "plan_id": plans_response[1]["id"],
                    "term": Term.YEARLY,
                },
                headers=headers,
            )
    assert subscribe_response.status_code == 201

    api_response = client.get(
        "/subscriptions", params={"account_id": account_id}, headers=headers
    )
    assert api_response.status_code == 200
    assert len(subscriptions := api_response.json()) == 1

    subscription_id = subscriptions[0]["id"]
    # upgrade
    with patch.object(PaymentMethodService, "list", return_value=methods_list_mock):
        with patch.object(
            PaymentIntentService, "create", return_value=payment_intent_mock
        ):
            api_response = client.patch(
                f"/subscriptions/{subscription_id}",
                json={"new_plan_id": plans_response[2]["id"], "account_id": account_id},
                headers=headers,
            )

    subscription = api_response.json()
    assert subscription["plan_id"] == plans_response[2]["id"]
    assert subscription["pending_change"] is None

    api_response = client.patch(
        f"/subscriptions/{subscription_id}",
        json={"new_plan_id": plans_response[1]["id"], "account_id": account_id},
        headers=headers,
    )
    subscription = api_response.json()
    assert subscription["plan_id"] == plans_response[2]["id"]
    assert subscription["pending_change"] == {"new_plan_id": plans_response[1]["id"]}

    with patch.object(PaymentMethodService, "list", return_value=methods_list_mock):
        with patch.object(
            PaymentIntentService, "create", return_value=payment_intent_mock
        ):
            renewal_at = datetime.fromisoformat(
                subscription["next_renewal_at"]
            ) + timedelta(hours=3)
            with time_machine.travel(renewal_at):
                session = Session()
                facade = SubscriptionsFacade(
                    session, PaymentsFacade(session), PlansFacade(session)
                )
                facade.renew_subscriptions()

    subscriptions = client.get(
        "/subscriptions", params={"account_id": account_id}, headers=headers
    ).json()
    assert len(subscriptions) == 1
    assert subscriptions[0]["plan_id"] == plans_response[1]["id"]
    assert subscriptions[0]["pending_change"] is None
