from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from subscriptions.shared.account_id import AccountId
from subscriptions.main import deps, StripePublishableKey
from subscriptions.payments._app._facade import PaymentsFacade

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/details")
def get_enter_details_page(
    request: Request,
    account_id: int,
    return_url: str = "",
    payments: PaymentsFacade = deps.depends(PaymentsFacade),
    stripe_publishable_key: StripePublishableKey = deps.depends(StripePublishableKey),
) -> HTMLResponse:
    account_id = AccountId(account_id)
    client_secret = payments.client_secret(account_id)
    return templates.TemplateResponse(
        request=request,
        name="payment_details.html",
        context={
            "client_secret": client_secret,
            "publishable_key": stripe_publishable_key,
            "return_url": return_url or "http://localhost:8000/payments/details_saved",
        },
    )


@router.get("/details_saved")
def success_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="payment_details_saved.html",
    )
