from typing import assert_never

from sqlalchemy import select
from sqlalchemy.orm import Session

from subscriptions.payments._domain._customer import Customer
from subscriptions.payments._domain._payment import Payment
from subscriptions.payments._app._stripe_gateway import (
    StripeGateway,
    Success,
    Failure,
    NeedsAuthentication,
    NoPaymentMethods,
)
from subscriptions.shared.account_id import AccountId
from subscriptions.shared.money import Money


class InternalError(Exception):
    pass


class PaymentsFacade:
    def __init__(self, session: Session, stripe_gateway: StripeGateway) -> None:
        self._session = session
        self._stripe_gateway = stripe_gateway

    def register_account(self, account_id: AccountId, tenant_id: int) -> None:
        customer_id, setup_intent_id = self._stripe_gateway.setup_new_customer()
        customer = Customer(
            account_id=account_id,
            tenant_id=tenant_id,
            stripe_customer_id=customer_id,
            stripe_setup_intent_id=setup_intent_id,
        )
        self._session.add(customer)
        self._session.commit()

    def client_secret(self, account_id: AccountId) -> str:
        stmt = select(Customer).filter(Customer.account_id == account_id)
        customer = self._session.execute(stmt).scalars().one()
        return self._stripe_gateway.get_client_secret(customer.stripe_setup_intent_id)

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
