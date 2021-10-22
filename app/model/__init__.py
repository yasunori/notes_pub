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
async_session_maker = sessionmaker(engine,
                             autocommit=conf['AUTO_COMMIT'],
                             autoflush=conf['AUTO_FLUSH'],
                             class_=AsyncSession,
                             expire_on_commit=False,
                             future=True)

db_session = async_session_maker()


async def close_session():
    global db_session
    if db_session:
        print("*****close*****")
        await db_session.close()

# モデルの追加
from app.model.users import Users
from app.model.usertokens import UserTokens
from app.model.notes import Notes
