from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime


class ConversationItemResponse(BaseModel):
    convid: UUID
    title: str | None
    updat: datetime


class ChatResponse(BaseModel):
    cid: UUID
    cnm: str
    updat: datetime
    conversations: List[ConversationItemResponse]


class ConversationListResponse(BaseModel):
    status_code: int
    chats: List[ChatResponse]