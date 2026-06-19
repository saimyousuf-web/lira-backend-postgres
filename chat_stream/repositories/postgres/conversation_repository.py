from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID

from models.conversation import Conversation
from models.session import Session
from chat_stream.repositories.Iconversation import ConversationRepository
import asyncio
from datetime import datetime
from models.course import Course
from models.module import Module
from models.chunks import Chunk
class PostgresConversationRepository(ConversationRepository):

    def __init__(self, db: AsyncSession):
        self.db = db


    async def get_conversation(self, conversation_id: UUID,):
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
        )

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()
    
    async def create_conversation(
        self,
        conversation_id: UUID,
        uid: UUID,
        ndid: UUID,
        course_id: UUID,
        title: str,
        created_by: UUID,
        sts: str,
        step: str
    ):
        conversation = Conversation(
            id=conversation_id,
            uid=uid,
            ndid=ndid,
            cid=course_id,
            title=title,
            crtby=created_by,
            updby=created_by,
            sts = sts,
            step= step
        )

        self.db.add(conversation)

        await self.db.flush()
        await self.db.refresh(conversation)
        
        return conversation

    
    async def update_conversation(
        self,
        conversation_id: UUID,
        last_message: str,
        step: str
    ):
        stmt = (
            update(Session)
            .where(Session.convid == conversation_id)
            .values(
                msgtxt=last_message[:100],
                updat=datetime.utcnow(),
            )
            .returning(Session)
        )

        result = await self.db.execute(stmt)
        updated = result.scalar_one_or_none()

        if updated:            
            return updated
        
        return None

    async def create_message( # message stored at session table
        self,
        conversation_id: UUID,
        sender: UUID,
        message: str,
        created_by: UUID,
        updated_by: UUID
    ):
        db_message = Session(
            convid=conversation_id,
            msgtxt=message,
            sender=sender,
            crtby=created_by,
            updby=updated_by,
        )

        self.db.add(db_message)

        await self.db.flush()
        await self.db.refresh(db_message)

        return db_message

    async def get_recent_messages(
        self,
        conversation_id: UUID,
        limit: int = 20,
    ):
        stmt = (
            select(Session)
            .where(
                Session.convid
                == conversation_id
            )
            .order_by(
                Session.crtat.desc()
            )
            .limit(limit)
        )

        result = await self.db.execute(stmt)

        messages = result.scalars().all()

        return list(reversed(messages))

    async def increment_message_count(self, conversation_id: UUID):
        await self.db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(msgnum=Conversation.msgnum + 1)
        )

    async def update_step(self, conversation_id: UUID, step: str):
        await self.db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(step=step)
        )

    async def update_message(self, message: str, message_id: UUID):
        stmt = (
            update(Session)
            .where(Session.id == message_id)
            .values(
                msgtxt=message,
                updat=datetime.utcnow(),
            )
            .returning(Session)
        )

        result = await self.db.execute(stmt)
        updated = result.scalar_one_or_none()
        return updated

    async def get_chunk_context(self, chunk_ids: list[UUID],) -> list[dict]:
        
        try:
            if not chunk_ids:
                return []

            result = await self.db.execute(
                select(
                    Chunk.id.label("chunk_id"),
                    Chunk.txt.label("chunk_text"),
                    Chunk.imgkeys.label("image_keys"),

                    Module.id.label("module_id"),
                    Module.nm.label("fileName"),
                    Module.ty.label("module_type"),
                    Module.loc.label("s3Location"),
                    
                    Course.id.label("course_id"),
                    Course.nm.label("course_name"),
                )
                .join(
                    Module,
                    Chunk.moid == Module.id
                )
                .join(
                    Course,
                    Chunk.cid == Course.id
                )
                .where(
                    Chunk.id.in_(chunk_ids)
                )
            )

            rows = result.mappings().all()
            res = [dict(row) for row in rows]
            return res
            
        except Exception as e:
             return []
        

