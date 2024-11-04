from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from subscriptions.plans._plan import Plan
from subscriptions.shared.tenant_id import TenantId


class PlansRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, plan: Plan) -> None:
        self._session.add(plan)

    def get_all(self, tenant_id: TenantId) -> Sequence[Plan]:
        stmt = select(Plan).filter(Plan.tenant_id == tenant_id)
        return self._session.execute(stmt).scalars().all()
