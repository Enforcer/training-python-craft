from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


from subscriptions.plans._add_ons._flat_price_add_on import FlatPriceAddOn
from subscriptions.plans._add_ons._not_found import RequestedAddOnNotFound
from subscriptions.plans._add_ons._requested_add_on import RequestedAddOn
from subscriptions.plans._add_ons._tiered_add_on import TieredAddOn
from subscriptions.plans._add_ons._unit_price_add_on import UnitPriceAddOn
from subscriptions.shared.money import MoneyType, Money
from subscriptions.shared.sqlalchemy import Base, AsJSON
from subscriptions.shared.term import Term


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (UniqueConstraint("tenant_id", "name"),)

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    tenant_id: Mapped[int]
    name: Mapped[str]
    price: Mapped[Money] = mapped_column(MoneyType)
    description: Mapped[str]
    add_ons: Mapped[list[UnitPriceAddOn | FlatPriceAddOn | TieredAddOn]] = (
        mapped_column(AsJSON[list[UnitPriceAddOn | FlatPriceAddOn | TieredAddOn]])
    )

    def calculate_cost(self, term: Term, add_ons: list[RequestedAddOn]) -> Money:
        price = self.price

        for requested_add_on in add_ons:
            corresponding_add_on = self._add_on_named(requested_add_on.name)
            if corresponding_add_on is None:
                raise RequestedAddOnNotFound(requested_add_on.name)
            price += corresponding_add_on.calculate_price(requested_add_on.quantity)

        multiplier = 1 if term == Term.MONTHLY else 12
        return price * multiplier

    def _add_on_named(
        self, name: str
    ) -> UnitPriceAddOn | FlatPriceAddOn | TieredAddOn | None:
        return next((add_on for add_on in self.add_ons if add_on.name == name), None)
