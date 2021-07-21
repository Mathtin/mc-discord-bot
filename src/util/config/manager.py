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

import json
import typing
from typing import Any, Dict, Optional, Type, get_type_hints

from .parser import ConfigParser
from .view import ConfigView


class ConfigManager(object):
    path: str
    raw: str
    raw_dict: dict
    config: ConfigView
    parser: ConfigParser
    model = None

    _section_model_cache: Dict[Type[ConfigView], Dict[Type[ConfigView], str]] = {}

    def __init__(self, path: str, parser: ConfigParser = None) -> None:
        if parser is None:
            parser = ConfigParser()
        if self.model is None:
            self.__class__.model = get_type_hints(self.__class__)['config']
        self.path = path
        self.parser = parser
        self.reload()

    def reload(self) -> None:
        with open(self.path, 'r') as f:
            raw = f.read()
        self.alter(raw)

    def save(self) -> None:
        self.sync()
        with open(self.path, 'w') as f:
            f.write(self.raw)

    def alter(self, raw: str) -> None:
        self.raw = raw
        self.raw_dict = self.parser.parse(self.raw)
        self.config = self.model(self.raw_dict)

    def sync(self) -> None:
        raw_dict = self.config.to_dict()
        raw = self.serialize_obj(raw_dict)
        self.alter(raw)

    def get_raw(self, path: str) -> str:
        value = self.config.get(path)
        value_prim = ConfigView.deconstruct_obj(value)
        return ConfigManager.serialize_obj(value_prim)

    def set_raw(self, path: str, assignment: str) -> None:
        value_dict = self.parser.parse(assignment)
        # Set root
        if path == '.':
            self._merge_dict(self.raw_dict, value_dict)
            return self._explode_raw_dict()
        # Resolve path node
        parts = path.split('.')
        node = self.raw_dict
        for part in parts:
            if part not in node:
                raise KeyError(f"Invalid path: {path}")
            node = node[part]
        # Update
        self._merge_dict(node, value_dict)
        self._explode_raw_dict()

    @staticmethod
    def _merge_dict(d1, d2):
        for k in d2:
            d1[k] = d2[k]

    def _explode_raw_dict(self) -> None:
        raw = self.serialize_obj(self.raw_dict)
        self.alter(raw)

    def section_path(self, element: Type[ConfigView], source: Type[ConfigView]) -> Optional[str]:
        if source not in self._section_model_cache:
            self._section_model_cache[source] = {source: '.'}
        cache = self._section_model_cache[source]
        if element in cache:
            return cache[element]
        res = None
        types = get_type_hints(source)
        for field, type_ in types.items():
            if field.startswith('_') or \
                    isinstance(type_, typing._GenericAlias) or \
                    not issubclass(type_, ConfigView):
                continue
            path = self.section_path(element, type_)
            if path is not None:
                res = f'{field}.{path}' if path != '.' else field
                break
        cache[element] = res
        return res

    def find_section(self, model: Type[ConfigView]) -> Any:
        path = self.section_path(model, self.config.__class__)
        return self.config.get(path)

    @staticmethod
    def serialize_obj(obj: Any) -> str:
        if isinstance(obj, dict):
            res = []
            for k, v in obj.items():
                if isinstance(v, dict):
                    section_lines = ConfigManager.serialize_obj(v).splitlines()
                    section_lines_indented = [f'    {line}\n' for line in section_lines]
                    res.append(f'{k} {{\n' + ''.join(section_lines_indented) + '}\n')
                elif isinstance(v, list):
                    values = [ConfigManager.serialize_obj(a) for a in v]
                    values_str = ', '.join(values)
                    res.append(f'{k} = [{values_str}]\n')
                else:
                    res.append(f'{k} = {ConfigManager.serialize_obj(v)}\n')
            return ''.join(res)
        elif isinstance(obj, str):
            return '"' + obj.replace('"', '\\"') + '"'
        else:
            return json.dumps(obj)
