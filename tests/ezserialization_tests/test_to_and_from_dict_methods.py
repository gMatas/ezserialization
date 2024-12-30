import json
from abc import ABC
from typing import Mapping, Type, cast, overload

from ezserialization import (
    Serializable,
    deserialize,
    serializable,
)


class _BaseTestCase(Serializable, ABC):
    def __init__(self, value: str):
        self.value = value

    def to_dict(self) -> Mapping:
        return self.to_raw_dict()

    def to_raw_dict(self) -> dict:
        return {"value": self.value}


@serializable
class _TestFromDictWithClassmethod(_BaseTestCase):
    @classmethod
    def from_dict(cls, src: Mapping) -> "_TestFromDictWithClassmethod":
        return cls(value=src["value"])


@serializable
class _TestFromDictWithStaticmethod(_BaseTestCase):
    @staticmethod
    @overload
    def from_dict(cls: Type["_TestFromDictWithStaticmethod"], src: Mapping) -> "_TestFromDictWithStaticmethod": ...

    @staticmethod
    @overload
    def from_dict(*args) -> "_TestFromDictWithStaticmethod": ...

    @staticmethod
    def from_dict(*args, **kwargs) -> "_TestFromDictWithStaticmethod":
        obj = args[0](value=args[1]["value"])
        assert isinstance(obj, _TestFromDictWithStaticmethod)
        return obj


def test_from_dict_as_classmethod():
    obj = _TestFromDictWithClassmethod("wow")
    obj_dict = obj.to_dict()
    assert obj.value == obj.from_dict(obj_dict).value
    assert obj.value == _TestFromDictWithClassmethod.from_dict(obj_dict).value

    assert obj.value == cast(_TestFromDictWithClassmethod, deserialize(json.loads(json.dumps(obj_dict)))).value


def test_from_dict_as_staticmethod():
    obj = _TestFromDictWithStaticmethod("wow")
    obj_dict = obj.to_dict()
    assert obj.value == obj.from_dict(obj_dict).value
    assert obj.value == _TestFromDictWithStaticmethod.from_dict(obj, obj_dict).value
    assert obj.value == _TestFromDictWithStaticmethod.from_dict(_TestFromDictWithStaticmethod, obj_dict).value

    assert obj.value == cast(_TestFromDictWithStaticmethod, deserialize(json.loads(json.dumps(obj_dict)))).value
