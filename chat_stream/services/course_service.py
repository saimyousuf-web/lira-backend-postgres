from uuid import UUID

from repositories.postgres.course_repository import CourseRepository


class CourseService:

    def __init__(
        self,
        course_repository: CourseRepository,
    ):
        self.course_repository = course_repository

    async def get_course(
        self,
        course_id: UUID,
    ):
        return await self.course_repository.get_course(
            course_id
        )

    async def get_chunks(
        self,
        chunk_ids: list[UUID],
    ):
        if not chunk_ids:
            return []

        return await self.course_repository.get_chunks_by_ids(
            chunk_ids
        )

    async def get_modules(
        self,
        module_ids: list[UUID],
    ):
        if not module_ids:
            return []

        return await self.course_repository.get_modules_by_ids(
            module_ids
        )

    async def get_chunk_context(
        self,
        chunk_ids: list[UUID],
    ):
        if not chunk_ids:
            return []

        return await self.course_repository.get_chunk_context(
            chunk_ids
        )

    async def validate_course(
        self,
        course_id: UUID,
    ):
        course = await self.get_course(course_id)

        if not course:
            raise ValueError(
                f"Course {course_id} not found"
            )

        return course