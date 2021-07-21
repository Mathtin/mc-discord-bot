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
from concurrent.futures.thread import ThreadPoolExecutor
from logging import getLogger
from typing import Type, Optional, Any, Dict, List

from sqlalchemy import engine as SyncEngine, create_engine, select, update, delete
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError, DataError, InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, AsyncResult, AsyncSessionTransaction
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker, Session, SessionTransaction

from .models.base import Base, BaseModel

log = getLogger('db')


class DBSyncSession(object):
    _session: Session

    def __init__(self, session: Session) -> None:
        self._session = session

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._session.__exit__(exc_type, exc_val, exc_tb)

    ########################
    # Base session methods #
    ########################

    def execute(self, statement: Any) -> Result:
        return self._session.execute(statement)

    def commit(self) -> None:
        try:
            self._session.commit()
        except IntegrityError as e:
            log.error(f'`{__name__}` {e}')
            raise
        except DataError as e:
            log.error(f'`{__name__}` {e}')
            raise

    def rollback(self) -> None:
        self._session.rollback()

    def begin(self) -> SessionTransaction:
        return self._session.begin()

    def flush(self, objects=None) -> None:
        self._session.flush(objects)

    def refresh(self, instance, attribute_names=None, with_for_update=None) -> None:
        self._session.refresh(instance, attribute_names, with_for_update)

    def expunge(self, model: BaseModel) -> None:
        self._session.expunge(model)

    def detach(self, model: BaseModel) -> None:
        try:
            self.refresh(model)
            self.expunge(model)
        except InvalidRequestError:
            pass

    def close(self) -> None:
        self._session.close()

    def close_all(self) -> None:
        self._session.close_all()

    ##############################
    # Dict based session methods #
    ##############################

    def get(self, model_type: Type[BaseModel], pk: Any, pk_col: str = 'id') -> BaseModel:
        return self.execute(select(model_type).filter_by(**{pk_col: pk})).scalar_one_or_none()

    def add(self, *, model: Optional[BaseModel] = None,
            model_type: Type[BaseModel] = None,
            value: Dict[str, Any] = None) -> BaseModel:
        if model is None:
            model = model_type(**value)
        self._session.add(model)
        return model

    def merge(self, *, model: Optional[BaseModel] = None,
              model_type: Type[BaseModel] = None,
              value: Dict[str, Any] = None,
              pk_col: str = 'id') -> BaseModel:
        if model is None:
            model = self.get(model_type=model_type, pk=value[pk_col], pk_col=pk_col)
            if model is not None:
                for k, v in value.items():
                    setattr(model, k, v)
            else:
                model = model_type(**value)
                self._session.add(model)
        else:
            return self._session.merge(model)
        return model

    def delete(self, *, model: Optional[BaseModel] = None,
               model_type: Type[BaseModel] = None,
               pk: int = None,
               pk_col: str = 'id') -> Optional[BaseModel]:
        if model is None:
            model = self.get(model_type, pk, pk_col)
            if model is None:
                return None
            self.detach(model)
        self.execute(delete(type(model)).where(type(model).id == model.id))
        return model

    def touch(self, *, model: BaseModel = None,
              model_type: Type[BaseModel] = None,
              pk: int = None,
              pk_col: str = 'id') -> None:
        if model is None:
            self.execute(update(model_type).filter_by(**{pk_col: pk}))
        else:
            self.execute(update(model_type).where(model_type.id == model.id))

    def update(self, model_type: Type[BaseModel],
               value: Dict[str, Any],
               pk_col: str = 'id') -> Optional[BaseModel]:
        row = self.get(model_type, value[pk_col], pk_col)
        if row is None:
            return None
        for col in value:
            if getattr(row, col) != value[col]:
                setattr(row, col, value[col])
        return row

    ###################
    # Special methods #
    ###################

    def sync_table(self, model_type: Type[BaseModel],
                   values: List[Dict[str, Any]],
                   pk_col: str = 'id') -> None:
        # In-memory table index
        index = {}
        for v in values:
            index[v[pk_col]] = v
        # Sync existing rows
        for row in self.execute(select(model_type)).scalars().all():
            # Remove not in values
            if getattr(row, pk_col) not in index:
                self.delete(model=row)
                continue
            # Update those are in values
            new_values = index[getattr(row, pk_col)]
            for col in new_values:
                if getattr(row, col) != new_values[col]:
                    setattr(row, col, new_values[col])
            del index[getattr(row, pk_col)]
        # Add absent
        for pk in index:
            new_value = index[pk]
            self.add(model_type=model_type, value=new_value)


