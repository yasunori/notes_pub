import logging
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Text, DateTime, SmallInteger, func, ForeignKey, Boolean, Date, BigInteger
from sqlalchemy.schema import Index
from app.model import Base
from app.model.manager import ModelManager, DBException, TransactionException
import uuid


class NotesManager(ModelManager):
    def get_model(self):
        return Notes

    @property
    def user_scope(self):
        return (Notes.status == Notes.NOTE_STATUS_SAFE)

    async def select_user(self, cond=True, order_by='id', offset=0, limit=20, session=None):
        try:
            if cond is True:
                cond = self.user_scope
            else:
                cond = cond & self.user_scope
            return await self.select(cond, order_by, offset, limit, session)
        except DBException as de:
            raise de

    async def select_user_count(self, cond=True, session=None):
        try:
            if cond is True:
                cond = self.user_scope
            else:
                cond = cond & self.user_scope
            return await self.select_count(cond, session)
        except DBException as de:
            raise de

    async def save(self, user_id, name, contents, note_id=None, original_id=None, session=None):
        try:
            if note_id:
                note = await self.select_one(note_id, session=session)  # 削除済み含めて検索
            elif original_id:
                note = await self.select_one(original_id, 'original_id', session)

            if note and note.user_id != user_id:  # 通常状態で誰かが保持している
                raise TransactionException('san_id:{0} のNoteは別のuser_id:{1}で登録済みです'.format(note_id, note.user_id))

            dt = {}
            if not note:
                dt['url'] = str(uuid.uuid4())  # urlの発行

            dt['user_id'] = user_id
            dt['name'] = name
            dt['contents'] = contents
            dt['original_id'] = original_id
            dt['status'] = Notes.NOTE_STATUS_SAFE

            if note:
                cond = (Notes.id == note.id)
                await self.update(dt, cond, session)
            else:
                pk = await self.insert(dt, session)
                note = await self.select_one(pk, session=session)

            return note

        except DBException as de:
            raise de

        except TransactionException as te:
            logging.error(str(te), exc_info=True)
            raise te

    async def delete(self, user_id, note_id, session=None):
        try:
            note = await self.select_one(note_id, session)
            if not note or note.user_id != user_id:
                raise TransactionException('note_id:{0} , user_id:{1}のnoteは見つかりません'.format(note_id, user_id))
            cond = (Notes.id == note_id)
            await self.update({'status': Notes.NOTE_STATUS_DELETED}, cond, session)
            return True

        except DBException as de:
            raise de

        except TransactionException as te:
            logging.error(str(te), exc_info=True)
            raise te


class Notes(Base):
    __tablename__ = 'notes'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(Text)
    contents = Column(Text)
    url = Column(Text, unique=True)
    original_id = Column(Text)
    status = Column(SmallInteger, server_default='1')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.current_timestamp())

    manager = NotesManager()

    NOTE_STATUS_SAFE = 1
    NOTE_STATUS_DELETED = -1


Index("notes_search_by_user_index", Notes.user_id, Notes.status, Notes.id.desc())
