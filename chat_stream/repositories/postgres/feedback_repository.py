from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chat_stream.repositories.Ifeedback import FeedbackRepository
from models.feedback import Feedback


class PostgresFeedbackRepository(FeedbackRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_top_feedbacks(
        self,
        organization_id: UUID,
        course_id: UUID,
        limit: int = 3,
    ):

        result = await self.db.execute(
            select(Feedback)
            .where(
                Feedback.cid == course_id,
                Feedback.isact.is_(True),
                Feedback.feedty == "Positive",
            )
            .order_by(
                Feedback.crtat.desc()
            )
            .limit(limit)
        )

        return result.scalars().all()