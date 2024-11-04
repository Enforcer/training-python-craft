from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from subscriptions.api.multitenancy import subject
from subscriptions.auth import Subject
from subscriptions.main import Session
from subscriptions.payments import PaymentsFacade
from subscriptions.plans import PlansFacade, PlanId, RequestedAddOn
from subscriptions.plans._repository import PlansRepository
from subscriptions.shared.account_id import AccountId
from subscriptions.shared.term import Term
from subscriptions.subscriptions._facade import SubscriptionsFacade
from subscriptions.subscriptions._subscription_dto import SubscriptionDto
from subscriptions.subscriptions._subscription_id import SubscriptionId

router = APIRouter()


class Subscribe(BaseModel):
    account_id: int
    plan_id: int
    term: Term
    add_ons: list[RequestedAddOn] = Field(default_factory=list)


@router.post("/subscriptions", status_code=201)
def subscribe(
    payload: Subscribe, subject: Subject = Depends(subject)
) -> SubscriptionDto:
    session = Session()
    payments_facade = PaymentsFacade(session=session)
    plans_facade = PlansFacade(session=session, repository=PlansRepository(session))
    facade = SubscriptionsFacade(session, payments_facade, plans_facade)
    try:
        return facade.subscribe(
            subject=subject,
            account_id=AccountId(payload.account_id),
            plan_id=PlanId(payload.plan_id),
            term=payload.term,
            add_ons=payload.add_ons,
        )
    except Exception as e:
        raise HTTPException(status_code=500) from e


@router.get("/subscriptions")
def get_subscriptions(
    account_id: int, subject: Subject = Depends(subject)
) -> list[SubscriptionDto]:
    session = Session()
    payments_facade = PaymentsFacade(session=session)
    plans_facade = PlansFacade(session=session, repository=PlansRepository(session))
    facade = SubscriptionsFacade(session, payments_facade, plans_facade)
    return facade.subscriptions(
        subject=subject,
        account_id=AccountId(account_id),
    )


class ChangePlanPayload(BaseModel):
    account_id: int
    new_plan_id: int


@router.patch("/subscriptions/{subscription_id}")
def change_plan(
    subscription_id: int,
    payload: ChangePlanPayload,
    subject: Subject = Depends(subject),
) -> SubscriptionDto:
    session = Session()
    payments_facade = PaymentsFacade(session=session)
    plans_facade = PlansFacade(session=session, repository=PlansRepository(session))
    facade = SubscriptionsFacade(session, payments_facade, plans_facade)
    return facade.change_plan(
        subject=subject,
        account_id=AccountId(payload.account_id),
        subscription_id=SubscriptionId(subscription_id),
        new_plan_id=PlanId(payload.new_plan_id),
    )
