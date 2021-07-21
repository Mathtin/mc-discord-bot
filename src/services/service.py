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
from typing import Any, Type, Dict, Optional

import db as DB
from db.models.base import BaseModel

log = logging.getLogger('event-service')


##########################
# Service implementation #
##########################

class DBService(object):

    # Members passed via constructor
    _db: DB.DBConnection

    def __init__(self, db: DB.DBConnection) -> None:
        self._db = db

    def session(self):
        return self._db.async_session()

    def sync_session(self):
        return self._db.sync_session()

    def execute_sync(self, stmt: Any) -> None:
        with self.sync_session() as session:
            with session.begin():
                session.execute(stmt)

    async def execute(self, stmt: Any) -> None:
        async with self.session() as session:
            async with session.begin():
                await session.execute(stmt)

    def get_optional_sync(self, stmt: Any) -> Any:
        with self.sync_session() as session:
            obj = session.execute(stmt).scalar_one_or_none()
            session.detach(obj)
            return obj

    async def get_optional(self, stmt: Any) -> Any:
        async with self.session() as session:
            obj = (await session.execute(stmt)).scalar_one_or_none()
            await session.detach(obj)
            return obj

    def create_sync(self, model_type: Type[BaseModel], value: Dict[str, Any]) -> BaseModel:
        with self.sync_session() as session:
            with session.begin():
                obj = session.add(model_type=model_type, value=value)
            session.detach(obj)
        return obj

    async def create(self, model_type: Type[BaseModel], value: Dict[str, Any]) -> BaseModel:
        async with self.session() as session:
            async with session.begin():
                obj = session.add(model_type=model_type, value=value)
            await session.detach(obj)
        return obj

    def merge_sync(self, model_type: Type[BaseModel],
                   value: Dict[str, Any],
                   pk_col: str = 'id') -> BaseModel:
        with self.sync_session() as session:
            with session.begin():
                obj = session.merge(model_type=model_type, value=value, pk_col=pk_col)
            session.detach(obj)
        return obj

    async def merge(self, model_type: Type[BaseModel],
                    value: Dict[str, Any],
                    pk_col: str = 'id') -> BaseModel:
        async with self.session() as session:
            async with session.begin():
                obj = await session.merge(model_type=model_type, value=value, pk_col=pk_col)
            await session.detach(obj)
        return obj

    def save_sync(self, model: BaseModel) -> BaseModel:
        with self.sync_session() as session:
            with session.begin():
                obj = session.merge(model=model)
            session.detach(obj)
        return obj

    async def save(self, model: BaseModel) -> BaseModel:
        async with self.session() as session:
            async with session.begin():
                obj = await session.merge(model=model)
            await session.detach(obj)
        return obj

    def delete_sync(self, model_type: Type[BaseModel], pk: int) -> Optional[BaseModel]:
        with self.sync_session() as session:
            with session.begin():
                obj = session.delete(model_type=model_type, pk=pk)
            if obj is not None:
                session.detach(obj)
        return obj

    async def delete(self, model_type: Type[BaseModel], pk: int) -> Optional[BaseModel]:
        async with self.session() as session:
            async with session.begin():
                obj = await session.delete(model_type=model_type, pk=pk)
            if obj is not None:
                await session.detach(obj)
        return obj
