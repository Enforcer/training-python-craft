from sqlalchemy.orm import Session

from subscriptions.accounts._account import Account
from subscriptions.payments import PaymentsFacade
from subscriptions.shared.account_id import AccountId


class AccountsFacade:
    def __init__(self, session: Session, payments_facade: PaymentsFacade) -> None:
        self._session = session
        self._payments_facade = payments_facade

    def open(self, tenant_id: int) -> AccountId:
        account = Account(tenant_id=tenant_id)
        self._session.add(account)
        self._session.commit()
        account_id = AccountId(account.id)
        self._payments_facade.register_account(account_id, tenant_id)
        return account_id
