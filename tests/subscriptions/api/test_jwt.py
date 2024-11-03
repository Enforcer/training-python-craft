from subscriptions.api import jwt
from subscriptions.api.jwt import Payload


def test_encoded_jwt_is_decoded_back() -> None:
    payload = Payload(
        user_id=1,
        tenant_id=1,
        roles=["admin"],
    )

    encoded = jwt.encode(payload)

    decoded: Payload = jwt.decode(encoded)
    assert decoded == payload
