from typing import Annotated

from fastapi import Depends, APIRouter, Response
from pydantic import BaseModel

from subscriptions.api.multitenancy import extract_tenant_id
from subscriptions.main import Session
from subscriptions.plans._plan_dto import PlanDto
from subscriptions.plans._facade import PlansFacade
from subscriptions.shared.money import MoneyAnnotation, Money

router = APIRouter()


class AddPlan(BaseModel):
    name: str
    price: Annotated[Money, MoneyAnnotation]
    description: str


@router.post("/plans")
def add_plan(payload: AddPlan, tenant_id: int = Depends(extract_tenant_id)) -> PlanDto:
    session = Session()
    plans = PlansFacade(session=session)
    return plans.add(
        tenant_id,
        name=payload.name,
        price=payload.price,
        description=payload.description,
    )


@router.get("/plans")
def get_plans(tenant_id: int = Depends(extract_tenant_id)) -> list[PlanDto]:
    session = Session()
    plans = PlansFacade(session=session)
    return plans.get_all(tenant_id)


@router.delete("/plans/{plan_id}")
def delete_plan(plan_id: int, tenant_id: int = Depends(extract_tenant_id)) -> Response:
    session = Session()
    plans = PlansFacade(session=session)
    plans.delete(tenant_id, plan_id)
    return Response(status_code=204)
