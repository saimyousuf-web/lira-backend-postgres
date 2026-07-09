from uuid import UUID
from pydantic import BaseModel, field_serializer
from core.id_cypher import encrypt_id


class FunctionResponse(BaseModel):
    ndid: UUID
    prtndid: UUID
    name: str

    @field_serializer("ndid", "prtndid")
    def serialize_ids(self, value: UUID) -> str:
        return encrypt_id(value)


class GetAllFunctionsByDeptResponse(BaseModel):
    status_code: int
    success: bool
    functions: list[FunctionResponse]