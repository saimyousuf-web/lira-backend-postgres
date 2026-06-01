from pydantic import BaseModel
from uuid import UUID


class DepartmentResponse(BaseModel):
    ndid: UUID
    prtndid: UUID
    name: str


class GetAllDepartmentsByOrgResponse(BaseModel):
    status_code: int
    success: bool
    departments: list[DepartmentResponse]