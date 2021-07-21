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
from typing import Any, Dict, List, Callable, Awaitable, Optional

import discord as DIS

import db as DB
from util import ConfigView


###################
# Generic Objects #
###################

class OverlordGenericObject(object):
    db: Any
    discord: Any

    def __init__(self, discord, db) -> None:
        super().__init__()
        self.discord = discord
        self.db = db


class OverlordRole(OverlordGenericObject):
    db: DB.Role
    discord: DIS.Role


class OverlordUser(OverlordGenericObject):
    db: DB.User
    discord: DIS.User


class OverlordMember(OverlordUser):
    discord: DIS.Member


###########
# Configs #
###########

class OverlordControlConfig(ConfigView):
    """
    control {
        prefix = "..."
        roles = [...]
        channel = ...
    }
    """
    prefix: str = "ov/"
    roles: List[str] = ["Overlord"]
    channel: int = 0


class OverlordRootConfig(ConfigView):
    """
    bot {
        control : OverlordControlConfig
        egg_done = ...
        keep_absent_users = ...
        command {
            help = ["help", ...]
            ...
        }
    }
    """
    control: OverlordControlConfig = OverlordControlConfig()
    egg_done: str = "change this part"
    keep_absent_users: bool = True
    command: Dict[str, List[str]] = {}


##############
# Interfaces #
##############

class IOverlordTask(object):

    def task(self, ext) -> asyncio.AbstractEventLoop:
        raise NotImplementedError()


class IOverlordCommand(object):

    optional_prefix = 'opt_'

    func: Callable[..., Awaitable[None]]
    name: str
    description: str

    def usage(self, prefix: str, cmd_name: str) -> str:
        raise NotImplementedError()

    def help(self, prefix: str, aliases: List[str]) -> str:
        raise NotImplementedError()

    def handler(self, ext):
        raise NotImplementedError()


class IBotExtension(object):

    @staticmethod
    def task(*, seconds=0, minutes=0, hours=0, count=None, reconnect=True) -> \
            Callable[[Callable[..., Awaitable[None]]], IOverlordTask]:
        raise NotImplementedError()

    @staticmethod
    def command(name, description='') -> Callable[[Callable[..., Awaitable[None]]], IOverlordCommand]:
        raise NotImplementedError()

    @property
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def bot(self) -> Any:
        raise NotImplementedError()

    def start(self) -> None:
        raise NotImplementedError()

    def stop(self) -> None:
        raise NotImplementedError()

    def sync(self) -> asyncio.Lock:
        raise NotImplementedError()

    def help_embed(self, name) -> DIS.Embed:
        raise NotImplementedError()

    def cmd(self, name: str) -> Optional[IOverlordCommand]:
        raise NotImplementedError()

    def cmd_handler(self, name: str) -> Optional[Callable[..., Awaitable[None]]]:
        raise NotImplementedError()

    async def run_handler(self, coroutine: Callable[..., Awaitable[None]], *args, **kwargs):
        raise NotImplementedError()

    @property
    def priority(self) -> int:
        raise NotImplementedError()

    @property
    def enabled(self) -> bool:
        raise NotImplementedError()

    ####################
    # Default Handlers #
    ####################

    async def on_error(self, event, *_, **__) -> None:
        raise NotImplementedError()

    async def on_ready(self) -> None:
        raise NotImplementedError()
