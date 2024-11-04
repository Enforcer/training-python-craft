from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from subscriptions.plans._add_ons._flat_price_add_on import FlatPriceAddOn
from subscriptions.plans._add_ons._requested_add_on import RequestedAddOn
from subscriptions.plans._add_ons._tiered_add_on import TieredAddOn
from subscriptions.plans._add_ons._unit_price_add_on import UnitPriceAddOn
from subscriptions.plans._plan_id import PlanId
from subscriptions.plans._plan_dto import PlanDto
from subscriptions.plans._plan import Plan
from subscriptions.shared.money import Money
from subscriptions.shared.tenant_id import TenantId
from subscriptions.shared.term import Term


class PlansFacade:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        tenant_id: int,
        name: str,
        price: Money,
        description: str,
        add_ons: list[UnitPriceAddOn | FlatPriceAddOn | TieredAddOn],
    ) -> PlanDto:
        plan = Plan(
            tenant_id=tenant_id,
            name=name,
            price=price,
            description=description,
            add_ons=add_ons,
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

    def calculate_cost(
        self,
        tenant_id: TenantId,
        plan_id: PlanId,
        term: Term,
        add_ons: list[RequestedAddOn],
    ) -> Money:
        stmt = select(Plan).filter(Plan.id == plan_id, Plan.tenant_id == tenant_id)
        plan = self._session.execute(stmt).scalars().one()

        price = plan.price
        for requested_add_on in add_ons:
            corresponding_add_on = next(
                add_on
                for add_on in plan.add_ons
                if add_on.name == requested_add_on.name
            )
            if isinstance(corresponding_add_on, UnitPriceAddOn):
                add_on_price = (
                    corresponding_add_on.unit_price * requested_add_on.quantity
                )
            elif isinstance(corresponding_add_on, FlatPriceAddOn):
                add_on_price = corresponding_add_on.flat_price
            elif isinstance(corresponding_add_on, TieredAddOn):
                add_on_price = corresponding_add_on.tiers[requested_add_on.quantity]
            else:
                raise Exception("Impossible")

            price += add_on_price

        multiplier = 1 if term == Term.MONTHLY else 12
        return price * multiplier
