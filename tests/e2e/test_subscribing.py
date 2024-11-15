from datetime import datetime, timedelta
from unittest.mock import patch, Mock, seal

import time_machine
from lagom import Container
from stripe import (
    CardError,
    CustomerService,
    SetupIntentService,
    PaymentMethodService,
    PaymentIntentService,
)

from subscriptions.api import jwt
from subscriptions.api.jwt import Payload
from fastapi.testclient import TestClient

from subscriptions.shared.term import Term
from subscriptions.subscriptions._app._facade import SubscriptionsFacade


def auth_header(tenant_id: int) -> str:
    payload = Payload(user_id=1, tenant_id=tenant_id, roles=["admin"])
    token = jwt.encode(payload)
    return f"JWT {token}"


def test_subscribing(client: TestClient, container: Container) -> None:
    headers = {"Authorization": auth_header(1)}

    client.post(
        "/plans",
        json={
            "name": "plan1",
            "price": {"amount": 10.0, "currency": "USD"},
            "description": "desc1",
        },
        headers=headers,
    )
    client.post(
        "/plans",
        json={
            "name": "plan2",
            "price": {"amount": 10.0, "currency": "USD"},
            "description": "desc1",
        },
        headers=headers,
    )
    client.post(
        "/plans",
        json={
            "name": "plan3",
            "price": {"amount": 20.0, "currency": "USD"},
            "description": "desc1",
        },
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
        ) as pay_mock:
            subscribe_response = client.post(
                "/subscriptions",
                json={
                    "account_id": account_id,
                    "plan_id": plans_response[1]["id"],
                    "term": Term.YEARLY,
                },
                headers=headers,
            )
            pay_mock.assert_called_once()
            pay_call_kwargs = pay_mock.mock_calls[0].kwargs["params"]
            assert pay_call_kwargs["amount"] == 12000
            assert pay_call_kwargs["currency"] == "usd"
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
                facade = container.resolve(SubscriptionsFacade)
                facade.renew_subscriptions()

    subscriptions = client.get(
        "/subscriptions", params={"account_id": account_id}, headers=headers
    ).json()
    assert len(subscriptions) == 1
    assert subscriptions[0]["plan_id"] == plans_response[1]["id"]
    assert subscriptions[0]["pending_change"] is None


def test_subscribing_to_add_ons_increases_price(client: TestClient) -> None:
    headers = {"Authorization": auth_header(1)}
    # Given: Plan with add-on
    add_plan_response = client.post(
        "/plans",
        json={
            "name": "plan_with_addon",
            "price": {"amount": 15.99, "currency": "USD"},
            "description": "desc1",
            "add_ons": [
                {
                    "name": "extra_screens",
                    "unit_price": {"amount": 9.99, "currency": "USD"},
                },
                {
                    "name": "quality_4k",
                    "flat_price": {"amount": 12.99, "currency": "USD"},
                },
                {
                    "name": "extra_members",
                    "tiers": {
                        1: {"amount": 9.99, "currency": "USD"},
                        3: {"amount": 19.99, "currency": "USD"},
                        5: {"amount": 30.99, "currency": "USD"},
                    },
                },
            ],
        },
        headers=headers,
    )
    assert add_plan_response.status_code == 200, add_plan_response.json()
    plan_id = add_plan_response.json()["id"]

    # Given: a customer account
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
        with patch.object(
            PaymentIntentService, "create", return_value=payment_intent_mock
        ) as pay_mock:
            subscribe_response = client.post(
                "/subscriptions",
                json={
                    "account_id": account_id,
                    "plan_id": plan_id,
                    "term": Term.MONTHLY,
                    "add_ons": [
                        {"name": "extra_screens", "quantity": 2},
                        {"name": "quality_4k", "quantity": 1},
                        {"name": "extra_members", "quantity": 5},
                    ],
                },
                headers=headers,
            )
            pay_mock.assert_called_once()
            pay_call_kwargs = pay_mock.mock_calls[0].kwargs["params"]
            assert pay_call_kwargs["amount"] == 7995
            assert pay_call_kwargs["currency"] == "usd"
    assert subscribe_response.status_code == 201
