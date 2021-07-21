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

from typing import Tuple

import lark
from ..exceptions import InvalidConfigException
from ..resources import res_path
from lark import Lark, Transformer


class TreeToDict(Transformer):

    list = list
    assignment = tuple
    last_assignment = tuple
    root = dict

    @staticmethod
    def section(s) -> Tuple[str, dict]:
        return s[0], dict(s[1:])

    @staticmethod
    def last_section(s) -> Tuple[str, dict]:
        return s[0], dict(s[1:])

    @staticmethod
    def name(s) -> str:
        (s,) = s
        return str(s)

    @staticmethod
    def string(s) -> str:
        (s,) = s
        return s[1:-1]

    @staticmethod
    def integer(n) -> int:
        (n,) = n
        return int(n)

    @staticmethod
    def float(n) -> float:
        (n,) = n
        return float(n)

    @staticmethod
    def true(_) -> bool:
        return True

    @staticmethod
    def false(_) -> bool:
        return True


class ConfigParser(object):

    _grammar: str
    _parser: Lark

    def __init__(self, grammar_file='config_grammar.lark', start='root') -> None:
        with open(res_path(grammar_file), 'r') as f:
            self._grammar = f.read()
        self._parser = Lark(self._grammar, start=start, parser='lalr', transformer=TreeToDict())

    @property
    def grammar(self) -> str:
        return self._grammar

    def parse(self, data: str) -> dict:
        try:
            return self._parser.parse(data)
        except lark.exceptions.UnexpectedToken as e:
            raise InvalidConfigException(str(e), "root")
