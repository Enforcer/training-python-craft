from dataclasses import dataclass

import stripe

from subscriptions.main import StripeApiKey
from subscriptions.shared.money import Money


class InternalError(Exception):
    pass


@dataclass(frozen=True)
class Success:
    payment_intent_id: str


@dataclass(frozen=True)
class NeedsAuthentication:
    payment_intent_id: str


@dataclass(frozen=True)
class Failure:
    payment_intent_id: str


@dataclass(frozen=True)
class NoPaymentMethods:
    pass


class StripeGateway:
    def __init__(self, stripe_api_key: StripeApiKey) -> None:
        self._client = stripe.StripeClient(api_key=stripe_api_key)

    def charge_with_first_available_method(
        self, customer_id: str, amount: Money
    ) -> Success | Failure | NeedsAuthentication | NoPaymentMethods:
        methods = self._client.payment_methods.list(
            params=dict(customer=customer_id, type="card")
        )
        if not methods:
            return NoPaymentMethods()

        selected_method_id = methods.data[0].id
        try:
            payment_intent = self._client.payment_intents.create(
                params=dict(
                    amount=int(amount.amount * 100),
                    currency=amount.currency.lower(),
                    automatic_payment_methods={"enabled": True},
                    customer=customer_id,
                    payment_method=selected_method_id,
                    off_session=True,
                    confirm=True,
                )
            )
            return Success(payment_intent.id)
        except stripe.CardError as exc:
            error_object = exc.error
            if error_object is None:
                raise InternalError("Payment failed and no details are not available")

            if error_object.payment_intent is None:
                raise InternalError("Payment failed and no payment intent is available")

            payment_intent_id = error_object.payment_intent["id"]

            if error_object.code == "authentication_required":
                return NeedsAuthentication(payment_intent_id)

            return Failure(payment_intent_id)
