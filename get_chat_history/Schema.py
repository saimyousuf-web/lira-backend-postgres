from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_serializer

from core.id_cypher import encrypt_id


class ConversationResponse(BaseModel):
    convid: UUID
    title: str
    updat: datetime

    @field_serializer("convid")
    def serialize_conversation_id(self, value: UUID) -> str:
        return encrypt_id(value)


class ChatResponse(BaseModel):
    cid: UUID
    cnm: str
    updat: datetime
    conversations: list[ConversationResponse]

    @field_serializer("cid")
    def serialize_course_id(self, value: UUID) -> str:
        return encrypt_id(value)


class GetUserChatsResponse(BaseModel):
    status_code: int
    chats: list[ChatResponse]