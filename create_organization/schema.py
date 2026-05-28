from pydantic import BaseModel, Field

class CreateOrganizationRequest(BaseModel):
    name: str = Field(..., example="Ford Motor Company", max_length=255, min_length=1)

class CreateOrganizationResponse(BaseModel):
    status: str
    status_code: int
    message: str
    data: dict 