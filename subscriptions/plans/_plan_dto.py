from typing import Annotated

from pydantic import BaseModel, ConfigDict

from subscriptions.plans._add_on import AddOn
from subscriptions.shared.money import MoneyAnnotation, Money


class PlanDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Annotated[Money, MoneyAnnotation]
    description: str
    add_ons: list[AddOn]
