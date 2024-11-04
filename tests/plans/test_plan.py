import pytest

from subscriptions.plans import RequestedAddOn
from subscriptions.plans._add_ons._flat_price_add_on import FlatPriceAddOn
from subscriptions.plans._add_ons._invalid_tier_requested import InvalidTierRequested
from subscriptions.plans._add_ons._not_found import RequestedAddOnNotFound
from subscriptions.plans._add_ons._tiered_add_on import TieredAddOn
from subscriptions.plans._add_ons._unit_price_add_on import UnitPriceAddOn
from subscriptions.plans._plan import Plan
from subscriptions.shared.money import Money
from subscriptions.shared.term import Term


@pytest.fixture()
def plan_with_add_ons() -> Plan:
    return Plan(
        tenant_id=1,
        name="Dummy",
        price=Money(5, "USD"),
        description="Irrelevant",
        add_ons=[
            UnitPriceAddOn(name="unit_price", unit_price=Money(1, "USD")),
            FlatPriceAddOn(name="flat_price", flat_price=Money(13, "USD")),
            TieredAddOn(
                name="tiered",
                tiers={
                    1: Money(1, "USD"),
                    3: Money(2, "USD"),
                    5: Money(3, "USD"),
                },
            ),
        ],
    )


@pytest.mark.parametrize("quantity", [1, 2, 3])
def test_adding_only_flat_price_adds_flat_price_to_plan_price_ignoring_quantity(
    plan_with_add_ons: Plan, quantity: int
) -> None:
    result = plan_with_add_ons.calculate_cost(
        term=Term.MONTHLY,
        add_ons=[RequestedAddOn(name="flat_price", quantity=quantity)],
    )

    assert result == Money(18, "USD")


def test_requesting_non_existing_add_on_raises_exception(
    plan_with_add_ons: Plan,
) -> None:
    with pytest.raises(RequestedAddOnNotFound):
        plan_with_add_ons.calculate_cost(
            term=Term.MONTHLY, add_ons=[RequestedAddOn(name="i_dont_exist", quantity=1)]
        )


def test_requesting_not_existing_tier(plan_with_add_ons: Plan) -> None:
    with pytest.raises(InvalidTierRequested):
        plan_with_add_ons.calculate_cost(
            term=Term.MONTHLY, add_ons=[RequestedAddOn(name="tiered", quantity=100)]
        )
