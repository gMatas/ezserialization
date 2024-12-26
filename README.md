# EzSerialization

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI](https://img.shields.io/pypi/v/ezserialization?style=flat)](https://pypi.org/project/ezserialization)
[![License](https://img.shields.io/pypi/l/ezserialization)](https://github.com/gMatas/ezserialization/blob/main/LICENSE)

**ezserialization** - Simple, easy to use & transparent python objects serialization & deserialization.

## About

EzSerialization is meant to be simple in features and usage. It follows these three ideas:

- **python dicts based**. This package only helps to serialize objects to dicts. 
  Converting them to JSON, XML, etc. is left to the user;
- **transparent serialization logic**. It does not have automatic `from_dict` & `to_dict` methods that convert class 
  instances of any kind to dicts. Implementing them is left to the end-user, thus being transparent with what actually 
  happens with the user data;

## Install

Simply install from PyPI via pip command:
```sh
pip install ezserialization
```

Or use Poetry:
```sh
poetry install
```

## Usage

To use this package:

- simply implement `Serializable` protocol for your classes by having defined `to_dict()` and 
  `from_dict()` methods;
- decorate your classes with `@serializable`.

During serialization, simply use your implemented `to_dict` method, and it will return 
your defined dict `{'some_value': 'wow', ...}` placed inside a wrapper 
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

## Configuration

Currently only a single option is available for customizing `ezserialization`:
- `ezserialization.TYPE_FIELD_NAME` - By default it is set to `_type_`, however if user's solution has `to_dict()` 
  methods that already contains such field, an alternative field name can be set to override the default one.