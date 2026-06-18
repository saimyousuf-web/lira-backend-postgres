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
        try:
            result = await self.db.execute(
                select(Feedback.smeres)
                .where(
                    Feedback.ndid == organization_id,
                    Feedback.cid == course_id,
                )
                .order_by(Feedback.crtat.desc())
                .limit(limit)
            )

            # returns list of strings instead of full objects
            res = result.scalars().all()
            return res

        except Exception as e:
            print("Exception:", str(e))
            raise
