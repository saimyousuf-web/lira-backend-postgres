from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_serializer

from core.id_cypher import encrypt_id


class MessageResponse(BaseModel):
    messageId: UUID
    sender: str
    text: str
    timestamp: datetime | None
    courseId: UUID

    @field_serializer("messageId", "courseId")
    def serialize_ids(self, value: UUID) -> str:
        return encrypt_id(value)


class ChatHistoryResponse(BaseModel):
    chatId: UUID
    messages: list[MessageResponse]

    @field_serializer("chatId")
    def serialize_chat_id(self, value: UUID) -> str:
        return encrypt_id(value)