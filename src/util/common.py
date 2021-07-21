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

import importlib
import shlex
from typing import Any, List, Optional

import discord

_module_cache = {}


def get_module_element(path: str) -> Any:
    split_path = path.split('.')
    module_name = '.'.join(split_path[:-1])
    object_name = split_path[-1]
    if module_name not in _module_cache:
        _module_cache[module_name] = importlib.import_module(module_name)
    module = _module_cache[module_name]
    return getattr(module, object_name)


def dict_fancy_table(values: dict, key_name='name') -> str:
    if not values:
        return '++\n' * 2

    col0 = [key_name] + list(values.keys())
    row_count = len(col0)
    col_names = list(values[col0[-1]].keys())

    def to_col(k):
        return [k] + [values[v][k] for v in values]

    def col_width(col):
        return max(len(str(v)) for v in col)

    table = [col0] + [to_col(k) for k in col_names]
    cols_width = [col_width(col) for col in table]
    cols_format = [f'{{:{w}}}' for w in cols_width]
    separator = '+-' + '-+-'.join(['-' * w for w in cols_width]) + '-+\n'

    def str_row_values(i):
        return [cols_format[j].format(col[i]) for (j, col) in enumerate(table)]

    def format_line(i):
        return '| ' + ' | '.join(str_row_values(i)) + ' |\n'

    lines = [format_line(i) for i in range(row_count)]
    return separator + separator.join(lines) + separator


def pretty_days(days: int) -> str:
    if days == 0:
        return '0 days'

    def _s(x: int) -> str:
        return '' if (x % 10) == 1 and x != 11 else 's'

    res = ''
    years = days // 365
    if years > 0:
        res += f'{years} year{_s(years)} '
        days %= 365
    months = days // 30
    if months > 0:
        res += f'{months} month{_s(months)} '
        days %= 30
    if days > 0:
        res += f'{days} day{_s(days)} '

    return res.strip()


def pretty_seconds(seconds: int) -> str:
    if seconds == 0:
        return '0 seconds'

    def _s(x: int) -> str:
        return '' if (x % 10) == 1 and x != 11 else 's'

    res = ''
    days = seconds // 86400
    if days > 0:
        seconds %= 86400
        res += pretty_days(days) + ' '
    hours = seconds // 3600
    if hours > 0:
        res += f'{hours} hour{_s(hours)} '
        seconds %= 3600
    minutes = seconds // 60
    if minutes > 0:
        res += f'{minutes} min{_s(minutes)} '
        seconds %= 60
    if seconds > 0:
        res += f'{seconds} second{_s(seconds)} '
    return res.strip()


def parse_control_message(prefix: str, message: discord.Message) -> Optional[List[str]]:
    prefix_len = len(prefix)
    msg = message.content.strip()

    msg_prefix = msg[: prefix_len]
    msg_suffix = msg[prefix_len:]

    if msg_prefix != prefix or msg_suffix == "":
        return None

    lines = [line.strip() for line in msg_suffix.splitlines()]
    res = shlex.split(lines[0])
    lines = lines[1:]
    merging = False
    merging_val = ''
    for line in lines:
        if line[:2] == '> ':
            if merging:
                merging_val += '\n' + line[2:]
            else:
                merging = True
                merging_val = line[2:]
            continue
        elif merging:
            res.append(merging_val)
            merging = False
            merging_val = ''
        res += shlex.split(line)
    if merging:
        res.append(merging_val)

    return res


def limit_traceback(traceback: List[str], from_file: str, offset: int) -> List[str]:
    res = []
    found = False
    effective_offset = 0
    for line in traceback:
        if not found and from_file in line and line.strip().startswith("File"):
            found = True
            res.append(line)
        elif found and line.strip().startswith("File"):
            effective_offset += 1
        if found and effective_offset < offset:
            res.append(line)
    return res


def _format_messages(m):
    return f'{m} messages'


def _format_reactions(m):
    return f'{m} reactions'


def _format_default(m):
    return str(m)


FORMATTERS = {
    "membership": pretty_days,
    "new_message_count": _format_messages,
    "delete_message_count": _format_messages,
    "edit_message_count": _format_messages,
    "new_reaction_count": _format_reactions,
    "delete_reaction_count": _format_reactions,
    "vc_time": pretty_seconds,
    "min_weight": _format_default,
    "max_weight": _format_default,
    "exact_weight": _format_default,
    "weight": _format_default,
    "messages": _format_default,
    "vc": pretty_seconds
}
