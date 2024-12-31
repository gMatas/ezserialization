import itertools
from abc import abstractmethod
from collections.abc import MutableMapping
from typing import Generic, Hashable, Mapping, TypeVar, Union

__all__ = [
    "OverlayedDict",
    "ObfuscatedDict",
]

_OM = TypeVar("_OM", bound=Union[Mapping, MutableMapping])
_BM = TypeVar("_BM", bound=Union[Mapping, MutableMapping])


class MappingOverlayMixin(MutableMapping, Generic[_OM, _BM]):
    def __setitem__(self, key, value, /):
        for mapping in self.inner_mappings:
            if key in mapping:
                mapping[key] = value
                return
        self.inner_mappings[1][key] = value

    def __delitem__(self, key, /):
        for mapping in self.inner_mappings:
            if key in mapping:
                del mapping[key]
                return
        del self.inner_mappings[1][key]

    def __getitem__(self, key, /):
        for mapping in self.inner_mappings:
            if key in mapping:
                return mapping[key]
        raise KeyError(key)

    def __len__(self):
        return len(self.inner_mappings[0]) + len(self.inner_mappings[1])

    def __iter__(self):
        return itertools.chain(*self.inner_mappings)

    @property
    @abstractmethod
    def inner_mappings(self) -> tuple[_OM, _BM]:
        pass

    def set_overlay_item(self, key, value):
        if key in self.inner_mappings[1]:
            raise KeyError(f"Key {key} is already present at base mapping!")
        self.inner_mappings[0][key] = value

    def get_overlay_item(self, key):
        return self.inner_mappings[0][key]


class OverlayedDict(MappingOverlayMixin[_OM, _BM], dict):
    def __init__(self, overlay: _OM, base: _BM):
        self._maps = (overlay, base)
        super().__init__({"overlay": overlay, "base": base})

    @property
    def inner_mappings(self) -> tuple[_OM, _BM]:
        return self._maps


_M = TypeVar("_M", bound=Union[Mapping, MutableMapping])


class ObfuscatedMappingMixin(MutableMapping, Generic[_M]):
    def __setitem__(self, key, value, /):
        self.unhide_key(key)
        self.inner_mapping[key] = value

    def __delitem__(self, key, /):
        if self.key_is_hidden(key):
            raise KeyError(f"Key {key} is hidden!")
        del self.inner_mapping[key]

    def __getitem__(self, key, /):
        if self.key_is_hidden(key):
            raise KeyError(f"Key {key} is hidden!")
        return self.inner_mapping[key]

    def __len__(self):
        return len(tuple(iter(self)))

    def __iter__(self):
        return (key for key in self.inner_mapping if not self.key_is_hidden(key))

    @property
    @abstractmethod
    def inner_mapping(self) -> _M:
        pass

    @abstractmethod
    def hide_key(self, key: Hashable) -> None:
        pass

    @abstractmethod
    def key_is_hidden(self, key: Hashable) -> bool:
        pass

    @abstractmethod
    def unhide_key(self, key: Hashable) -> None:
        pass


class ObfuscatedDict(ObfuscatedMappingMixin[_M], dict):
    def __init__(self, mapping: _M, hidden_keys: set[Hashable]):
        self._mapping = mapping
        self._hidden_keys = hidden_keys
        super().__init__({"mapping": mapping, "hidden_keys": hidden_keys})

    @property
    def inner_mapping(self) -> _M:
        return self._mapping

    def hide_key(self, key: Hashable) -> None:
        self._hidden_keys.add(key)

    def key_is_hidden(self, key: Hashable) -> bool:
        return key in self._hidden_keys

    def unhide_key(self, key: Hashable) -> None:
        self._hidden_keys.discard(key)
