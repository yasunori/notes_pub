import logging
from sqlalchemy.future import select
from sqlalchemy import update, insert, delete, text, func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Text, DateTime, SmallInteger, func
from app.model import Base
from app.model.manager import ModelManager, DBException, TransactionException


class UsersManager(ModelManager):
    def get_model(self):
        return Users

    @property
    def user_scope(self):
        return (Users.status == 1)

    def __encode_password(self, password):
        import hashlib
        return hashlib.md5(password.encode('utf-8')).hexdigest()

    async def get_valid_user(self, login_id, password, session=None):
        try:
            password_encoded = self.__encode_password(password)
            cond = (Users.login_id == login_id) & (Users.password == password_encoded) & self.user_scope
            users = await self.select(cond, session=session)
            if users:
                return users[0]
            else:
                return False
        except DBException as de:
            raise de

    async def select_user(self, cond=True, order_by='id', offset=0, limit=20, session=None):
        try:
            if cond is True:
                cond = self.user_scope
            else:
                cond = cond & self.user_scope
            return await self.select(cond, order_by, offset, limit, session=session)
        except DBException as de:
            raise de

    async def select_user_count(self, cond=True, session=None):
        try:
            if cond is True:
                cond = self.user_scope
            else:
                cond = cond & self.user_scope
            return await self.select_count(cond, session=session)
        except DBException as de:
            raise de

    async def select_one_by_mail_address(self, mail_address, session=None):
        cond = (Users.mail_address == mail_address) & self.user_scope
        objs = await self.select(cond, session=session)
        if not objs:
            return None
        return objs[0]

    async def save(self, name, mail_address, password=None, user_id=None, session=None):
        try:
            if user_id:
                user = await self.select_one(user_id, session=session)
                if not user:
                    raise TransactionException('id:{0}のuserは見つかりません'.format(user_id))

                # mail_address の重複を確認する
                tmp = await self.select_one_by_mail_address(mail_address, session=session)
                if tmp and tmp.id != user2.id:
                    raise TransactionException('mail_address:{0} は別のuser_id:{1}で登録済みです'.format(mail_address, tmp.id))
            else:
                user = None
                tmp = await self.select_one_by_mail_address(mail_address, session=session)
                if tmp:
                    raise TransactionException('mail_address:{0} は別のuser_id:{1}で登録済みです'.format(mail_address, tmp.id))

            if password:
                password = self.__encode_password(password)

            dt = {}
            dt['name'] = name
            dt['mail_address'] = mail_address
            if password:
                dt['password'] = password

            if user:
                cond = (Users.id == user.id)
                await self.update(dt, cond, session=session)
            else:
                pk = await self.insert(dt, session=session)
                user = await self.select_one(pk, session=session)

            return user

        except DBException as de:
            raise de

        except TransactionException as te:
            logging.info(str(te), exc_info=True)
            raise te

    async def delete(self, id, session=None):
        user = await self.select_one(id)
        if not user:
            return False

        cond = (Users.id == id)
        await self.update({'status': Users.USER_STATUS_DELETED}, cond, session=session)
        return True


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    mail_address = Column(Text)
    password = Column(Text)
    user_type = Column(SmallInteger, server_default='1')
    status = Column(SmallInteger, server_default='1')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.current_timestamp())

    notes = relationship('Notes', uselist=True, backref='user', lazy='subquery')

    manager = UsersManager()

    USER_TYPE_GENERAL = 1
    USER_TYPE_ADMIN = 2

    USER_STATUS_SAFE = 1
    USER_STATUS_DELETED = -1

    @property
    def is_admin(self):
        if self.user_type == self.USER_TYPE_ADMIN:
            return True
        return False

    @property
    def is_manager(self):
        if self.user_type == self.USER_TYPE_MANAGER:
            return True
        return False
