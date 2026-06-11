from pydantic import BaseModel
from typing import List


class UserItemResponse(BaseModel):
    name: str
    email: str
    role: str | None = None


class GetAllUsersResponse(BaseModel):
    count: int
    users: List[UserItemResponse]