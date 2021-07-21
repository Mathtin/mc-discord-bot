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

from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, get_type_hints

import discord as DIS
from discord.errors import InvalidArgument

import db as DB
from util.extbot import check_coroutine
from util.resources import STRINGS as R
from .types import OverlordMember, IOverlordCommand, IBotExtension

_type_arg_converter_map: Dict[Type[Any], Callable[[DIS.Message, IBotExtension, str], Awaitable[Optional[str]]]] = {}


class SaveFor(object):
    def __init__(self, type_) -> None:
        self.type = type_

    def __call__(self, func: Callable[[DIS.Message, IBotExtension, str], Awaitable[Optional[str]]]) -> \
            Callable[[DIS.Message, IBotExtension, str], Awaitable[Optional[str]]]:
        _type_arg_converter_map[self.type] = func
        return func


class OverlordCommand(IOverlordCommand):

    _req_f_args: List[str]
    _f_args: List[str]
    _hints: Dict[str, Type[Any]]
    _args_str: str

    def __init__(self, func, name: str, description='') -> None:
        super().__init__()
        check_coroutine(func)
        self.func = func
        self.name = name
        self.description = description
        f_args = func.__code__.co_varnames[:func.__code__.co_argcount]
        assert len(f_args) >= 2
        self._f_args = f_args[2:]
        self._hints = {k: v for k, v in get_type_hints(func).items() if k in self._f_args}
        self._req_f_args = []
        args = []
        optionals = False
        for a in self._f_args:
            arg = a
            if a in self._hints:
                arg += f': {self._hints[a].__name__}'
            if not a.lower().startswith(self.optional_prefix):
                self._req_f_args.append(a)
                args.append(f'{{{arg}}}')
            elif optionals:
                raise InvalidArgument(
                    f'Non-optional argument {a} found after optional argument in {name} command coroutine')
            else:
                optionals = True
                args.append(f'[{arg[len(self.optional_prefix):]}]')
        self._args_str = ' '.join(args)

    def usage(self, prefix: str, cmd_name: str) -> str:
        return f'{prefix}{cmd_name} {self._args_str}'

    def help(self, prefix: str, aliases: List[str]) -> str:
        if not aliases:
            return 'This command is disabled. Please, add appropriate config'
        usage_line = f'Usage: `{prefix}{aliases[0]} {self._args_str}`' if self._args_str \
            else f'Usage: `{prefix}{aliases[0]}`'
        description_line = f'{self.description}'
        aliases_str = ', '.join([f'`{prefix}{a}`' for a in aliases[1:]])
        aliases_line = f'Aliases: {aliases_str}'
        return '\n'.join([usage_line, description_line, aliases_line])

    def handler(self, ext: IBotExtension):
        async def wrapped_func(message: DIS.Message, prefix: str, argv: List[str]):
            cmd = argv[0]
            argv = argv[1:]
            if len(self._req_f_args) > len(argv) or len(argv) > len(self._f_args):
                usage_str = 'Usage: ' + self.usage(prefix, cmd)
                await message.channel.send(usage_str)
                return
            argv = await self._convert_argv(message, ext, argv)
            if argv is None:
                usage_str = 'Usage: ' + self.usage(prefix, cmd)
                await message.channel.send(usage_str)
                return
            await ext.run_handler(self.func, ext, message, *argv)
        return wrapped_func

    async def _convert_argv(self, msg: DIS.Message, ext: Any, argv: List[str]) -> Optional[List[Any]]:
        res = [a for a in argv]
        for i in range(len(res)):
            name = self._f_args[i]
            if name in self._hints:
                arg = await self._convert_arg(msg, ext, name, res[i], self._hints[name])
                if arg is None:
                    return None
                res[i] = arg
        return res

    @staticmethod
    async def _convert_arg(msg: DIS.Message, ext: IBotExtension, name: str, arg: str, type_: Type[Any]) \
            -> Optional[Any]:
        if type_ in _type_arg_converter_map:
            return await _type_arg_converter_map[type_](msg, ext, arg)
        try:
            return type_(arg)
        except ValueError:
            await msg.channel.send(f'{R.MESSAGE.ERROR.INVALID_ARGUMENT} "{name}" -> {type_.__name__}')

    @staticmethod
    @SaveFor(DB.User)
    async def _resolve_db_user_w_fb(fb: DIS.Message, ext: IBotExtension, user_mention: str) -> Optional[DB.User]:
        user = await ext.bot.resolve_user(user_mention)
        if user is None:
            await fb.channel.send(R.MESSAGE.DB_ERROR.UNKNOWN_USER)
            return None
        return user

    @staticmethod
    @SaveFor(DIS.User)
    async def _resolve_user_w_fb(fb: DIS.Message, ext: IBotExtension, user_mention: str) -> Optional[DIS.User]:
        user = await OverlordCommand._resolve_db_user_w_fb(fb, ext, user_mention)
        if user is None:
            return None
        try:
            d_user = await ext.bot.fetch_user(user.did)
        except DIS.NotFound:
            await fb.channel.send(R.MESSAGE.D_ERROR.UNKNOWN_USER)
            return None
        return d_user

    @staticmethod
    @SaveFor(DIS.Member)
    async def _resolve_member_w_fb(fb: DIS.Message, ext: IBotExtension, user_mention: str) -> Optional[DIS.Member]:
        user = await OverlordCommand._resolve_user_w_fb(fb, ext, user_mention)
        if user is None:
            return None
        try:
            member = await ext.bot.guild.fetch_member(user.id)
        except DIS.NotFound:
            await fb.channel.send(R.MESSAGE.D_ERROR.USER_NOT_MEMBER)
            return None
        return member

    @staticmethod
    @SaveFor(DIS.TextChannel)
    async def _resolve_text_channel_w_fb(fb: DIS.Message, ext: IBotExtension, channel_mention: str) -> \
            Optional[DIS.TextChannel]:
        channel = await ext.bot.resolve_text_channel(channel_mention)
        if channel is None:
            if await ext.bot.resolve_voice_channel(channel_mention) is not None:
                await fb.channel.send(R.MESSAGE.D_ERROR.CHANNEL_NOT_TEXT)
            else:
                await fb.channel.send(R.MESSAGE.D_ERROR.UNKNOWN_CHANNEL)
            return None
        return channel

    @staticmethod
    @SaveFor(DIS.VoiceChannel)
    async def _resolve_voice_channel_w_fb(fb: DIS.Message, ext: IBotExtension, channel_mention: str) -> \
            Optional[DIS.VoiceChannel]:
        channel = await ext.bot.resolve_voice_channel(channel_mention)
        if channel is None:
            if await ext.bot.resolve_text_channel(channel_mention) is not None:
                await fb.channel.send(R.MESSAGE.D_ERROR.CHANNEL_NOT_VOICE)
            else:
                await fb.channel.send(R.MESSAGE.D_ERROR.UNKNOWN_CHANNEL)
            return None
        return channel

    @staticmethod
    @SaveFor(DIS.Role)
    async def _resolve_role_w_fb(fb: DIS.Message, ext: IBotExtension, role_name: str) -> Optional[DIS.Role]:
        role = ext.bot.get_role(role_name)
        if role is None:
            await fb.channel.send(R.MESSAGE.D_ERROR.UNKNOWN_ROLE)
            return None
        return role

    @staticmethod
    @SaveFor(OverlordMember)
    async def _resolve_ov_member_w_fb(fb: DIS.Message, ext: IBotExtension, user_mention: str) -> \
            Optional[OverlordMember]:
        user = await OverlordCommand._resolve_db_user_w_fb(fb, ext, user_mention)
        if user is None:
            return None
        try:
            member = await ext.bot.guild.fetch_member(user.did)
        except DIS.NotFound:
            await fb.channel.send(R.MESSAGE.D_ERROR.USER_NOT_MEMBER)
            return None
        return OverlordMember(member, user)