class DBAsyncWrappedSession(object):
    _session: DBSyncSession
    _executor: ThreadPoolExecutor
    sync_session: Session

    def __init__(self, session: Session, executor: ThreadPoolExecutor) -> None:
        self._session = DBSyncSession(session)
        self._executor = executor
        self.sync_session = session

    async def _run_in_executor(self, func, *args, **kwargs) -> Any:
        loop = asyncio.get_running_loop()

        def wrapped():
            return func(*args, **kwargs)

        return await loop.run_in_executor(self._executor, wrapped)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._run_in_executor(self._session.__exit__, exc_type, exc_val, exc_tb)

    ########################
    # Base session methods #
    ########################

    async def execute(self, statement: Any) -> Result:
        return await self._run_in_executor(self._session.execute, statement)

    async def scalar(self, statement: Any) -> Result:
        result = await self.execute(statement)
        return result.scalar()

    async def stream(self, statement: Any) -> AsyncResult:
        return AsyncResult(await self.execute(statement))

    async def commit(self) -> None:
        await self._run_in_executor(self._session.commit)

    async def flush(self, objects=None) -> None:
        return await self._run_in_executor(self._session.flush, objects)

    async def rollback(self) -> None:
        return await self._run_in_executor(self._session.rollback)

    def begin(self) -> AsyncSessionTransaction:
        return AsyncSessionTransaction(self)

    async def refresh(self, instance, attribute_names=None, with_for_update=None) -> None:
        await self._run_in_executor(self._session.refresh, instance, attribute_names, with_for_update)

    def expunge(self, model: BaseModel) -> None:
        self._session.expunge(model)

    async def detach(self, model: BaseModel) -> None:
        await self._run_in_executor(self._session.detach, model)

    async def close(self):
        await self._run_in_executor(self._session.close)

    async def close_all(self):
        await self._run_in_executor(self._session.close_all)

    ##############################
    # Dict based session methods #
    ##############################

    async def get(self, model_type: Type[BaseModel], pk: Any, pk_col: str = 'id') -> Optional[BaseModel]:
        return await self._run_in_executor(self._session.get, model_type, pk, pk_col)

    def add(self, *, model: Optional[BaseModel] = None,
                  model_type: Type[BaseModel] = None,
                  value: Dict[str, Any] = None) -> BaseModel:
        return self._session.add(model=model, model_type=model_type, value=value)

    async def merge(self, *, model: Optional[BaseModel] = None,
                    model_type: Type[BaseModel] = None,
                    value: Dict[str, Any] = None,
                    pk_col: str = 'id') -> BaseModel:
        return await self._run_in_executor(self._session.merge,
                                           model=model,
                                           model_type=model_type,
                                           value=value,
                                           pk_col=pk_col)

    async def delete(self, *, model: Optional[BaseModel] = None,
                     model_type: Type[BaseModel] = None,
                     pk: int = None,
                     pk_col: str = 'id') -> Optional[BaseModel]:
        return await self._run_in_executor(self._session.delete,
                                           model=model,
                                           model_type=model_type,
                                           pk=pk,
                                           pk_col=pk_col)

    async def touch(self, *, model: BaseModel = None,
                    model_type: Type[BaseModel] = None,
                    pk: int = None,
                    pk_col: str = 'id') -> None:
        return await self._run_in_executor(self._session.touch,
                                           model=model,
                                           model_type=model_type,
                                           pk=pk,
                                           pk_col=pk_col)

    async def update(self, model_type: Type[BaseModel],
                     value: Dict[str, Any],
                     pk_col: str = 'id') -> Optional[BaseModel]:
        return await self._run_in_executor(self._session.update,
                                           model_type=model_type,
                                           value=value,
                                           pk_col=pk_col)

    ###################
    # Special methods #
    ###################

    async def sync_table(self, model_type: Type[BaseModel], values: List[Dict[str, Any]], pk_col: str = 'id'):
        return await self._run_in_executor(self._session.sync_table,
                                           model_type=model_type,
                                           values=values,
                                           pk_col=pk_col)


