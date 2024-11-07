from sqlalchemy.orm import Mapped, mapped_column

from subscriptions.shared.sqlalchemy import Base


class Customer(Base):
    __tablename__ = "customers"

    account_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    tenant_id: Mapped[int]
    stripe_customer_id: Mapped[str]
    stripe_setup_intent_id: Mapped[str]
