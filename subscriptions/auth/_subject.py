from typing import Type

from subscriptions.auth._forbidden import Forbidden
from subscriptions.auth._role import Role
from subscriptions.shared.tenant_id import TenantId


class Subject:
    def __init__(self, tenant_id: TenantId, roles: list[Role]) -> None:
        self._tenant_id = tenant_id
        self._roles: dict[Type[Role], Role] = {type(role): role for role in roles}

    @property
    def tenant_id(self) -> TenantId:
        return self._tenant_id

    def get_role_or_raise(self, role_type: Type[Role]) -> Role:
        """Raises forbidden if role of a given type not found."""
        try:
            return self._roles[role_type]
        except KeyError:
            raise Forbidden
