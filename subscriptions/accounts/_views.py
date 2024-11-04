from fastapi import APIRouter, Depends

from subscriptions.accounts import AccountsFacade
from subscriptions.api.multitenancy import subject
from subscriptions.auth import Subject

from subscriptions.main import Session
from subscriptions.payments import PaymentsFacade

router = APIRouter()


@router.post("/accounts")
def open_account(subject: Subject = Depends(subject)) -> dict[str, int]:
    session = Session()
    payments_facade = PaymentsFacade(session)
    facade = AccountsFacade(session, payments_facade)
    account_id = facade.open(subject)
    return {"account_id": account_id}
