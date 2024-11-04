from dataclasses import dataclass
from typing import Annotated

from subscriptions.shared.money import Money, MoneyAnnotation


@dataclass(frozen=True)
class TieredAddOn:
    name: str
    tiers: dict[int, Annotated[Money, MoneyAnnotation]]