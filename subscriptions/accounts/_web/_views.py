from fastapi import APIRouter, Depends

from subscriptions.accounts import AccountsFacade
from subscriptions.api import subject
from subscriptions.auth import Subject

from subscriptions.main import deps

router = APIRouter()


@router.post("/accounts")
def open_account(
    subject: Subject = Depends(subject),
    accounts: AccountsFacade = deps.depends(AccountsFacade),
) -> dict[str, int]:
    account_id = accounts.open(subject)
    return {"account_id": account_id}
