from datetime import datetime, timezone, timedelta
import secrets

import jwt
from pydantic import BaseModel

SECRET = secrets.token_hex(16)
ALGORITHM = "HS256"
VALID_FOR = timedelta(minutes=30)


class Payload(BaseModel):
    user_id: int
    tenant_id: int
    roles: list[str]


def encode(payload: Payload) -> str:
    expires_at = datetime.now(timezone.utc) + VALID_FOR
    raw = payload.model_dump()
    return jwt.encode(
        {**raw, "exp": expires_at},
        SECRET,
        algorithm=ALGORITHM,
    )


def decode(token: str) -> Payload:
    raw = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    return Payload.model_validate(raw)
