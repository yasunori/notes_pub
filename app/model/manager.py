# -*- coding: utf-8 -*-
from sqlalchemy.future import select
from sqlalchemy import update, insert, delete, text, func
from app.model import async_session


class ModelManager():

    @property
    def async_session(self):
        """
        外部でtransaction管理するためにsessionmakerを渡す
        """
        return async_session

    async def insert(self, dt, session=None):
        try:
            if session:
                # 外部でtransaction管理している
                ret = await self._insert(dt, session)
                return ret.inserted_primary_key[0]

            # transaction作成してcommit
            async with async_session.begin() as session:
                ret = await self._insert(dt, session)
                return ret.inserted_primary_key[0]

        except Exception as e:
            raise DBException() from e

    async def _insert(self, dt, session):
        class_f = self.get_model()
        stmt = insert(class_f)
        return await session.execute(stmt, dt)

    async def update(self, dt, cond, session=None):
        try:
            if session:
                # 外部でtransaction管理している
                return await self._update(dt, cond, session)

            # transaction作成してcommit
            async with async_session.begin() as session:
                return await self._update(dt, cond, session)

        except Exception as e:
            raise DBException() from e

    async def _update(self, dt, cond, session):
        class_f = self.get_model()
        stmt = update(class_f).where(cond).values(**dt)
        await session.execute(stmt)

    async def delete(self, cond=True, session=None):
        if(cond is True):
            # 全部消すのを禁止
            return False
        try:
            if session:
                # 外部でtransaction管理している
                return await self._delete(cond, session)

            # transaction作成してcommit
            async with async_session.begin() as session:
                return await self._delete(cond, session)

        except Exception as e:
            raise DBException() from e

    async def _delete(self, cond, session):
        class_f = self.get_model()
        stmt = delete(class_f).where(cond)
        await session.execute(stmt)

    async def select_one(self, dt, key='id', session=None):
        try:
            if session:
                # 外部でtransaction管理している
                return await self._select_one(dt, key, session)

            async with async_session.begin() as session:
                return await self._select_one(dt, key, session)

        except Exception as e:
            raise DBException() from e

    async def _select_one(self, dt, key, session):
        def is_numeric(n):
            return not isinstance(n, bool) and isinstance(n, (int, float, complex))

        class_f = self.get_model()
        if is_numeric(dt):
            dt = str(dt)
        else:
            dt = "'" + str(dt) + "'"
        cond = text(key + '=' + dt)
        stmt = select(class_f).where(cond).limit(1)
        return (await session.execute(stmt)).scalars().first()

    async def select(self, cond=True, order_by='id', offset=0, limit=20, session=None):
        try:
            if session:
                # 外部でtransaction管理している
                return await self._select(cond, order_by, offset, limit, session)

            async with async_session.begin() as session:
                return await self._select(cond, order_by, offset, limit, session)

        except Exception as e:
            raise DBException() from e

    async def _select(self, cond, order_by, offset, limit, session):
        class_f = self.get_model()
        stmt = select(class_f).where(cond).order_by(order_by).slice(offset, offset + limit)
        return (await session.execute(stmt)).scalars().all()

    async def select_count(self, cond=True, session=None):
        try:
            if session:
                # 外部でtransaction管理している
                return await self._select_count(cond, session)

            async with async_session.begin() as session:
                return await self._select_count(cond, session)

        except Exception as e:
            raise DBException() from e

    async def _select_count(self, cond, session):
        class_f = self.get_model()
        stmt = select(func.count(class_f.id)).where(cond)
        return (await session.execute(stmt)).scalars().one()


class TransactionException(Exception):
    EXCEPTION_TYPE_ABORT = 1
    EXCEPTION_TYPE_CONTINUE = 2

    def __init__(self, message, exception_type=1, error_code=None, action_data=None):
        Exception.__init__(self, message)
        self.exception_type = exception_type
        self.error_code = error_code
        self.action_data = action_data


class DBException(Exception):
    """ Exceptopn """
