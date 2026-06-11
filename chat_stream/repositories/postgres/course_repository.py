from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def get_chunk_context(self, chunk_ids: list[UUID],) -> list[dict]:

        if not chunk_ids:
            return []

        result = await self.db.execute(
            select(
                Chunk.id.label("chunk_id"),
                Chunk.txt.label("chunk_text"),
                Chunk.imgkeys.label("image_keys"),

                Module.id.label("module_id"),
                Module.nm.label("module_name"),
                Module.ty.label("module_type"),

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

        return [dict(row) for row in rows]