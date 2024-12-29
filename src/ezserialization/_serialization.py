import contextlib
import functools
import importlib
import threading
from abc import abstractmethod
from copy import copy
from typing import Callable, Dict, Iterator, Mapping, Optional, Protocol, Type, TypeVar, cast

__all__ = [
    "TYPE_FIELD_NAME",
    "using_serialization",
    "use_serialization",
    "no_serialization",
    "Serializable",
    "serializable",
    "deserialize",
    "isdeserializable",
    "set_typename_alias",
]

TYPE_FIELD_NAME = "_type_"
"""
This attribute is being injected into the "serialized" object's dict to hold information about the source type. 

This value can customized by the end-user.
"""


class Serializable(Protocol):
    @abstractmethod
    def to_dict(self) -> Mapping: ...

    @classmethod
    @abstractmethod
    def from_dict(cls, src: Mapping) -> "Serializable": ...


def _is_serializable_subclass(cls: Type) -> bool:
    """
    As of now, ``@runtime_checkable`` protocols only check if a subclass has the same methods as the target without
    validating their full signatures.
    Thus, mypy recommends not rely on this decorator and just use ``hasattr()`` instead.

    :param cls: Type to check.
    """
    return hasattr(cls, "from_dict") and hasattr(cls, "to_dict")


_T = TypeVar("_T", bound=Serializable)
"""
Serializable object type.
"""

_thread_local = threading.local()
_thread_local.enabled = (_SERIALIZATION_ENABLED_DEFAULT := True)
"""
Thread-safe serialization enabling/disabling flag. 
"""


def using_serialization() -> bool:
    if not hasattr(_thread_local, "enabled"):
        _thread_local.enabled = _SERIALIZATION_ENABLED_DEFAULT
    return cast(bool, _thread_local.enabled)


@contextlib.contextmanager
def use_serialization() -> Iterator[None]:
    prev = using_serialization()
    try:
        _thread_local.enabled = _SERIALIZATION_ENABLED_DEFAULT
        yield
    finally:
        _thread_local.enabled = prev


@contextlib.contextmanager
def no_serialization() -> Iterator[None]:
    prev = using_serialization()
    try:
        _thread_local.enabled = not _SERIALIZATION_ENABLED_DEFAULT
        yield
    finally:
        _thread_local.enabled = prev


_types_: Dict[str, Type[Serializable]] = {}
_typenames_: Dict[Type[Serializable], str] = {}
_typename_aliases_: Dict[str, str] = {}


def set_typename_alias(alias: str, typename: str) -> None:
    if alias in _typename_aliases_:
        raise ValueError(f"Given alias '{alias}' is already taken!")
    _typename_aliases_[alias] = typename


def isdeserializable(src: Mapping) -> bool:
    """Return whether an object is deserializable.

    :param src: Source mapping object.
    :return: True if object is deserializable.
    """
    return isinstance(src, dict) and TYPE_FIELD_NAME in src


def _abs_qualname(cls: Type) -> str:
    if hasattr(cls, "__qualname__"):
        class_name = cls.__qualname__
    else:
        class_name = cls.__name__

    return f"{cls.__module__}.{class_name}"


def _is_same_type_by_qualname(a: Type, b: Type) -> bool:
    """
    This method is only being used by serialization as a temporary workaround for an issue.

    The issue it tries to solve is when same module is being loaded multiple times
    by different runs that module is treated as two different instances
    i.e. imported normally within the lib and imported directly by some tools like pytest.
    """

    return _abs_qualname(a) == _abs_qualname(b)


def serializable(cls: Optional[Type[_T]] = None, *, name: Optional[str] = None):
    def wrapper(cls_: Type[_T]) -> Type[_T]:
        nonlocal name
        if name is None:
            name = _abs_qualname(cls_)

        if name in _types_ and not _is_same_type_by_qualname(cls_, _types_[name]):
            raise KeyError(f"This {name=} is already taken!")

        if not _is_serializable_subclass(cls_):
            raise TypeError("Decorated type is not serializable.")

        if cls_ not in _typenames_:
            # Wrap to/from_dict methods only once.

            def wrap_to_dict(method: Callable[..., Mapping]):
                @functools.wraps(method)
                def to_dict_wrapper(obj: Serializable) -> Mapping:
                    data = method(obj)
                    # Wrap object with serialization metadata.
                    if TYPE_FIELD_NAME in data:
                        raise KeyError(f"Key '{TYPE_FIELD_NAME}' already exist in the serialized data mapping!")
                    if using_serialization():
                        typename = _typenames_[type(obj)]
                        return {TYPE_FIELD_NAME: typename, **data}
                    return copy(data)

                return to_dict_wrapper

            cls_.to_dict = wrap_to_dict(cls_.to_dict)  # type: ignore[method-assign]

            def wrap_from_dict(method: Callable[..., Serializable]):
                @functools.wraps(method)
                def from_dict_wrapper(*args) -> Serializable:
                    # See if `from_dict` method is staticmethod-like or classmethod-like (or normal method-like),
                    # i.e. `Serializable.from_dict(data)` or `Serializable().from_dict(data)`.
                    src = args[1] if len(args) == 2 else args[0]
                    # Remove deserialization metadata.
                    src = dict(src)
                    src.pop(TYPE_FIELD_NAME, None)
                    # Deserialize as-is.
                    return method(src)

                return from_dict_wrapper

            cls_.from_dict = wrap_from_dict(cls_.from_dict)  # type: ignore[method-assign]

        _types_[name] = cls_
        _typenames_[cls_] = name
        return cls_

    if cls is None:
        # Decorator being called with parens i.e. @serializable(...).
        return wrapper

    # Decorator called as @serializable without parens.
    return wrapper(cls)


def deserialize(src: Mapping) -> Serializable:
    if not isdeserializable(src):
        raise KeyError(f"Given data mapping does not contain key '{TYPE_FIELD_NAME}' required for deserialization.")

    typename = src[TYPE_FIELD_NAME]
    assert isinstance(typename, str), f"`typename` must be a string! Received {type(typename)=}"

    if typename not in _types_:
        typename_alias = None
        if typename in _typename_aliases_:
            typename_alias = typename
            typename = _typename_aliases_[typename]

        parent_name = typename.rsplit(".", 1)[0]
        try:
            importlib.import_module(parent_name)
        except ImportError:
            err_msg = f"Failed to import the given type: `{typename}`."
            if typename_alias is not None:
                err_msg += f" ({typename_alias=})"
            raise ImportError(err_msg)

    cls = _types_[typename]
    obj = cls.from_dict(src)
    return obj
