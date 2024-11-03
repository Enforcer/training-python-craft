"""Assembling the application."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from subscriptions.settings import PaymentsSettings

engine = create_engine(
    "postgresql://subscriptions:subscriptions@localhost/subscriptions", echo=True
)
Session = scoped_session(sessionmaker(bind=engine))

payments_settings = PaymentsSettings.model_validate({})
