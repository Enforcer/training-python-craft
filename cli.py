import typer

from subscriptions.accounts import AccountsFacade
from subscriptions.payments import PaymentsFacade
from subscriptions.shared.account_id import AccountId
from subscriptions.shared.sqlalchemy import Base
from subscriptions.main import engine, Session

app = typer.Typer()


@app.command()
def init_db() -> None:
    Base.metadata.create_all(engine)


@app.command()
def create_new_account(tenant_id: int = 1) -> None:
    session = Session()
    account_facade = AccountsFacade(session, PaymentsFacade(session))
    account_facade.open(tenant_id)


@app.command()
def charge(account_id: int, amount: float = 10.99) -> None:
    session = Session()
    payments_facade = PaymentsFacade(session)
    payments_facade.charge(AccountId(account_id), amount)


if __name__ == "__main__":
    app()
