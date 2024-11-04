from dataclasses import dataclass
from typing import Annotated

from subscriptions.shared.money import Money, MoneyAnnotation


@dataclass(frozen=True)
class FlatPriceAddOn:
    name: str
    flat_price: Annotated[Money, MoneyAnnotation]
