from dataclasses import dataclass
from typing import Annotated

from subscriptions.plans._domain._add_ons._invalid_tier_requested import (
    InvalidTierRequested,
)
from subscriptions.shared.money import Money, MoneyAnnotation


@dataclass(frozen=True)
class TieredAddOn:
    name: str
    tiers: dict[int, Annotated[Money, MoneyAnnotation]]

    def calculate_price(self, quantity: int) -> Money:
        try:
            return self.tiers[quantity]
        except KeyError:
            raise InvalidTierRequested(self.name, quantity, list(self.tiers.keys()))
