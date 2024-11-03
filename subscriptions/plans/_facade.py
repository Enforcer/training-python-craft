from decimal import Decimal

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from subscriptions.plans._plan_id import PlanId
from subscriptions.plans._plan_dto import PlanDto
from subscriptions.plans._plan import Plan
from subscriptions.shared.tenant_id import TenantId
from subscriptions.shared.term import Term


class PlansFacade:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, tenant_id: int, name: str, price: float, description: str) -> PlanDto:
        plan = Plan(
            tenant_id=tenant_id,
            name=name,
            price=price,
            description=description,
        )
        self._session.add(plan)
        self._session.commit()
        return PlanDto.model_validate(plan)

    def get_all(self, tenant_id: int) -> list[PlanDto]:
        stmt = select(Plan).filter(Plan.tenant_id == tenant_id)
        plans = self._session.execute(stmt).scalars().all()
        return [PlanDto.model_validate(plan) for plan in plans]

    def delete(self, tenant_id: int, plan_id: int) -> None:
        stmt = delete(Plan).filter(Plan.tenant_id == tenant_id, Plan.id == plan_id)
        self._session.execute(stmt)
        self._session.commit()

    def calculate_cost(self, tenant_id: TenantId, plan_id: PlanId, term: Term) -> float:
        stmt = select(Plan).filter(Plan.id == plan_id, Plan.tenant_id == tenant_id)
        plan = self._session.execute(stmt).scalars().one()
        multiplier = 1 if term == Term.MONTHLY else 12
        return float(Decimal(str(plan.price)) * multiplier)
