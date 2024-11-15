from typing import Annotated

from fastapi import Depends, APIRouter, Response
from pydantic import BaseModel, Field

from subscriptions.api import subject
from subscriptions.auth import Subject
from subscriptions.main import deps
from subscriptions.plans._domain._add_ons._flat_price_add_on import FlatPriceAddOn
from subscriptions.plans._domain._add_ons._tiered_add_on import TieredAddOn
from subscriptions.plans._domain._add_ons._unit_price_add_on import UnitPriceAddOn
from subscriptions.plans._app._plan_dto import PlanDto
from subscriptions.plans._app._facade import PlansFacade
from subscriptions.shared.money import MoneyAnnotation, Money

router = APIRouter()


class AddPlan(BaseModel):
    name: str
    price: Annotated[Money, MoneyAnnotation]
    description: str
    add_ons: list[UnitPriceAddOn | FlatPriceAddOn | TieredAddOn] = Field(
        default_factory=list
    )


@router.post("/plans")
def add_plan(
    payload: AddPlan,
    subject: Subject = Depends(subject),
    plans: PlansFacade = deps.depends(PlansFacade),
) -> PlanDto:
    return plans.add(
        subject,
        name=payload.name,
        price=payload.price,
        description=payload.description,
        add_ons=payload.add_ons,
    )


@router.get("/plans")
def get_plans(
    subject: Subject = Depends(subject),
    plans: PlansFacade = deps.depends(PlansFacade),
) -> list[PlanDto]:
    return plans.get_all(subject)


@router.delete("/plans/{plan_id}")
def delete_plan(
    plan_id: int,
    subject: Subject = Depends(subject),
    plans: PlansFacade = deps.depends(PlansFacade),
) -> Response:
    plans.delete(subject, plan_id)
    return Response(status_code=204)
