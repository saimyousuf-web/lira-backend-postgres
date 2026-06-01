from pydantic import BaseModel
from uuid import UUID


class Organization(BaseModel):
    name: str
    ndid: UUID


class GetAllOrganizationsResponse(BaseModel):
    status_code: int
    status: str
    count: int
    organizations: list[Organization]