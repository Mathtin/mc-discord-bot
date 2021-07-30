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

import asyncio
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Awaitable, Optional, Union, Tuple

import discord

from .common import pretty_seconds
from .exceptions import InvalidConfigException, NotCoroutineException
from .resources import STRINGS as R


##################################
# Bot control coroutine wrappers #
##################################

def check_coroutine(func) -> None:
    if not asyncio.iscoroutinefunction(func):
        raise NotCoroutineException(func)


def get_coroutine_attrs(obj: Any, filter_=lambda x: True, name_filter=lambda x: True) -> \
        Dict[str, Callable[..., Awaitable[Any]]]:
    attrs = {attr: getattr(obj, attr) for attr in dir(obj) if name_filter(attr)}
    return {name: f for name, f in attrs.items() if asyncio.iscoroutinefunction(f) and filter_(f)}


def get_loop_attrs(obj: Any, filter_=lambda x: True, name_filter=lambda x: True) -> List[asyncio.AbstractEventLoop]:
    attrs = [getattr(obj, attr) for attr in dir(obj) if name_filter(attr)]
    return [loop for loop in attrs if isinstance(loop, asyncio.AbstractEventLoop) and filter_(loop)]


######################
# Utility decorators #
######################

def after_initialized(func):
    async def _func(self, *args, **kwargs):
        await self.init_lock()
        return await func(self, *args, **kwargs)

    return _func


def skip_bots(func):
    async def _func(self, obj, *args, **kwargs):
        if isinstance(obj, discord.User) or isinstance(obj, discord.Member):
            if obj.bot:
                return
        elif isinstance(obj, discord.Message):
            if obj.author.bot:
                return
        return await func(self, obj, *args, **kwargs)

    return _func


def guild_member_event(func):
    async def _func(self, obj, *args, **kwargs):
        if isinstance(obj, discord.Member):
            if not self.is_guild_member(obj):
                return
        elif isinstance(obj, discord.Message):
            if not self.is_guild_member_message(obj):
                return
        return await func(self, obj, *args, **kwargs)

    return _func


###########################
# Bot model utility funcs #
###########################

def is_user_member(user: discord.User) -> bool:
    return isinstance(user, discord.Member)


def qualified_name(user: Union[discord.User, discord.Member]) -> str:
    return f'{user.name}#{user.discriminator}'


def quote_msg(msg: str) -> str:
    return '\n'.join([f'> {line}' for line in msg.replace("`", "\\`").splitlines()])


def code_msg(msg: str) -> str:
    return '\n'.join([f'`{line}`' for line in msg.replace("`", "\\`").splitlines()])


def get_channel_env_var_name(n) -> str:
    return f'DISCORD_CHANNEL_{n}'


def get_channel_id(n) -> Optional[int]:
    var_name = get_channel_env_var_name(n)
    try:
        res = os.environ.get(var_name)
        return int(res) if res is not None else None
    except ValueError as e:
        raise InvalidConfigException(str(e), var_name)


def is_text_channel(channel) -> bool:
    return channel.type == discord.ChannelType.text


def is_dm_message(message: discord.Message) -> bool:
    return isinstance(message.channel, discord.DMChannel)


def is_same_author(m1: discord.Message, m2: discord.Message) -> bool:
    return m1.author.id == m2.author.id


def is_role_applied(user: discord.Member, role: Union[discord.Role, str]) -> bool:
    if isinstance(role, discord.Role):
        return is_role_applied(user, role.name)
    for r in user.roles:
        if r.name == role:
            return True
    return False


def filter_roles(user: discord.Member, roles_filter: List[Union[discord.Role, str]]) -> List[Union[discord.Role, str]]:
    res = []
    for r in roles_filter:
        if is_role_applied(user, r):
            res.append(r)
    return res


async def send_long_line(channel: discord.TextChannel, line: str):
    chunk = 2000
    parts = [line[i:i + chunk] for i in range(0, len(line), chunk)]
    for part in parts:
        await channel.send(part)


async def send_long_message(channel: discord.TextChannel, message: str):
    lines = message.splitlines()
    cur = ''
    for line in lines:
        if not cur:
            if len(line) > 2000:
                await send_long_line(channel, line)
            else:
                cur = line
        else:  # if something in cur
            if len(line) > 2000:
                await channel.send(cur)
                cur = ''
                await send_long_line(channel, line)
            elif len(cur) + len(line) < 2000:
                cur += '\n' + line
            else:  # if len(cur) + len(line) > 2000
                await channel.send(cur)
                cur = line
    if cur:
        await channel.send(cur)


SEP = '-------------------------------------------------------------------------------------------------'


def embed_long_line(embed: discord.Embed, line: str) -> None:
    chunk = 1000
    parts = [line[i:i + chunk] for i in range(0, len(line), chunk)]
    for part in parts:
        embed.add_field(name=SEP, value=part, inline=False)


