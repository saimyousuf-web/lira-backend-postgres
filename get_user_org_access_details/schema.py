from uuid import UUID

from pydantic import BaseModel, field_serializer

from core.id_cypher import encrypt_id


class UserOrgAccessResponse(BaseModel):
    userId: UUID
    name: str
    user_email: str
    orgid: UUID
    ndid: UUID
    ndty: str
    ndname: str
    prtndid: str          
    # have made this parent id string explicitly because can be root
    role: str
    permissions: list[str]

    @field_serializer("userId", "orgid", "ndid")
    def serialize_ids(self, value: UUID):
        return encrypt_id(value)