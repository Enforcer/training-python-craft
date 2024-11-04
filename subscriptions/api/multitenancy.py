from fastapi import Request, HTTPException
from subscriptions.api import jwt
from subscriptions.auth import Subject


def extract_tenant_id(request: Request) -> int:
    if auth_header := request.headers.get("Authorization"):
        _token_type, token = auth_header.split(maxsplit=1)
        decoded = jwt.decode(token)
        return decoded.tenant_id
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")


def subject(request: Request) -> Subject:
    if auth_header := request.headers.get("Authorization"):
        _token_type, token = auth_header.split(maxsplit=1)
        decoded = jwt.decode(token)
        return Subject(tenant_id=decoded.tenant_id, roles=[])
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
