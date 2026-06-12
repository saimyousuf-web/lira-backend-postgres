from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID


class ConversationRepository(ABC):

    # -----------------------------
    # Conversation Operations
    # -----------------------------

    @abstractmethod
    async def create_conversation(
        self,
        uid: UUID,
        ndid: UUID,
        cid: UUID,
        title: str,
        created_by: UUID,
    ):
        pass

    @abstractmethod
    async def get_conversation(
        self,
        conversation_id: UUID,
    ):
        pass

    @abstractmethod
    async def update_conversation(
        self,
        conversation_id: UUID,
        **kwargs,
    ):
        pass

    @abstractmethod
    async def increment_message_count(
        self,
        conversation_id: UUID,
    ):
        pass

    # -----------------------------
    # Message Operations
    # -----------------------------

    @abstractmethod
    async def create_message(
        self,
        conversation_id: UUID,
        sender: str,
        message: str,
        created_by: UUID,
        updated_by: UUID,
        metadata: Optional[dict] = None,
    ):
        pass

    @abstractmethod
    async def get_recent_messages(
        self,
        conversation_id: UUID,
        limit: int = 20,
    ) -> List:
        pass
