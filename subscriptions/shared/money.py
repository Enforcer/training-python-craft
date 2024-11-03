from decimal import Decimal
from typing import Any, TypedDict

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
from sqlalchemy import types, JSON, Dialect


class Money:
    def __init__(self, amount: float | int | Decimal) -> None:
        if amount < 0:
            raise ValueError(f"Invalid amount: {amount}")

        if isinstance(amount, float):
            amount = Decimal(str(amount))
        elif isinstance(amount, int):
            amount = Decimal(amount)

        # TODO: we're gonna handle more currencies
        normalized = amount.quantize(Decimal("0.01"))
        if normalized != amount:
            raise ValueError(f"Invalid amount: {amount}")

        self._amount = normalized

    @property
    def amount(self) -> Decimal:
        return self._amount


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
        return {"amount": str(value.amount)} if value is not None else None

    def process_result_value(self, value: Any | None, dialect: Dialect) -> Money | None:
        if value is None:
            return None
        as_decimal = Decimal(value["amount"])
        return Money(amount=as_decimal)


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

        from_dict_schema = core_schema.chain_schema(
            [
                core_schema.typed_dict_schema(
                    {
                        "amount": core_schema.typed_dict_field(
                            core_schema.float_schema()
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
                lambda instance: {"amount": instance.amount}
            ),
        )
