import functools
from decimal import Decimal
from typing import Any, TypedDict, Type, ClassVar

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
from sqlalchemy import types, JSON, Dialect


class Currency:
    iso_code: ClassVar[str]
    decimal_places: ClassVar[int]
    __iso_code_to_type: dict[str, Type["Currency"]] = {}

    def __init_subclass__(cls) -> None:
        cls.__iso_code_to_type[cls.iso_code] = cls

    @classmethod
    def supported_currencies(cls) -> set[str]:
        return set(cls.__iso_code_to_type.keys())

    @classmethod
    def from_iso_code(cls, iso_code: str) -> Type["Currency"]:
        return cls.__iso_code_to_type[iso_code]


class USD(Currency):
    iso_code = "USD"
    decimal_places = 2


class JPY(Currency):
    iso_code = "JPY"
    decimal_places = 0


class ETH(Currency):
    iso_code = "ETH"
    decimal_places = 24


@functools.total_ordering
class Money:
    def __init__(self, amount: float | int | Decimal, currency: str) -> None:
        a_currency = Currency.from_iso_code(currency)

        if amount < 0:
            raise ValueError(f"Invalid amount: {amount}")

        if isinstance(amount, float):
            amount = Decimal(str(amount))
        elif isinstance(amount, int):
            amount = Decimal(amount)

        min_unit = Decimal(str(10**-a_currency.decimal_places))
        normalized = amount.quantize(min_unit)
        if normalized != amount:
            raise ValueError(f"Invalid amount: {amount}")

        self._amount = normalized
        self._currency = currency

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def currency(self) -> str:
        return self._currency

    def __mul__(self, other: Any) -> "Money":
        if isinstance(other, int):
            return Money(amount=self.amount * other, currency=self.currency)

        raise TypeError(f"Multiplication of Money by {type(other)} is not supported")

    def __add__(self, other: Any) -> "Money":
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add {type(other)} to Money")

        if other.currency != self.currency:
            raise ValueError("Cannot add monet in different currencies!")

        return Money(self.amount + other.amount, self.currency)

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            raise TypeError(f"Comparison of Money with {type(other)} is not supported")

        if self.currency != other.currency:
            raise ValueError("Cannot compare money in different currencies")

        return self.amount <= other.amount

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return False

        return (other.amount, other.currency) == (self.amount, other.currency)

    def __repr__(self) -> str:
        return f"Money({repr(self.amount)}, {repr(self.currency)})"


class MoneyType(types.TypeDecorator[Money]):
    """Adapter for SQLAlchemy that enables storing Money instances in JSON column.

    Example usage:

            ```python
            class Order(Base):
                __tablename__ = "orders"

                id: Mapped[int] = mapped_column(init=False, primary_key=True)
                amount: Mapped[Money] = mapped_column(MoneyType)
                description: Mapped[str]
            ```
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(
        self, value: Money | None, dialect: Dialect
    ) -> dict[str, str] | None:
        if value is None:
            return None

        return {"amount": str(value.amount), "currency": value.currency}

    def process_result_value(self, value: Any | None, dialect: Dialect) -> Money | None:
        if value is None:
            return None
        as_decimal = Decimal(value["amount"])
        return Money(amount=as_decimal, currency=value["currency"])


class MoneyAnnotation:
    """Pydantic annotation that enables support for Money class.

    Example usage:

        ```python
        class Order(BaseModel):
            amount: Annotated[Money, MoneyAnnotation]
        ```
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        def _validate_from_dict(v: dict[str, Any]) -> Money:
            return Money(**v)

        class _MoneyAsTypedDict(TypedDict):
            amount: float
            currency: str

        from_dict_schema = core_schema.chain_schema(
            [
                core_schema.typed_dict_schema(
                    {
                        "amount": core_schema.typed_dict_field(
                            core_schema.float_schema()
                        ),
                        "currency": core_schema.typed_dict_field(
                            core_schema.str_schema(max_length=3)
                        ),
                    },
                    cls=_MoneyAsTypedDict,
                ),
                core_schema.no_info_plain_validator_function(_validate_from_dict),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_dict_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(Money),
                    from_dict_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: {
                    "amount": instance.amount,
                    "currency": instance.currency,
                }
            ),
        )
