#   Copyright 2022 Modelyst LLC
#   All Rights Reserved

import inspect
import sys
from typing import Any, Callable, Tuple, Type, Union

try:
    from typing import GenericAlias as TypingGenericAlias  # type: ignore
except ImportError:
    # python < 3.9 does not have GenericAlias (list[int], tuple[str, ...] and so on)
    TypingGenericAlias = ()  # type: ignore

if sys.version_info < (3, 10):
    WithArgsTypes = (TypingGenericAlias,)
else:
    import types

    WithArgsTypes = (types.GenericAlias, types.UnionType)


# Adapted from pydantic
def lenient_issubclass(cls: Any, class_or_tuple: Union[Type[Any], Tuple[Type[Any], ...], None]) -> bool:
    try:
        return isinstance(cls, type) and issubclass(cls, class_or_tuple)  # type: ignore[arg-type]
    except TypeError:
        if isinstance(cls, WithArgsTypes):
            return False
        raise  # pragma: no cover


def is_coroutine_callable(call: Callable[..., Any]) -> bool:
    if inspect.isroutine(call):
        return inspect.iscoroutinefunction(call)
    if inspect.isclass(call):
        return False
    dunder_call = getattr(call, "__call__", None)  # noqa: B004
    return inspect.iscoroutinefunction(dunder_call)
