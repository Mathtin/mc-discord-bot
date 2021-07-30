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
import logging
import sys
import traceback
from typing import Dict, List, Optional, Callable, Awaitable

import discord
from discord.errors import InvalidArgument
from discord.ext.tasks import Loop

from overlord.bot import Overlord
from overlord.task import OverlordTask
from overlord.command import OverlordCommand
from overlord.types import IBotExtension
from util.exceptions import InvalidConfigException
from util.extbot import ProgressEmbed, get_coroutine_attrs
from util.resources import STRINGS as R

log = logging.getLogger('overlord-extension')


############################
# Bot Extension Base Class #
############################

class BotExtension(IBotExtension):

    __priority__ = 0
    __extname__ = 'Base Extension'
    __description__ = 'Base bot extension class'
    __color__ = 0x7B838A

    _skip_init_lock = ['on_config_update', 'on_ready', 'on_error']

    # Members passed via constructor
    _bot: Overlord

    # State members
    _enabled: bool
    _tasks: List[OverlordTask]
    _commands: Dict[str, OverlordCommand]
    _command_handlers: Dict[str, Callable[..., Awaitable[None]]]
    _task_instances: List[Loop]
    _async_lock: asyncio.Lock

    def __init__(self, bot: Overlord, priority=None) -> None:
        super().__init__()
        self._bot = bot
        self._enabled = False
        self._async_lock = asyncio.Lock()

        attrs = [getattr(self, attr) for attr in dir(self) if not attr.startswith('_')]

        # Gather tasks
        self._tasks = [t for t in attrs if isinstance(t, OverlordTask)]
        self._task_instances = []

        # Gather commands
        self._commands = {c.name: c for c in attrs if isinstance(c, OverlordCommand)}
        self._command_handlers = {name: c.handler(self) for name, c in self._commands.items()}

        # Reattach implemented handlers
        handlers = get_coroutine_attrs(self, name_filter=lambda x: x.startswith('on_'))
        for h_name, h in handlers.items():
            setattr(self, h_name, self._handler(h))

        # Prioritize
        if priority is not None:
            self.__priority__ = priority
        if self.priority > 63 or self.priority < 0:
            raise InvalidArgument(f'priority should be less then 63 and bigger or equal then 0, got: {priority}')

    async def run_handler(self, coroutine: Callable[..., Awaitable[None]], *args, **kwargs):
        try:
            await coroutine(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except InvalidConfigException as e:
            raise e
        except Exception:
            try:
                await self.on_error(coroutine.__name__, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def _handler(self, func: Callable[..., Awaitable[None]]) -> Callable[..., Awaitable[None]]:
        async def wrapped(*args, **kwargs):
            if not self._enabled:
                return
            if func.__name__ not in BotExtension._skip_init_lock:
                await self.bot.init_lock()
            await self.run_handler(func, *args, **kwargs)
        return wrapped

    @staticmethod
    def task(*, seconds=0, minutes=0, hours=0, count=None, reconnect=True) -> \
            Callable[[Callable[..., Awaitable[None]]], OverlordTask]:

        def decorator(func: Callable[..., Awaitable[None]]) -> OverlordTask:

            async def wrapped(self, *args, **kwargs) -> None:
                await self.bot.init_lock()
                await func(self, *args, **kwargs)

            return OverlordTask(wrapped, seconds=seconds, minutes=minutes, hours=hours, count=count,
                                reconnect=reconnect)
        return decorator

    @staticmethod
    def command(name, description='') -> Callable[[Callable[..., Awaitable[None]]], OverlordCommand]:

        def decorator(func: Callable[..., Awaitable[None]]) -> OverlordCommand:
            return OverlordCommand(func, name=name, description=description)

        return decorator

    @property
    def name(self):
        return self.__extname__

    @property
    def bot(self) -> Overlord:
        return self._bot

    def start(self) -> None:
        if self._enabled:
            return
        self._enabled = True
        self._task_instances = [t.task(self) for t in self._tasks]
        for task in self._task_instances:
            task.start()

    def stop(self) -> None:
        if not self._enabled:
            return
        self._enabled = False
        for task in self._task_instances:
            task.stop()

    def sync(self) -> asyncio.Lock:
        return self._async_lock

    def help_embed(self, name) -> discord.Embed:
        title = f'{self.__extname__}'
        help_page = self.bot.new_embed(title, self.__description__, header=name, color=self.__color__)
        commands = self.bot.config.command
        prefix = self.bot.prefix
        for name, cmd in self._commands.items():
            if name not in commands or not commands[name]:
                help_page.add_field(name=f'[DISABLED] {prefix}{name}', value=cmd.help(prefix, []), inline=False)
            else:
                help_page.add_field(name=f'`$ {prefix}{commands[name][0]}`', value=cmd.help(prefix, commands[name]),
                                    inline=False)
        return help_page

    def cmd(self, name: str) -> Optional[OverlordCommand]:
        if name in self._commands:
            return self._commands[name]
        return None

    def cmd_handler(self, name: str) -> Optional[Callable[..., Awaitable[None]]]:
        if name in self._command_handlers:
            return self._command_handlers[name]
        return None

    def new_progress(self, name: str):
        embed = self.bot.new_embed('', '')
        return ProgressEmbed(name, embed)

    @property
    def priority(self) -> int:
        return self.__priority__

    @property
    def enabled(self) -> bool:
        return self._enabled

    ####################
    # Default Handlers #
    ####################

    async def on_error(self, event, *args, **kwargs) -> None:
        """
            Async error event handler

            Sends stacktrace to error channel
        """
        ext_name = type(self).__name__
        logging.exception(f'Error from {ext_name} extension on event: {event}, args: {args}, kwargs: {kwargs}')

        ex_type = sys.exc_info()[0]
        ex = sys.exc_info()[1]
        tb = traceback.format_exception(*sys.exc_info())
        name = ex_type.__name__

        reported_to = f'{R.MESSAGE.STATUS.REPORTED_TO} {self.bot.maintainer.mention}'
        details = f'{str(ex)}\n\n**{self.__extname__}** disabled'

        maintainer_report = self.bot.new_error_report(name, details, tb, args, kwargs)
        channel_report = self.bot.new_error_report(name, str(ex) + '\n' + reported_to)

        if self.bot.log_channel is not None and event != 'on_ready':
            try:
                await self.bot.log_channel.send(embed=channel_report)
            except Exception:
                pass

        try:
            await self.bot.maintainer.send(embed=maintainer_report)
        except Exception:
            pass

        self.stop()

    async def on_ready(self) -> None:
        pass
