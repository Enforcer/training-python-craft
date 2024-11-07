"""Assembling the application."""

from typing import NewType

from lagom import Container
from lagom.integrations.fast_api import FastApiIntegration

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from subscriptions.settings import PaymentsSettings

StripeApiKey = NewType("StripeApiKey", str)
StripePublishableKey = NewType("StripePublishableKey", str)


container = Container()
container[Engine] = create_engine(
    "postgresql://subscriptions:subscriptions@localhost/subscriptions", echo=True
)

SessionFactory = scoped_session(sessionmaker(bind=container[Engine]))

container[Session] = lambda: SessionFactory()

payments_settings = PaymentsSettings.model_validate({})

container[StripeApiKey] = StripeApiKey(payments_settings.STRIPE_API_KEY)
container[StripePublishableKey] = StripePublishableKey(
    payments_settings.STRIPE_PUBLISHABLE_KEY
)

deps = FastApiIntegration(container)
