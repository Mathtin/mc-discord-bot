#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###################################################
#........../\./\...___......|\.|..../...\.........#
#........./..|..\/\.|.|_|._.|.\|....|.c.|.........#
#......../....../--\|.|.|.|i|..|....\.../.........#
#        Mathtin (c)                              #
###################################################
#   Author: Daniel [Mathtin] Shiko                #
#   Copyright (c) 2020 <wdaniil@mail.ru>          #
#   This file is released under the MIT license.  #
###################################################

__author__ = 'Mathtin'

from sqlalchemy.orm.query import Query
from sqlalchemy.sql.dml import Insert
from sqlalchemy.sql.elements import literal_column
from sqlalchemy.sql.selectable import Select
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy import func, insert, select, and_

from .models import *
from .session import DBSession

def get_user_by_did(db: DBSession, id: int) -> User:
    return db.query(User).filter(User.did == id).first()

def get_msg_by_did(db: DBSession, id: int) -> MessageEvent:
    return db.query(MessageEvent).filter(MessageEvent.message_id == id).first()

def get_last_member_event_by_did(db: DBSession, id: int) -> MessageEvent:
    return db.query(MemberEvent).join(User)\
            .filter(User.did == id)\
            .order_by(MemberEvent.created_at.desc()).first()

def get_last_vc_event_by_id(db: DBSession, id: int, channel_id: int) -> VoiceChatEvent:
    return db.query(VoiceChatEvent)\
            .filter(and_(VoiceChatEvent.user_id == id, VoiceChatEvent.channel_id == channel_id))\
            .order_by(VoiceChatEvent.created_at.desc()).first()

def get_user_stat_by_id(db: DBSession, id: int, type_id: int) -> UserStat:
    return db.query(UserStat)\
            .filter(and_(UserStat.user_id == id, UserStat.type_id == type_id)).first()

def select_message_count_per_user(type_id: int, lit_values: list) -> Select:
    value_column = func.count(MessageEvent.id).label('value')
    lit_columns = [literal_column(str(v)).label(l) for (l,v) in lit_values]
    select_columns = [value_column, MessageEvent.user_id] + lit_columns
    return select(select_columns).where(MessageEvent.type_id == type_id).group_by(MessageEvent.user_id)

def select_vc_time_per_user(type_id: int, lit_values: list) -> Select:
    join_time = cast(func.strftime('%s', VoiceChatEvent.created_at), Integer)
    left_time = cast(func.strftime('%s', VoiceChatEvent.updated_at), Integer)
    value_column = func.sum(left_time - join_time).label('value')
    lit_columns = [literal_column(str(v)).label(l) for (l,v) in lit_values]
    select_columns = [value_column, VoiceChatEvent.user_id] + lit_columns
    return select(select_columns).where(VoiceChatEvent.type_id == type_id).group_by(VoiceChatEvent.user_id)

def insert_user_stat_from_select(select_query: Query) -> Insert:
    return insert(UserStat, inline=True).from_select(['value', 'user_id', 'type_id'], select_query)