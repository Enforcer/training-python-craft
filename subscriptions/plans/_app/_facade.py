from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from subscriptions.auth import Subject, requires_role
from subscriptions.plans._domain._add_ons._flat_price_add_on import FlatPriceAddOn
from subscriptions.plans._domain._add_ons._requested_add_on import RequestedAddOn
from subscriptions.plans._domain._add_ons._tiered_add_on import TieredAddOn
from subscriptions.plans._domain._add_ons._unit_price_add_on import UnitPriceAddOn
from subscriptions.plans._domain._plan_id import PlanId
from subscriptions.plans._app._plan_dto import PlanDto
from subscriptions.plans._domain._plan import Plan
from subscriptions.plans._app._repository import PlansRepository
from subscriptions.plans._app._role_objects import PlansAdmin, PlansViewer
from subscriptions.shared.money import Money
from subscriptions.shared.tenant_id import TenantId
from subscriptions.shared.term import Term


class PlansFacade:
    def __init__(self, session: Session, repository: PlansRepository) -> None:
        self._session = session
        self._repository = repository

    @requires_role(PlansAdmin)
    def add(
        self,
        subject: Subject,
        name: str,
        price: Money,
        description: str,
        add_ons: list[UnitPriceAddOn | FlatPriceAddOn | TieredAddOn],
    ) -> PlanDto:
        plan = Plan(
            tenant_id=subject.tenant_id,
            name=name,
            price=price,
            description=description,
            add_ons=add_ons,
        )
        self._repository.add(plan)
        self._session.commit()
        return PlanDto.model_validate(plan)

    @requires_role(PlansViewer)
    def get_all(self, subject: Subject) -> list[PlanDto]:
        plans = self._repository.get_all(subject.tenant_id)
        return [PlanDto.model_validate(plan) for plan in plans]

    @requires_role(PlansAdmin)
    def delete(self, subject: Subject, plan_id: int) -> None:
        stmt = delete(Plan).filter(
            Plan.tenant_id == subject.tenant_id, Plan.id == plan_id
        )
        self._session.execute(stmt)
        self._session.commit()

    def calculate_cost(
        self,
        tenant_id: TenantId,
        plan_id: PlanId,
        term: Term,
        add_ons: list[RequestedAddOn],
    ) -> Money:
        stmt = select(Plan).filter(Plan.id == plan_id, Plan.tenant_id == tenant_id)
        plan = self._session.execute(stmt).scalars().one()
        return plan.calculate_cost(term, add_ons)
