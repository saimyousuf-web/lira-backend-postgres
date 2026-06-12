from uuid import UUID

from pydantic import BaseModel

class CategoryResponse(BaseModel):
    catid: UUID
    catnm : str