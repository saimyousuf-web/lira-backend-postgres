from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, field_serializer

from core.id_cypher import encrypt_id


class ModuleResponse(BaseModel):
    moid: UUID
    monm: str
    moty: str | None
    crtat: datetime
    sts: str |None
    isapr: bool
    s3loc: str | None

    @field_serializer("moid")
    def serialize_moid(self, value: UUID) -> str:
        return encrypt_id(value)