def embed_long_message(embed: discord.Embed, message: str) -> None:
    message = message[:5000]
    if len(message) <= 2000:
        embed.description = message
        return
    f_p = message[:2000]
    i = f_p.rfind('\n')
    if i == -1:
        message = message[2000:]
    else:
        f_p = message[:i]
        message = message[i + 1:]
    embed.description = f_p
    lines = message.splitlines()
    cur = ''
    for line in lines:
        if not cur:
            if len(line) > 1000:
                embed_long_line(embed, line)
            else:
                cur = line
        else:  # if something in cur
            if len(line) > 1000:
                embed.add_field(name=SEP, value=cur, inline=False)
                cur = ''
                embed_long_line(embed, line)
            elif len(cur) + len(line) < 1000:
                cur += '\n' + line
            else:  # if len(cur) + len(line) > 1000
                embed.add_field(name=SEP, value=cur, inline=False)
                cur = line
    if cur:
        embed.add_field(name=SEP, value=cur, inline=False)


class ProgressEmbed(object):

    NOT_STARTED = 0
    IN_PROGRESS = 1
    FINISHED = 2
    SKIPPED = 3
    FAILED = -1

    _embed: discord.Embed
    _msg: Optional[discord.Message]
    _date: Optional[datetime]
    _steps: List[List[Tuple[str, int]]]
    _current_step: int
    _name: str
    _state: int

    def __init__(self, name: str, base: discord.Embed) -> None:
        self._embed = base
        self._name = name
        self._msg = None
        self._date = None
        self._steps = []
        self._current_step = 0
        self._state = ProgressEmbed.NOT_STARTED

    def _format_embed(self) -> None:
        self._embed.title = self._format_step(self._name, self._state)
        self._embed.description = '\n'.join(['\n'.join(self._format_step(*s) for s in step) for step in self._steps])
        elapsed = int((datetime.now() - self._date).total_seconds())
        self._embed.description += f'\n\n{R.NAME.COMMON.STATE}: **{self.state}**\n'
        self._embed.description += f'{R.MESSAGE.STATUS.ELAPSED}: {pretty_seconds(elapsed)}'

    def _set_step_status(self, i: int, status: int):
        self._steps[i] = [(n, status) for n, _ in self._steps[i]]

    def _next_step(self, status: int) -> None:
        if self._current_step >= len(self._steps):
            raise ValueError("No more steps")
        self._set_step_status(self._current_step, status)
        self._current_step += 1
        if self._current_step < len(self._steps):
            self._set_step_status(self._current_step, ProgressEmbed.IN_PROGRESS)

    def add_step(self, names: Union[str, List[str]]) -> None:
        if isinstance(names, str):
            return self.add_step([names])
        self._steps.append([(name, ProgressEmbed.NOT_STARTED) for name in names])

    async def start(self, channel: discord.TextChannel) -> None:
        if not self._steps:
            raise ValueError("No steps provided")
        self._date = datetime.now()
        self._current_step = 0
        self._state = ProgressEmbed.IN_PROGRESS
        self._format_embed()
        self._set_step_status(0, ProgressEmbed.IN_PROGRESS)
        self._msg = await channel.send(embed=self._embed)

    async def update(self) -> None:
        if self._msg is None:
            raise RuntimeError("Call to start() is missing")
        self._format_embed()
        await self._msg.edit(embed=self._embed)

    async def skip_step(self, update: bool = False) -> None:
        self._next_step(ProgressEmbed.SKIPPED)
        if update:
            await self.update()

    async def next_step(self, failed: bool = False, update: bool = True) -> None:
        self._next_step(ProgressEmbed.FINISHED if not failed else ProgressEmbed.FAILED)
        if update:
            await self.update()

    async def finish(self, failed: bool = False, update: bool = True) -> None:
        self._state = ProgressEmbed.FINISHED if not failed else ProgressEmbed.FAILED
        self._set_step_status(self._current_step, self._state)
        for step in range(self._current_step + 1, len(self._steps)):
            self._set_step_status(step, ProgressEmbed.SKIPPED)
        if update:
            await self.update()

    @property
    def state(self) -> str:
        if self._state == ProgressEmbed.NOT_STARTED:
            return R.MESSAGE.STATE.NOT_STARTED
        elif self._state == ProgressEmbed.IN_PROGRESS:
            return R.MESSAGE.STATE.IN_PROGRESS
        elif self._state == ProgressEmbed.FINISHED:
            return R.MESSAGE.STATE.FINISHED
        elif self._state == ProgressEmbed.SKIPPED:
            return R.MESSAGE.STATE.SKIPPED
        elif self._state == ProgressEmbed.FAILED:
            return R.MESSAGE.STATE.FAILED
        return R.MESSAGE.STATE.UNKNOWN

    @staticmethod
    def _format_step(name: str, status: int):
        if status == ProgressEmbed.NOT_STARTED:
            return f'⚪ {name}'
        elif status == ProgressEmbed.IN_PROGRESS:
            return f'🔄 {name}'
        elif status == ProgressEmbed.FINISHED:
            return f'✅ {name}'
        elif status == ProgressEmbed.SKIPPED:
            return f'✖ {name}'
        elif status == ProgressEmbed.FAILED:
            return f'❌ {name}'
        return f'❔ {name}'
