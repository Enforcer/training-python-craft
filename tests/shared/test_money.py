from decimal import Decimal

import pytest

from subscriptions.shared.money import Money


@pytest.mark.parametrize(
    "amount, currency, expected",
    [
        [1, "USD", Decimal("1.00")],
        [1.2, "USD", Decimal("1.20")],
        [1.51, "USD", Decimal("1.51")],
        [Decimal("1.01"), "USD", Decimal("1.01")],
        [Decimal("1.1"), "USD", Decimal("1.10")],
        [0, "USD", Decimal("0.00")],
        [0.0, "USD", Decimal("0.00")],
        [Decimal(), "USD", Decimal("0.00")],
        [Decimal(), "JPY", Decimal("0.00")],
        [10, "JPY", Decimal("10")],
        [0.00000005, "ETH", Decimal("0.00000005")],
        [10**-24, "ETH", Decimal("0." + ("0" * 23) + "1")],
    ],
)
def test_money_with_up_to_two_decimal_points(
    amount: int | float | Decimal, currency: str, expected: Decimal
) -> None:
    money = Money(amount, currency)

    assert money.amount == expected


@pytest.mark.parametrize(
    "amount, currency",
    [
        [-1, "USD"],
        [-1.2, "USD"],
        [-1.001, "USD"],
        [1.001, "USD"],
        [0.1, "JPY"],
        [10**-25, "ETH"],
    ],
)
def test_money_with_negative_or_too_many_decimal_points_in_amount_raises_value_error(
    amount: int | float | Decimal, currency: str
) -> None:
    with pytest.raises(ValueError):
        Money(amount, currency)
