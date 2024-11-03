from fastapi import Request, HTTPException
from subscriptions.api import jwt


def extract_tenant_id(request: Request) -> int:
    if auth_header := request.headers.get("Authorization"):
        _token_type, token = auth_header.split(maxsplit=1)
        decoded = jwt.decode(token)
        return decoded.tenant_id
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
