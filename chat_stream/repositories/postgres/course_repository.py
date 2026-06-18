from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import ARRAY

from chat_stream.repositories.Icourse import CourseRepository

from models.course import Course
from models.module import Module
from models.chunks import Chunk


class PostgresCourseRepository(CourseRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_course(self, course_id: UUID,) -> Course | None:
        result = await self.db.execute(
            select(Course)
            .where(Course.id == course_id)
        )

        return result.scalar_one_or_none()

    async def get_chunks_by_ids(self, chunk_ids: list[UUID],) -> list[Chunk]:

        if not chunk_ids:
            return []

        result = await self.db.execute(
            select(Chunk)
            .where(Chunk.id.in_(chunk_ids))
        )

        return result.scalars().all()

    async def get_modules_by_ids(self, module_ids: list[UUID],) -> list[Module]:

        if not module_ids:
            return []

        result = await self.db.execute(
            select(Module)
            .where(Module.id.in_(module_ids))
        )

        return result.scalars().all()

        