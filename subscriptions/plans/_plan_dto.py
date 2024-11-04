from typing import Annotated

from pydantic import BaseModel, ConfigDict

from subscriptions.plans._add_ons._flat_price_add_on import FlatPriceAddOn
from subscriptions.plans._add_ons._tiered_add_on import TieredAddOn
from subscriptions.plans._add_ons._unit_price_add_on import UnitPriceAddOn
from subscriptions.shared.money import MoneyAnnotation, Money


class PlanDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Annotated[Money, MoneyAnnotation]
    description: str
    add_ons: list[UnitPriceAddOn | FlatPriceAddOn | TieredAddOn]
