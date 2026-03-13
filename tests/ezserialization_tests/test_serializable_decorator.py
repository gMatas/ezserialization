import json
from typing import Mapping, cast

from ezserialization import (
    Serializable,
    deserialize,
    serializable,
    type_field_name,
)


@serializable  # <- valid for serialization
@serializable(name="A")
@serializable(name="XXX")
class _CaseAUsingAutoName(Serializable):
    def __init__(self, value: str):
        self.value = value

    def to_raw_dict(self) -> dict:
        return {"value": self.value}

    def to_dict(self) -> Mapping:
        return self.to_raw_dict()

    @classmethod
    def from_dict(cls, src: Mapping):
        return cls(value=src["value"])

    @classmethod
    def abs_qualname(cls) -> str:
        return f"{cls.__module__}.{cls.__qualname__}"


@serializable(name="B")  # <- valid for serialization
@serializable(name="YYY")
@serializable
@serializable(name="ZZZ")
class _CaseBUsingNameAlias(Serializable):
    def __init__(self, value: str):
        self.value = value

    def to_dict(self) -> Mapping:
        return {"value": self.value}

    @classmethod
    def from_dict(cls, src: Mapping):
        return cls(value=src["value"])


@serializable
class _SerializableParent:
    def __init__(self, value: str):
        self.value = value

    def to_dict(self) -> Mapping:
        return {"value": self.value}

    @classmethod
    def from_dict(cls, src: Mapping):
        return cls(value=src["value"])


@serializable
class _SerializableChild(_SerializableParent):
    """Inherits to_dict/from_dict from parent."""

    pass


def test_serializable_inheritance():
    # Parent round-trip
    parent = _SerializableParent("hello")
    data = parent.to_dict()
    assert data[type_field_name] == f"{_SerializableParent.__module__}.{_SerializableParent.__qualname__}"
    restored = deserialize(json.loads(json.dumps(data)))
    assert isinstance(restored, _SerializableParent)
    assert not isinstance(restored, _SerializableChild)
    assert restored.value == "hello"

    # Child round-trip (inherits to_dict/from_dict)
    child = _SerializableChild("world")
    data = child.to_dict()
    assert data[type_field_name] == f"{_SerializableChild.__module__}.{_SerializableChild.__qualname__}"
    restored = deserialize(json.loads(json.dumps(data)))
    assert isinstance(restored, _SerializableChild)
    assert restored.value == "world"


def test_serialization_typenames_order():
    """
    Expected behaviour: Only the top typename is used to serialize instances.
    On the other hand, for deserialization all typenames are valid.
    """

    a = _CaseAUsingAutoName("a")
    data = a.to_dict()

    a.from_dict(data)

    assert data["_type_"] == _CaseAUsingAutoName.abs_qualname()
    assert a.value == cast(_CaseAUsingAutoName, deserialize(json.loads(json.dumps(data)))).value

    b = _CaseBUsingNameAlias("b")
    data = b.to_dict()
    assert data["_type_"] == "B"
    assert b.value == cast(_CaseBUsingNameAlias, deserialize(json.loads(json.dumps(data)))).value
