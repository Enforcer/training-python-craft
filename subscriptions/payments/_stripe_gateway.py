import stripe

from subscriptions.main import StripeApiKey


class StripeGateway:
    def __init__(self, stripe_api_key: StripeApiKey) -> None:
        self._client = stripe.StripeClient(api_key=stripe_api_key)
