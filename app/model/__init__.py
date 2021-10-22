from __future__ import annotations
from sqlalchemy.orm import scoped_session, sessionmaker, relation
from sqlalchemy.orm import declarative_base

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
import config

Base = declarative_base()

conf = config.__get_app_conf(config.MODE)['DB']
engine = create_async_engine(conf['DSN'])
async_session = sessionmaker(engine,
                             autocommit=conf['AUTO_COMMIT'],
                             autoflush=conf['AUTO_FLUSH'],
                             class_=AsyncSession,
                             expire_on_commit=False,
                             future=True)


async def close_db():
    print("*****close*****")
    #session = async_session()
    #await session.close()
    await engine.dispose()
    print("*****ok*****")

# モデルの追加
from app.model.users import Users
from app.model.usertokens import UserTokens
from app.model.notes import Notes
