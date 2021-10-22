import logging
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Text, DateTime, SmallInteger, func, ForeignKey, Boolean, Date, BigInteger
from app.model import Base
from app.model.manager import ModelManager, DBException, TransactionException
from app.lib import master
import uuid
from datetime import datetime
from dateutil.relativedelta import relativedelta


class UserTokensManager(ModelManager):
    def get_model(self):
        return UserTokens

    async def save(self, user_id, session=None):
        token = str(uuid.uuid4())

        try:
            user_token = await self.select_one(user_id, 'user_id', session=session)

            dt = {}
            dt['token'] = token
            dt['user_id'] = user_id
            dt['expired_at'] = datetime.now() + relativedelta(years=1)
            dt['status'] = 1

            if not user_token:
                cond = (UserTokens.user_id == user_id)
                await self.update(dt, cond, session=session)
            else:
                await self.insert(dt, session=session)

            return token

        except DBException as de:
            raise de

        except TransactionException as te:
            logging.info(str(te), exc_info=True)
            raise te


class UserTokens(Base):
    __tablename__ = 'user_tokens'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    token = Column(Text)
    expired_at = Column(DateTime)
    status = Column(SmallInteger, server_default='1')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.current_timestamp())

    manager = UserTokensManager()
