from abc import ABC, abstractmethod
from uuid import UUID


class FeedbackRepository(ABC):

    @abstractmethod
    async def get_top_feedbacks(
        self,
        organization_id: UUID,
        course_id: UUID,
        limit: int = 3,
    ):
        pass