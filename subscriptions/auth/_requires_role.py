import functools
import inspect
import itertools
from typing import Type, Callable

from subscriptions.auth import Subject
from subscriptions.auth._role import Role


def requires_role[**PP, TT](
    role_type: Type[Role],
) -> Callable[[Callable[PP, TT]], Callable[PP, TT]]:
    def decorator[**P, T](method: Callable[P, T]) -> Callable[P, T]:
        annotations = inspect.get_annotations(method)
        for arg_name, type_annotation in annotations.items():
            if arg_name != "return" and type_annotation is Subject:
                break
        else:
            raise Exception(
                f"{method} needs to accept Subject argument so role can be checked"
            )

        @functools.wraps(method)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            subject = next(
                obj
                for obj in itertools.chain(args, kwargs.values())
                if isinstance(obj, Subject)
            )
            subject.get_role_or_raise(role_type)
            return method(*args, **kwargs)

        return wrapper

    return decorator
