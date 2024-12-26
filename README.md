# EzSerialization

[![PyPI](https://img.shields.io/pypi/v/ezserialization)](https://pypi.org/project/ezserialization)

**ezserialization** - Simple, easy to use & transparent python objects serialization & deserialization.

## Install

Simply install from PyPI via
```sh 
pip install ezserialization
```

## Usage

To use this package:
- simply implement `Serializable` protocol for your classes by having defined `to_dict()` and 
`from_dict()` methods;
- decorate your classes with `@serializable`.

During serialization, simply use your `to_dict` method, and it will return 
your defined dict `{'some_value': 'wow', ...}` wrapped inside a wrapper 
dict `{'_type_': 'example.module.Example', 'some_value': 'wow', ...}`.

During de-serialization (via `deserialize()` method) the wrapped dict's `_type_` property will be removed and used 
to import `example.module` module dynamically. Finally, the found `Example` class' `from_dict` method will be used 
to create new object from the non-wrapped dict.

Here's an example:

```python
from pprint import pprint
from typing import Mapping
from ezserialization import serializable, deserialize

@serializable
class Example:
    def __init__(self, value: str):
        self.value = value

    def to_dict(self) -> dict:
        return {"some_value": self.value}

    @classmethod
    def from_dict(cls, src: Mapping):
        return cls(value=src["some_value"])


obj = Example("wow")
obj_dict = obj.to_dict()

pprint(obj_dict, indent=2)
# Output:
# {'_type_': '__main__.Example', 'some_values': 'wow'}

obj2 = deserialize(obj_dict)

print(obj.value == obj2.value)
# Output:
# True
```