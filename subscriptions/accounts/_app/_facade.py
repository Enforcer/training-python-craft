from sqlalchemy.orm import Session

from subscriptions.accounts._domain._account import Account
from subscriptions.accounts._app._role_objects import AccountsAdmin
from subscriptions.auth import requires_role, Subject
from subscriptions.payments import PaymentsFacade
from subscriptions.shared.account_id import AccountId


class AccountsFacade:
    def __init__(self, session: Session, payments_facade: PaymentsFacade) -> None:
        self._session = session
        self._payments_facade = payments_facade

    @requires_role(AccountsAdmin)
    def open(self, subject: Subject) -> AccountId:
        account = Account(tenant_id=subject.tenant_id)
        self._session.add(account)
        self._session.commit()
        account_id = AccountId(account.id)
        self._payments_facade.register_account(account_id, subject.tenant_id)
        return account_id
