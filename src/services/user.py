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

import logging

import discord
import db as DB
import db.converters as conv
import db.queries as q

from typing import Optional, Union, Tuple
from .role import RoleService
from .service import DBService

log = logging.getLogger('user-service')


##########################
# Service implementation #
##########################

class UserService(DBService):

    # Members passed via constructor
    db: DB.DBConnection
    roles: RoleService

    def __init__(self, db: DB.DBConnection, roles: RoleService) -> None:
        super().__init__(db)
        self.roles = roles

    @staticmethod
    def parse_qualified_name(qualified_name: str) -> Tuple[str, int]:
        if '#' not in qualified_name:
            raise ValueError(f"Invalid qualified name: {qualified_name}")
        [name, disc] = qualified_name.split('#')
        return name, int(disc)

    @staticmethod
    def is_absent(user: DB.User) -> bool:
        return user.roles is None and user.display_name is None

    def get_sync(self, d_user: Union[discord.User, discord.Member]) -> Optional[DB.User]:
        return self.get_optional_sync(q.select_user_by_did(d_user.id))

    async def get(self, d_user: Union[discord.User, discord.Member]) -> Optional[DB.User]:
        return await self.get_optional(q.select_user_by_did(d_user.id))

    def get_by_display_name_sync(self, display_name: str) -> Optional[DB.User]:
        return self.get_optional_sync(q.select_user_by_display_name(display_name))

    async def get_by_display_name(self, display_name: str) -> Optional[DB.User]:
        return await self.get_optional(q.select_user_by_display_name(display_name))

    def get_by_q_name_sync(self, name: str, disc: int) -> Optional[DB.User]:
        return self.get_optional_sync(q.select_user_by_q_name(name, disc))

    async def get_by_q_name(self, name: str, disc: int) -> Optional[DB.User]:
        return await self.get_optional(q.select_user_by_q_name(name, disc))

    def get_by_qualified_name_sync(self, qualified_name: str) -> Optional[DB.User]:
        return self.get_by_q_name_sync(*self.parse_qualified_name(qualified_name))

    async def get_by_qualified_name(self, qualified_name: str) -> Optional[DB.User]:
        return await self.get_by_q_name(*self.parse_qualified_name(qualified_name))

    def mark_everyone_absent_sync(self) -> None:
        self.execute_sync(q.update_all_users_absent())

    async def mark_everyone_absent(self) -> None:
        await self.execute(q.update_all_users_absent())

    def merge_member_sync(self, d_user: discord.Member) -> DB.User:
        return self.merge_sync(DB.User, conv.member_row(d_user, self.roles.role_rows_did_map), 'did')

    async def merge_member(self, d_user: discord.Member) -> DB.User:
        return await self.merge(DB.User, conv.member_row(d_user, self.roles.role_rows_did_map), 'did')

    def add_user_sync(self, d_user: discord.User) -> DB.User:
        return self.create_sync(DB.User, conv.user_row(d_user))

    async def add_user(self, d_user: discord.User) -> DB.User:
        return await self.create(DB.User, conv.user_row(d_user))

    def remove_sync(self, d_user: Union[discord.User, discord.Member]) -> Optional[DB.User]:
        user = self.get_sync(d_user)
        return user and self.delete_sync(DB.User, user.id)

    async def remove(self, d_user: Union[discord.User, discord.Member]) -> Optional[DB.User]:
        user = await self.get(d_user)
        return user and await self.delete(DB.User, user.id)

    def make_user_absent_sync(self, d_user: Union[discord.User, discord.Member]) -> Optional[DB.User]:
        self.execute_sync(q.update_user_absent_by_did(d_user.id))
        return self.get_sync(d_user)

    async def make_user_absent(self, d_user: Union[discord.User, discord.Member]) -> Optional[DB.User]:
        await self.execute(q.update_user_absent_by_did(d_user.id))
        return await self.get(d_user)

    def remove_absent_sync(self) -> None:
        self.execute_sync(q.delete_absent_users())

    async def remove_absent(self) -> None:
        await self.execute(q.delete_absent_users())

    def clear_all_sync(self):
        self.execute_sync(q.delete_all(DB.User))

    async def clear_all(self):
        await self.execute(q.delete_all(DB.User))
