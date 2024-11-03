from fastapi import APIRouter, Depends

from subscriptions.accounts import AccountsFacade
from subscriptions.api.multitenancy import extract_tenant_id

from subscriptions.main import Session
from subscriptions.payments import PaymentsFacade

router = APIRouter()


@router.post("/accounts")
def open_account(tenant_id: int = Depends(extract_tenant_id)) -> dict[str, int]:
    session = Session()
    payments_facade = PaymentsFacade(session)
    facade = AccountsFacade(session, payments_facade)
    account_id = facade.open(tenant_id)
    return {"account_id": account_id}
