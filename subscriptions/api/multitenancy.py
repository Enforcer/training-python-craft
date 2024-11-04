from fastapi import Request, HTTPException
from subscriptions.api import jwt
from subscriptions.auth import Subject, Role
from subscriptions.shared.tenant_id import TenantId


def subject(request: Request) -> Subject:
    from subscriptions.plans import PlansViewer, PlansAdmin
    from subscriptions.subscriptions import SubscriptionsViewer, SubscriptionsAdmin
    from subscriptions.accounts import AccountsAdmin

    if auth_header := request.headers.get("Authorization"):
        _token_type, token = auth_header.split(maxsplit=1)
        decoded = jwt.decode(token)
        roles: set[Role] = set()
        if "admin" in decoded.roles:
            roles.add(PlansViewer())
            roles.add(PlansAdmin())
            roles.add(SubscriptionsViewer())
            roles.add(SubscriptionsAdmin())
            roles.add(AccountsAdmin())

        if "viewer" in decoded.roles:
            roles.add(PlansViewer())
            roles.add(SubscriptionsViewer())

        tenant_id = TenantId(decoded.tenant_id)
        return Subject(tenant_id=tenant_id, roles=list(roles))
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
