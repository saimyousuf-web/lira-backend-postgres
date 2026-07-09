from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_serializer

from core.id_cypher import encrypt_id


class ChildNodeResponse(BaseModel):
    ndid: UUID
    ndty: str
    name: str
    crtat: datetime
    updtat: datetime
    isact: bool

    @field_serializer("ndid")
    def serialize_ndid(self, value: UUID) -> str:
        return encrypt_id(value)


class ListNodesResponse(BaseModel):
    status: str
    message: str
    data: list[ChildNodeResponse]