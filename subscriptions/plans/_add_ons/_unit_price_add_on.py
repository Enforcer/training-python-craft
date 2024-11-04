from dataclasses import dataclass
from typing import Annotated

from subscriptions.shared.money import Money, MoneyAnnotation


@dataclass(frozen=True)
class UnitPriceAddOn:
    name: str
    unit_price: Annotated[Money, MoneyAnnotation]
