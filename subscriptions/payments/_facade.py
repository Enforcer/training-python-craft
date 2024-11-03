import stripe
from sqlalchemy import select
from sqlalchemy.orm import Session

from subscriptions.main import payments_settings
from subscriptions.payments._customer import Customer
from subscriptions.payments._payment import Payment
from subscriptions.shared.account_id import AccountId
from subscriptions.shared.money import Money


class ClientSecretUnavailable(ValueError):
    pass


class InternalError(Exception):
    pass


class PaymentsFacade:
    def __init__(self, session: Session) -> None:
        self._session = session
        stripe_api_key = payments_settings.STRIPE_API_KEY
        self._client = stripe.StripeClient(api_key=stripe_api_key)

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
        methods = self._client.payment_methods.list(
            params=dict(customer=customer.stripe_customer_id, type="card")
        )
        if not methods:
            raise Exception("No payment methods available")

        selected_method_id = methods.data[0].id
        try:
            payment_intent = self._client.payment_intents.create(
                params=dict(
                    amount=int(amount.amount * 100),
                    currency=amount.currency.lower(),
                    automatic_payment_methods={"enabled": True},
                    customer=customer.stripe_customer_id,
                    payment_method=selected_method_id,
                    off_session=True,
                    confirm=True,
                )
            )
            payment = Payment(
                tenant_id=customer.tenant_id,
                account_id=account_id,
                amount=amount,
                status="success",
                stripe_payment_id=payment_intent.id,
            )
            self._session.add(payment)
            self._session.commit()
            return True
        except stripe.CardError as exc:
            error_object = exc.error
            if error_object is None:
                raise InternalError("Payment failed and no details are not available")
            # `error_object.code` will be "authentication_required"
            # if authentication is needed
            if error_object.payment_intent is None:
                raise InternalError("Payment failed and no payment intent is available")

            payment_intent_id = error_object.payment_intent["id"]
            payment = Payment(
                tenant_id=customer.tenant_id,
                account_id=account_id,
                amount=amount,
                status="failure",
                stripe_payment_id=payment_intent_id,
            )
            self._session.add(payment)
            self._session.commit()
            return False
