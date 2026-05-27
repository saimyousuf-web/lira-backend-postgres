from pydantic import BaseModel

class CreateDepartmentsRequest(BaseModel):
    names: list[str]

class CreateDepartmentsResponse(BaseModel):
    status: str
    message: str
    data : list[dict]