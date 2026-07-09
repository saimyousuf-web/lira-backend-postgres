from uuid import UUID

from pydantic import BaseModel, field_serializer

from core.id_cypher import encrypt_id


class UserCurrentInfoResponse(BaseModel):
    userId: UUID
    name: str
    role: str
    is_approved: bool
    email: str
    node_name: str

    @field_serializer("userId")
    def serialize_user_id(self, value: UUID) -> str:
        return encrypt_id(value)