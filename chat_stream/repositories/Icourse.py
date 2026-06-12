from abc import ABC, abstractmethod
from typing import List
from uuid import UUID


class CourseRepository(ABC):

    @abstractmethod
    async def get_course(
        self,
        course_id: UUID,
    ):
        pass

    @abstractmethod
    async def get_modules_by_ids(
        self,
        module_ids: List[UUID],
    ):
        pass

    @abstractmethod
    async def get_chunks_by_ids(
        self,
        chunk_ids: List[UUID],
    ):
        pass