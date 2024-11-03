from sqlalchemy.orm import mapped_column, Mapped

from subscriptions.shared.money import Money, MoneyType
from subscriptions.shared.sqlalchemy import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    tenant_id: Mapped[int]
    account_id: Mapped[int]
    amount: Mapped[Money] = mapped_column(MoneyType)
    status: Mapped[str]
    stripe_payment_id: Mapped[str]
