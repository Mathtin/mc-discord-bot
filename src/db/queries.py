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

from datetime import datetime
from typing import Any, Tuple, List, Type

from sqlalchemy import func, and_, literal_column, Column
from sqlalchemy.sql import Select, Insert, Update, Delete
from sqlalchemy.sql.expression import cast, delete, text, extract
from sqlalchemy.sql.expression import insert, select, update
from sqlalchemy.sql.sqltypes import Integer

from .models import *
from .models.base import BaseModel


##################
# SELECT QUERIES #
##################

def select_role(role_name: str) -> Select:
    return select(Role).where(Role.name == role_name)


def select_user_by_did(did: int) -> Select:
    return select(User).where(User.did == did)


def select_user_by_display_name(display_name: str) -> Select:
    return select(User).where(User.display_name == display_name)


def select_user_by_q_name(name: str, disc: int) -> Select:
    return select(User).where(User.name == name, User.disc == disc)


def select_player_profile_by_did(did: int) -> Select:
    return select(PlayerProfile).join(User).where(User.did == did)


def select_player_profile_by_ign(ign: str) -> Select:
    return select(PlayerProfile).where(PlayerProfile.ign == ign)


def select_player_profile_by_message_did(did: int) -> Select:
    return select(PlayerProfile).where(PlayerProfile.message_did == did)


##################
# INSERT QUERIES #
##################

#


##################
# UPDATE QUERIES #
##################

def update_all_users_absent() -> Update:
    return update(User) \
        .values(roles=None, display_name=None)


def update_user_absent(id_: int) -> Update:
    return update(User) \
        .values(roles=None, display_name=None) \
        .where(User.id == id_)


def update_user_absent_by_did(did: int) -> Update:
    return update(User) \
        .values(roles=None, display_name=None) \
        .where(User.did == did)


##################
# DELETE QUERIES #
##################

def delete_absent_users() -> Delete:
    return delete(User) \
        .where(User.roles.is_(None), User.display_name.is_(None))

def delete_dynamic_profiles() -> Delete:
    return delete(PlayerProfile) \
        .where(PlayerProfile.persistent == False)


def delete_all(model_type: Type[BaseModel]) -> Delete:
    return delete(model_type)
