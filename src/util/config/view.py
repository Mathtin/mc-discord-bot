#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MIT License

Copyright (c) 2021-present Daniel [Mathtin] Shiko <wdaniil@mail.ru>
Project: Minecraft Discord Bot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

__author__ = "Mathtin"

import typing

from ..exceptions import InvalidConfigException
from typing import Any, Callable, Dict, Type, get_type_hints


class ConfigView(object):
    # Class fields
    _type_constructor_map: Dict[Type[Any], Callable[[Any, str], Any]] = {
        int: lambda v, p: int(v),
        float: lambda v, p: float(v),
        bool: lambda v, p: bool(v),
        str: lambda v, p: str(v),
        list: lambda v, p: list(v),
        dict: lambda v, p: dict(v),
    }
    _field_constructor_map: Dict[str, Callable[[Any, str], Any]] = None

    # Instance fields
    _path_prefix: str

    def __init__(self, values: typing.Optional[Dict[str, Any]] = None, path_prefix: str = '') -> None:
        if values is None:
            values = {}
        self._path_prefix = path_prefix
        # Build {_field_constructor_map} for each class implementation
        if self._field_constructor_map is None:
            types = get_type_hints(self.__class__)
            self.__class__._field_constructor_map = {
                field: self.get_type_constructor(type_)
                for field, type_ in types.items()
                if not field.startswith('_')
            }
        # Construct each field value provided by {values}
        for key, value in values.items():
            if key not in self._field_constructor_map:
                raise InvalidConfigException(f"Invalid key: {key}", self.path(key))
            if value is not None:
                constructor = self._field_constructor_map[key]
                field_value = constructor(value, self.path(key))
                setattr(self, key, field_value)

    def get_type_constructor(self, type_: Type[Any]) -> Callable[[Any, str], Any]:
        if type_ not in self._type_constructor_map:
            self._type_constructor_map[type_] = self._resolve_constructor(type_)
        return self._type_constructor_map[type_]

    def _resolve_constructor(self, type_: Type[Any]) -> Callable[[Any, str], Any]:
        # Primitive types already exist, only ConfigView and complex List/Dict type-hints are supported
        if isinstance(type_, typing._GenericAlias):
            # Resolve complex List type-hint
            if type_._name == 'List':
                sub_constructor = self.get_type_constructor(type_.__args__[0])
                return lambda l, p: [sub_constructor(e, f'{p}[{i}]') for i, e in enumerate(l)]
            # Resolve complex Dict type-hint
            elif type_._name == 'Dict':
                # Check key type
                if type_.__args__[0] is not str:
                    raise TypeError(f"Unsupported dict key type hint: {type_.__args__[0]}")
                sub_constructor = self.get_type_constructor(type_.__args__[1])
                return lambda d, p: {k: sub_constructor(v, f'{p}.{k}') for k, v in d.items()}
            # Other type-hints are not supported
            raise TypeError(f"Unsupported type hint: {type_}")
        # ConfigView are constructor-ready
        if issubclass(type_, ConfigView):
            return type_
        raise TypeError(f"Unsupported type: {type_}")

    def path(self, sub_path: str) -> str:
        return f'{self._path_prefix}.{sub_path}' if self._path_prefix else sub_path

    def get(self, path: str) -> Any:
        if path == '.':
            return self
        parts = path.split('.')
        node = self
        for part in parts:
            if not hasattr(node, part):
                raise KeyError(f"Invalid path: {path}")
            node = getattr(node, part)
        return node

    def to_dict(self) -> dict:
        res = {}
        for field in self._field_constructor_map:
            value = getattr(self, field)
            res[field] = self.deconstruct_obj(value)
        return res

    @staticmethod
    def deconstruct_obj(o: Any) -> Any:
        if isinstance(o, ConfigView):
            return o.to_dict()
        elif isinstance(o, list):
            return [ConfigView.deconstruct_obj(v) for v in o]
        elif isinstance(o, dict):
            return {k: ConfigView.deconstruct_obj(v) for k, v in o.items()}
        return o

    def __iter__(self):
        for field in self._field_constructor_map:
            yield field, getattr(self, field)