class DBAsyncSession(object):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.__aexit__(exc_type, exc_val, exc_tb)

    ########################
    # Base session methods #
    ########################

    async def execute(self, statement: Any) -> Result:
        return await self._session.execute(statement)

    async def stream(self, statement: Any) -> AsyncResult:
        return await self._session.stream(statement)

    async def commit(self) -> None:
        try:
            await self._session.commit()
        except IntegrityError as e:
            log.error(f'`{__name__}` {e}')
            raise
        except DataError as e:
            log.error(f'`{__name__}` {e}')
            raise

    async def rollback(self) -> None:
        await self._session.rollback()

    def begin(self) -> AsyncSessionTransaction:
        return self._session.begin()

    async def flush(self, objects=None) -> None:
        await self._session.flush(objects)

    async def refresh(self, instance, attribute_names=None, with_for_update=None):
        await self._session.refresh(instance, attribute_names, with_for_update)

    def expunge(self, model: BaseModel) -> None:
        self._session.expunge(model)

    async def detach(self, model: BaseModel) -> None:
        try:
            await self.refresh(model)
            self.expunge(model)
        except InvalidRequestError:
            pass

    async def close(self):
        await self._session.close()

    async def close_all(self):
        await self._session.close_all()

    ##############################
    # Dict based session methods #
    ##############################

    async def get(self, model_type: Type[BaseModel], pk: int, pk_col: str = 'id') -> BaseModel:
        return (await self.execute(select(model_type).filter_by(**{pk_col: pk}))).scalar_one_or_none()

    def add(self, *, model: BaseModel = None,
                  model_type: Type[BaseModel] = None,
                  value: Dict[str, Any] = None) -> BaseModel:
        if model is None:
            model = model_type(**value)
        self._session.add(model)
        return model

    async def merge(self, *, model: BaseModel = None,
                    model_type: Type[BaseModel] = None,
                    value: Dict[str, Any] = None,
                    pk_col: str = 'id') -> BaseModel:
        if model is None:
            model = await self.get(model_type=model_type, pk=value[pk_col], pk_col=pk_col)
            if model is not None:
                for k, v in value.items():
                    setattr(model, k, v)
            else:
                model = model_type(**value)
                self._session.add(model)
        else:
            return await self._session.merge(model)
        return model

    async def delete(self, *, model: BaseModel = None,
                     model_type: Type[BaseModel] = None,
                     pk: int = None,
                     pk_col: str = 'id') -> Optional[BaseModel]:
        if model is None:
            model = await self.get(model_type, pk, pk_col)
            if model is None:
                return None
            await self.detach(model)
        await self.execute(delete(type(model)).where(type(model).id == model.id))
        return model

    async def touch(self, *, model: BaseModel = None,
                    model_type: Type[BaseModel] = None,
                    pk: int = None,
                    pk_col: str = 'id') -> None:
        if model is None:
            await self.execute(update(model_type).filter_by(**{pk_col: pk}))
        else:
            await self.execute(update(model_type).where(model_type.id == model.id))

    async def update(self, model_type: Type[BaseModel],
                     value: Dict[str, Any],
                     pk_col: str = 'id') -> Optional[BaseModel]:
        row = await self.get(model_type, value[pk_col], pk_col)
        if row is None:
            return None
        for col in value:
            if getattr(row, col) != value[col]:
                setattr(row, col, value[col])
        return row

    ###################
    # Special methods #
    ###################

    async def sync_table(self, model_type: Type[BaseModel],
                         values: List[Dict[str, Any]],
                         pk_col: str = 'id') -> None:
        # In-memory table index
        index = {}
        for v in values:
            index[v[pk_col]] = v
        # Sync existing rows
        async for row in await self.stream(select(model_type)):
            row = row[0]
            # Remove not in values
            if getattr(row, pk_col) not in index:
                await self.delete(model=row)
                continue
            # Update those are in values
            new_values = index[getattr(row, pk_col)]
            for col in new_values:
                if getattr(row, col) != new_values[col]:
                    setattr(row, col, new_values[col])
            del index[getattr(row, pk_col)]
        # Add absent
        for pk in index:
            new_value = index[pk]
            self.add(model_type=model_type, value=new_value)


class DBConnection(object):
    _db_async_engine: AsyncEngine
    _db_sync_engine: SyncEngine
    _session_sync_factory: sessionmaker
    _session_async_factory: sessionmaker

    _sync_session: Optional[DBSyncSession]
    _async_session: Optional[DBAsyncSession]

    _wrap_sync: bool
    _single_thread_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix='DB_CONNECTION_THREAD_')

    def __init__(self, engine_url: str) -> None:
        if 'sqlite' in engine_url:
            engine_url += '?check_same_thread=False'
        sync_engine_url = engine_url.replace('+asyncpg', '')
        # Create sync backend
        self._db_sync_engine = create_engine(sync_engine_url)
        Base.metadata.create_all(self._db_sync_engine)
        self._session_sync_factory = sessionmaker(bind=self._db_sync_engine,
                                                  autocommit=False,
                                                  autoflush=True,
                                                  expire_on_commit=False)
        # Create async backend
        if 'sqlite' in engine_url:
            self._wrap_sync = True
        else:
            self._db_async_engine = create_async_engine(engine_url)
            self._session_async_factory = sessionmaker(bind=self._db_async_engine,
                                                       autocommit=False,
                                                       autoflush=True,
                                                       class_=AsyncSession,
                                                       expire_on_commit=False)
            self._wrap_sync = False
        self._sync_session = None
        self._async_session = None

    def sync_session(self):
        return DBSyncSession(self._session_sync_factory())

    def async_session(self):
        if self._wrap_sync:
            return DBAsyncWrappedSession(self._session_sync_factory(), self._single_thread_pool)
        else:
            return DBAsyncSession(self._session_async_factory())
