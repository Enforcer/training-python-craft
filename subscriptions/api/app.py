from typing import Callable, Awaitable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from subscriptions.auth import Forbidden
from subscriptions.main import SessionFactory
from subscriptions.payments import payments_router
from subscriptions.plans import plans_router
from subscriptions.subscriptions import subscriptions_router
from subscriptions.accounts import accounts_router

app = FastAPI()
app.include_router(payments_router, prefix="/payments")
app.include_router(plans_router)
app.include_router(subscriptions_router)
app.include_router(accounts_router)


@app.middleware("http")
async def close_session(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    SessionFactory.remove()
    return response


@app.exception_handler(Forbidden)
async def forbidden_handler(request: Request, exc: Forbidden) -> Response:
    return JSONResponse(
        {"message": "You are not allowed to perform this action."}, status_code=403
    )
