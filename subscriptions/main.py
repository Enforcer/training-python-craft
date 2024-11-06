"""Assembling the application."""

from lagom import Container
from lagom.integrations.fast_api import FastApiIntegration

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from subscriptions.settings import PaymentsSettings

container = Container()
container[Engine] = create_engine(
    "postgresql://subscriptions:subscriptions@localhost/subscriptions", echo=True
)

SessionFactory = scoped_session(sessionmaker(bind=container[Engine]))

container[Session] = lambda: SessionFactory()

payments_settings = PaymentsSettings.model_validate({})

deps = FastApiIntegration(container)
# How to use in FastAPI?
# from subscriptions.main import deps
#
# Use like
# @router.post("/subscriptions", status_code=201)
# def subscribe(
#     ...,
#     # ! facade is injected by Lagom
#     facade: SubscriptionsFacade = deps.depends(SubscriptionsFacade),
# ) -> SubscriptionDto:
