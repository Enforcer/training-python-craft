from typing import Type, TypeAlias, cast

from pydantic import TypeAdapter
from sqlalchemy import Dialect, types, JSON as ColumnJSON
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class Base(MappedAsDataclass, DeclarativeBase):
    pass


JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


class AsJSON[T](types.TypeDecorator[T]):
    """Will serialize to JSON and back everything that TypeAdapter handles.

    Usage: field: Mapped[Dataclass] = mapped_column(AsJSON[Dataclass])
    """

    impl = ColumnJSON
    cache_ok = True

    _type_adapter: TypeAdapter[T]

    def __class_getitem__(cls, type_: Type[T]) -> "AsJSON[T]":
        type_adapter = TypeAdapter(type_)
        specialized_class = type(
            f"JSONSerializable[{type_.__name__}]",
            (cls,),
            {"_type_adapter": type_adapter},
        )
        return cast("AsJSON[T]", specialized_class)

    def process_bind_param(self, value: T | None, dialect: Dialect) -> JSON | None:
        if self._type_adapter is None:
            raise RuntimeError(f"Type adapter not set, use {type(self).__name__}[Type]")

        if value is None:
            return value

        return cast(JSON, self._type_adapter.dump_python(value, mode="json"))

    def process_result_value(self, value: JSON | None, dialect: Dialect) -> T | None:
        if value is None:
            return value

        return self._type_adapter.validate_python(value)
