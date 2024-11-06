from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from subscriptions.shared.account_id import AccountId
from subscriptions.main import SessionFactory, payments_settings
from subscriptions.payments._facade import PaymentsFacade

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/details")
def get_enter_details_page(
    request: Request, account_id: int, return_url: str = ""
) -> HTMLResponse:
    session = SessionFactory()
    account_id = AccountId(account_id)
    payments = PaymentsFacade(session=session)
    client_secret = payments.client_secret(account_id)
    return templates.TemplateResponse(
        request=request,
        name="payment_details.html",
        context={
            "client_secret": client_secret,
            "publishable_key": payments_settings.STRIPE_PUBLISHABLE_KEY,
            "return_url": return_url or "http://localhost:8000/payments/details_saved",
        },
    )


@router.get("/details_saved")
def success_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="payment_details_saved.html",
    )
