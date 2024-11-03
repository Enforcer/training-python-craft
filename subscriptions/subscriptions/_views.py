from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from subscriptions.api.multitenancy import extract_tenant_id
from subscriptions.main import Session
from subscriptions.payments import PaymentsFacade
from subscriptions.plans import PlansFacade, PlanId
from subscriptions.shared.account_id import AccountId
from subscriptions.shared.tenant_id import TenantId
from subscriptions.shared.term import Term
from subscriptions.subscriptions._facade import SubscriptionsFacade
from subscriptions.subscriptions._subscription_dto import SubscriptionDto
from subscriptions.subscriptions._subscription_id import SubscriptionId

router = APIRouter()


class Subscribe(BaseModel):
    account_id: int
    plan_id: int
    term: Term


@router.post("/subscriptions", status_code=201)
def subscribe(
    payload: Subscribe, tenant_id: int = Depends(extract_tenant_id)
) -> SubscriptionDto:
    session = Session()
    payments_facade = PaymentsFacade(session=session)
    plans_facade = PlansFacade(session=session)
    facade = SubscriptionsFacade(session, payments_facade, plans_facade)
    try:
        return facade.subscribe(
            account_id=AccountId(payload.account_id),
            tenant_id=TenantId(tenant_id),
            plan_id=PlanId(payload.plan_id),
            term=payload.term,
        )
    except Exception as e:
        raise HTTPException(status_code=500) from e


@router.get("/subscriptions")
def get_subscriptions(
    account_id: int, tenant_id: int = Depends(extract_tenant_id)
) -> list[SubscriptionDto]:
    session = Session()
    payments_facade = PaymentsFacade(session=session)
    plans_facade = PlansFacade(session=session)
    facade = SubscriptionsFacade(session, payments_facade, plans_facade)
    return facade.subscriptions(
        account_id=AccountId(account_id),
        tenant_id=TenantId(tenant_id),
    )


class ChangePlanPayload(BaseModel):
    account_id: int
    new_plan_id: int


@router.patch("/subscriptions/{subscription_id}")
def change_plan(
    subscription_id: int,
    payload: ChangePlanPayload,
    tenant_id: int = Depends(extract_tenant_id),
) -> SubscriptionDto:
    session = Session()
    payments_facade = PaymentsFacade(session=session)
    plans_facade = PlansFacade(session=session)
    facade = SubscriptionsFacade(session, payments_facade, plans_facade)
    return facade.change_plan(
        account_id=AccountId(payload.account_id),
        tenant_id=TenantId(tenant_id),
        subscription_id=SubscriptionId(subscription_id),
        new_plan_id=PlanId(payload.new_plan_id),
    )
