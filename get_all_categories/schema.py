from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_serializer
from core.id_cypher import encrypt_id


class CategoryResponse(BaseModel):
    catid: UUID
    catnm: str
    desc: str | None
    crtat: datetime

    @field_serializer("catid")
    def serialize_id(self, value: UUID) -> str:
        return encrypt_id(value)