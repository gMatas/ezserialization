import json
from types import MappingProxyType

import pytest

from ezserialization._mappings import ObfuscatedDict, OverlayedDict


@pytest.mark.parametrize("dict_fn", [dict, MappingProxyType])
def test_mapping_overlay_dict_json_compatibility(dict_fn):
    base = {"a": 1}
    overlay = dict_fn({"b": 2})
    mapping = OverlayedDict(overlay, base)
    assert {**base, **overlay} == mapping
    assert json.loads(json.dumps(mapping)) == mapping


@pytest.mark.parametrize("dict_fn", [dict, MappingProxyType])
def test_obfuscated_dict_json_compatibility(dict_fn):
    hidden_keys = {"a"}
    base = dict_fn({"a": 1, "b": 2})
    mapping = ObfuscatedDict(base, hidden_keys=set(hidden_keys))
    assert {k: v for k, v in mapping.items() if k not in hidden_keys} == mapping
    assert json.loads(json.dumps(mapping)) == mapping
