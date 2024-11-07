from typing import assert_never

import stripe
from sqlalchemy import select
from sqlalchemy.orm import Session

from subscriptions.main import payments_settings
from subscriptions.payments._customer import Customer
from subscriptions.payments._payment import Payment
from subscriptions.payments._stripe_gateway import (
    StripeGateway,
    Success,
    Failure,
    NeedsAuthentication,
    NoPaymentMethods,
)
from subscriptions.shared.account_id import AccountId
from subscriptions.shared.money import Money


class ClientSecretUnavailable(ValueError):
    pass


class InternalError(Exception):
    pass


class PaymentsFacade:
    def __init__(self, session: Session, stripe_gateway: StripeGateway) -> None:
        self._session = session
        self._stripe_gateway = stripe_gateway
        # 👇 THIS should be removed 👇
        stripe_api_key = payments_settings.STRIPE_API_KEY
        self._client = stripe.StripeClient(api_key=stripe_api_key)
        # ...up to this point.

    def register_account(self, account_id: AccountId, tenant_id: int) -> None:
        stripe_customer = self._client.customers.create()
        setup_intent = self._client.setup_intents.create(
            params=dict(
                customer=stripe_customer.id,
                automatic_payment_methods={"enabled": True},
            )
        )
        customer = Customer(
            account_id=account_id,
            tenant_id=tenant_id,
            stripe_customer_id=stripe_customer.id,
            stripe_setup_intent_id=setup_intent.id,
        )
        self._session.add(customer)
        self._session.commit()

    def client_secret(self, account_id: AccountId) -> str:
        stmt = select(Customer).filter(Customer.account_id == account_id)
        customer = self._session.execute(stmt).scalars().one()
        setup_intent = self._client.setup_intents.retrieve(
            customer.stripe_setup_intent_id
        )
        if setup_intent.client_secret is None:
            raise ClientSecretUnavailable()
        return setup_intent.client_secret

    def charge(self, account_id: AccountId, amount: Money) -> bool:
        stmt = select(Customer).filter(Customer.account_id == account_id)
        customer = self._session.execute(stmt).scalars().one()
        result = self._stripe_gateway.charge_with_first_available_method(
            customer.stripe_customer_id, amount
        )
        match result:
            case Success():
                payment = Payment(
                    tenant_id=customer.tenant_id,
                    account_id=account_id,
                    amount=amount,
                    status="success",
                    stripe_payment_id=result.payment_intent_id,
                )
                self._session.add(payment)
                self._session.commit()
                return True
            case Failure():
                payment = Payment(
                    tenant_id=customer.tenant_id,
                    account_id=account_id,
                    amount=amount,
                    status="failure",
                    stripe_payment_id=result.payment_intent_id,
                )
                self._session.add(payment)
                self._session.commit()
                return False
            case NeedsAuthentication():
                pass  # no handling YET
                return False
            case NoPaymentMethods():
                raise Exception("No payment methods!")
            case _:
                assert_never(result)
