from uuid import UUID

from chat_stream.repositories.postgres.conversation_repository import ConversationRepository
from fastapi import HTTPException

from collections import deque, defaultdict
from asyncio import Lock
from datetime import datetime

class ConversationService:

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        db
    ):
        self.db = db
        self.conversation_repository = conversation_repository
        self.chat_memory_cached = {}

        self.cache_lock = Lock()
        self.MAX_CACHED_CHATS = 50

    async def _create_conversation(
        self,
        conversation_id: UUID,
        uid: UUID,
        ndid: UUID,
        course_id: UUID,
        title: str | None,
        created_by: UUID,
        sts: str,
        step: str
    ):
        return await self.conversation_repository.create_conversation(
            conversation_id=conversation_id,
            uid=uid,
            ndid=ndid,
            course_id=course_id,
            title=title,
            created_by=created_by,
            sts= sts,
            step= step
        )

    async def get_conversation(
        self,
        conversation_id: UUID,
    ):       
        return await self.conversation_repository.get_conversation(
            conversation_id
        )

    async def get_or_create_conversation(
        self,
        conversation_id: UUID | None,
        uid: UUID,
        ndid: UUID,
        course_id: UUID,
        title: str | None,
        created_by: UUID,
        sts: str,
        step: int
    ):
        if conversation_id:
            conversation = await self.get_conversation(conversation_id)

            if conversation:
                return conversation

        res = await self._create_conversation(
            conversation_id=conversation_id,
            uid=uid,
            ndid=ndid,
            course_id=course_id,
            title=title,
            created_by=created_by,
            sts= sts,
            step= step
        )
        await self.db.commit()
        return res

    async def add_message(self, conversation_id, user_id, sender, message):        
        
        res = await self.conversation_repository.create_message(
            conversation_id=conversation_id,
            sender=sender,
            message=message,
            created_by=user_id,
            updated_by=user_id
        )
        
        await self.conversation_repository.increment_message_count(conversation_id)

        await self.db.commit()

        return res

    async def get_chat_history(
        self,
        conversation_id: UUID,
        user_id: UUID,
        limit: int = 20
    ):
        res = await self.conversation_repository.get_recent_messages(
            conversation_id=conversation_id,
            limit=limit,
        )

        return res if res else []

    async def update_conversation(
        self,
        conversation_id: UUID,
        uid: UUID,
        ndid: UUID,
        course_id: UUID,
        title: str | None,
        created_by: UUID,
        sts: str,
        step: str,
        message: str,
        message_id: UUID
    ):
        await self.validate_conversation_access(conversation_id, uid)
        
        res = await self.update_message(
            conversation_id=conversation_id,
            message=message,
            message_id=message_id,
            user_id=uid
        )
        
        if not res:

            return await self._handle_chat(
                conversation_id= conversation_id,
                uid=uid,
                ndid=ndid,
                course_id=course_id,
                title=title,
                created_by=created_by,
                updated_by=updated_by,
                sts=sts,
                step=step
            )
            
        await self.db.commit()
        return res
    
    async def validate_conversation_access(self, conversation_id: UUID, user_id: UUID):
        conversation = await self.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if str(conversation.crtby) != str(user_id):
            raise HTTPException(status_code=403, detail="Unauthorized")

        return conversation
    
    async def get_context(self, chat_id, user_id):
        async with self.cache_lock:
            if chat_id not in self.chat_memory_cached:
                messages = await self.get_chat_history(chat_id, user_id, limit=20)
                self.chat_memory_cached[chat_id] = deque(messages, maxlen=20)
                if len(self.chat_memory_cached) > self.MAX_CACHED_CHATS:
                    oldest = next(iter(self.chat_memory_cached))
                    del self.chat_memory_cached[oldest]
            return self.chat_memory_cached[chat_id]


    async def save_message_cache(self, chat_id, user_id, role, message): 
        try:
            context = await self.get_context(chat_id, user_id)
            context.append({
                "role": role,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    
    async def _handle_chat(self,conversation_id: UUID,uid: UUID,ndid: UUID,course_id: UUID,title: str | None,created_by: UUID, updated_by: UUID,sts: str,step: int,message: str):
        try:
            await self._create_conversation(
                conversation_id= conversation_id,
                uid=uid,
                ndid=ndid,
                course_id=course_id,
                title=title,
                created_by=created_by,
                updated_by=updated_by,
                sts=sts,
                step=step,
            )
            await self.add_message(
                conversation_id= conversation_id,
                sender=sender,
                updated_by=updated_by,
                created_by=created_by,
            )
        except:
            await self.db.rollback()
            raise

    async def update_step(self, conversation_id: UUID, step: str):
        await self.conversation_repository.update_step(conversation_id, step)
        await self.db.commit()
    
    async def update_message(self, conversation_id: UUID, message: str, message_id: UUID, user_id: UUID):
        await self.validate_conversation_access(conversation_id, user_id)

        res = await self.conversation_repository.update_message(message, message_id)
        await self.db.commit()
        return res
    
    async def get_chunk_context(
        self,
        chunk_ids: list[UUID],
    ):
        if not chunk_ids:
            return []

        return await self.conversation_repository.get_chunk_context(
            chunk_ids
        )