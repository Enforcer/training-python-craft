from decimal import Decimal

import pytest

from subscriptions.shared.money import Money


@pytest.mark.parametrize(
    "amount, expected",
    [
        [1, Decimal("1.00")],
        [1.2, Decimal("1.20")],
        [1.51, Decimal("1.51")],
        [Decimal("1.01"), Decimal("1.01")],
        [Decimal("1.1"), Decimal("1.10")],
        [0, Decimal("0.00")],
        [0.0, Decimal("0.00")],
        [Decimal(), Decimal("0.00")],
    ],
)
def test_money_with_up_to_two_decimal_points(
    amount: int | float | Decimal, expected: Decimal
) -> None:
    money = Money(amount)

    assert money.amount == expected


@pytest.mark.parametrize(
    "amount",
    [
        -1,
        -1.2,
        1.001,
        Decimal("1.001"),
    ],
)
def test_money_with_negative_or_too_many_decimal_points_in_amount_raises_value_error(
    amount: int | float | Decimal,
) -> None:
    with pytest.raises(ValueError):
        Money(amount)
