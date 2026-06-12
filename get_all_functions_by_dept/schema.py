from pydantic import BaseModel
from uuid import UUID


class FunctionResponse(BaseModel):
    ndid: UUID
    prtndid: UUID
    name: str


class GetAllFunctionsByDeptResponse(BaseModel):
    status_code: int
    success: bool
    functions: list[FunctionResponse]