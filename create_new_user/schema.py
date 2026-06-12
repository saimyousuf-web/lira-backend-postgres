
from uuid import UUID

from pydantic import BaseModel, EmailStr


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str
    organization_id: UUID
    role: str
    department_id: UUID | None = None
    function_id: UUID | None = None
