import threading
import time
from typing import Mapping, cast

from ezserialization import (
    Serializable,
    deserialize,
    no_serialization,
    serializable,
    use_serialization,
    using_serialization,
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


def test_serialization_typenames_order():
    """
    Expected behaviour: Only the top typename is used to serialize instances.
    On the other hand, for deserialization all typenames are valid.
    """

    a = _CaseAUsingAutoName("a")
    data = a.to_dict()
    assert data["_type_"] == _CaseAUsingAutoName.abs_qualname()
    assert a.value == cast(_CaseAUsingAutoName, deserialize(data)).value

    b = _CaseBUsingNameAlias("b")
    data = b.to_dict()
    assert data["_type_"] == "B"
    assert b.value == cast(_CaseBUsingNameAlias, deserialize(data)).value


def test_threadsafe_serialization_enabling_and_disabling():
    a = _CaseAUsingAutoName("foo")

    assert using_serialization(), "By default, serialization must be enabled!"

    a_dict = a.to_dict()
    raw_a_dict = a.to_raw_dict()
    assert a_dict != raw_a_dict, "Bad test setup."

    thread = _TestThread()
    with no_serialization():
        with use_serialization():
            assert a.to_dict() == a_dict
        assert a.to_dict() == raw_a_dict

        thread.start()
        while not thread.serialization_explicitly_enabled:
            time.sleep(0.1)

        assert not using_serialization()

    assert using_serialization()
    thread.should_stop = True
    while not thread.finished:
        time.sleep(0.1)

    if thread.exception is not None:
        raise thread.exception

    assert using_serialization()


class _TestThread(threading.Thread):
    def __init__(self):
        self.exception = None
        self.finished = False
        self.should_stop = False
        self.serialization_explicitly_enabled = False
        super().__init__(target=self._fun, daemon=True)

    def _fun(self):
        try:
            assert using_serialization()
            with use_serialization():
                assert using_serialization()
                self.serialization_explicitly_enabled = True
                while not self.should_stop:
                    time.sleep(0.1)
        except Exception as e:
            self.exception = e
        finally:
            self.finished = True
            self.should_stop = True
            self.serialization_explicitly_enabled = True
