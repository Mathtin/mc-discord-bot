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
from typing import Optional, Union, List
from uuid import UUID

import discord

import db as DB
import db.converters as conv
import db.queries as q
from util.mcuuid import PlayerData
from .service import DBService
from .user import UserService

log = logging.getLogger('user-service')


##########################
# Service implementation #
##########################

class PlayerProfileService(DBService):

    # Members passed via constructor
    db: DB.DBConnection
    users: UserService

    def __init__(self, db: DB.DBConnection, users: UserService) -> None:
        super().__init__(db)
        self.users = users

    def get_all_sync(self, d_user: Union[discord.User, discord.Member, DB.User] = None) -> List[DB.PlayerProfile]:
        if d_user is None:
            return self.get_list_sync(q.select_player_profiles())
        if isinstance(d_user, DB.User):
            return self.get_list_sync(q.select_player_profiles_by_did(d_user.did))
        return self.get_list_sync(q.select_player_profiles_by_did(d_user.id))

    async def get_all(self, d_user: Union[discord.User, discord.Member, DB.User] = None) -> List[DB.PlayerProfile]:
        if d_user is None:
            return await self.get_list(q.select_player_profiles())
        if isinstance(d_user, DB.User):
            return await self.get_list(q.select_player_profiles_by_did(d_user.did))
        return await self.get_list(q.select_player_profiles_by_did(d_user.id))

    def get_whitelisted_sync(self,
                            d_user: Union[discord.User,
                                          discord.Member,
                                          DB.User] = None) -> List[DB.PlayerProfile]:
        if d_user is None:
            return self.get_list_sync(q.select_player_profiles_whitelisted())
        if isinstance(d_user, DB.User):
            return self.get_list_sync(q.select_player_profiles_by_did_whitelisted(d_user.did))
        return self.get_list_sync(q.select_player_profiles_by_did_whitelisted(d_user.id))

    async def get_whitelisted(self,
                              d_user: Union[discord.User,
                                            discord.Member,
                                            DB.User] = None) -> List[DB.PlayerProfile]:
        if d_user is None:
            return await self.get_list(q.select_player_profiles_whitelisted())
        if isinstance(d_user, DB.User):
            return await self.get_list(q.select_player_profiles_by_did_whitelisted(d_user.did))
        return await self.get_list(q.select_player_profiles_by_did_whitelisted(d_user.id))

    def get_by_ign_sync(self, ign: str) -> Optional[DB.PlayerProfile]:
        return self.get_optional_sync(q.select_player_profile_by_ign(ign))

    async def get_by_ign(self, ign: str) -> Optional[DB.PlayerProfile]:
        return await self.get_optional(q.select_player_profile_by_ign(ign))

    def get_by_uuid_sync(self, uuid: Union[UUID, str]) -> Optional[DB.PlayerProfile]:
        return self.get_optional_sync(q.select_player_profile_by_uuid(str(uuid)))

    async def get_by_uuid(self, uuid: Union[UUID, str]) -> Optional[DB.PlayerProfile]:
        return await self.get_optional(q.select_player_profile_by_uuid(str(uuid)))

    def get_by_message_did_sync(self, did: int) -> Optional[DB.PlayerProfile]:
        return self.get_optional_sync(q.select_player_profile_by_message_did(did))

    async def get_by_message_did(self, did: int) -> Optional[DB.PlayerProfile]:
        return await self.get_optional(q.select_player_profile_by_message_did(did))

    def add_profile_sync(self, user: DB.User, player: PlayerData, msg: discord.Message) -> DB.PlayerProfile:
        return self.create_sync(DB.PlayerProfile, conv.player_profile_row(user, player, msg))

    async def add_profile(self, user: DB.User, player: PlayerData, msg: discord.Message) -> DB.PlayerProfile:
        return await self.create(DB.PlayerProfile, conv.player_profile_row(user, player, msg))

    def add_persistent_profile_sync(self, user: DB.User, player: PlayerData) -> DB.PlayerProfile:
        return self.create_sync(DB.PlayerProfile, conv.persistent_player_profile_row(user, player))

    async def add_persistent_profile(self, user: DB.User, player: PlayerData) -> DB.PlayerProfile:
        return await self.create(DB.PlayerProfile, conv.persistent_player_profile_row(user, player))

    def remove_sync(self, profile: DB.PlayerProfile) -> None:
        self.delete_sync(DB.PlayerProfile, profile.id)

    async def remove(self, profile: DB.PlayerProfile) -> None:
        await self.delete(DB.PlayerProfile, profile.id)

    def clear_all_sync(self):
        self.execute_sync(q.delete_all(DB.PlayerProfile))

    async def clear_all(self):
        await self.execute(q.delete_all(DB.PlayerProfile))

    def clear_dynamic_sync(self):
        self.execute_sync(q.delete_dynamic_profiles())

    async def clear_dynamic(self):
        await self.execute(q.delete_dynamic_profiles())
