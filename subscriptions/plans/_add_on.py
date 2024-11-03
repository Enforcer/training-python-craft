from dataclasses import dataclass
from typing import Annotated

from subscriptions.shared.money import Money, MoneyAnnotation


@dataclass(frozen=True)
class AddOn:
    name: str
    unit_price: Annotated[Money, MoneyAnnotation]


@dataclass(frozen=True)
class RequestedAddOn:
    name: str
    quantity: int
