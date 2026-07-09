from uuid import UUID

from pydantic import BaseModel, field_serializer

from core.id_cypher import encrypt_id


class CategoryResponse(BaseModel):
    catid: UUID
    catnm: str

    @field_serializer("catid")
    def serialize_catid(self, value: UUID) -> str:
        return encrypt_id(value)