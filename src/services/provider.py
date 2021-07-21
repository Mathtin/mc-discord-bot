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

from db import DBConnection

from .role import RoleService
from .user import UserService
from .playerprofile import PlayerProfileService


class ServiceProvider(object):
    _db: DBConnection

    _s_roles:            RoleService
    _s_users:            UserService
    _s_player_profiles:  PlayerProfileService

    def __init__(self, db: DBConnection):
        self._db = db

        self._s_roles = RoleService(self._db)
        self._s_users = UserService(self._db, self._s_roles)
        self._s_player_profiles = PlayerProfileService(self._db, self._s_users)

    @property
    def role(self) -> RoleService:
        return self._s_roles

    @property
    def user(self) -> UserService:
        return self._s_users

    @property
    def player_profiles(self) -> PlayerProfileService:
        return self._s_player_profiles
