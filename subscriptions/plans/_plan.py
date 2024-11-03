from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from subscriptions.plans._add_on import AddOn
from subscriptions.shared.money import MoneyType, Money
from subscriptions.shared.sqlalchemy import Base, AsJSON


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (UniqueConstraint("tenant_id", "name"),)

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    tenant_id: Mapped[int]
    name: Mapped[str]
    price: Mapped[Money] = mapped_column(MoneyType)
    description: Mapped[str]
    add_ons: Mapped[list[AddOn]] = mapped_column(AsJSON[list[AddOn]])
