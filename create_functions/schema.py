from pydantic import BaseModel, Field
from typing import List

class CreateFunctionsRequest(BaseModel):
    department_id: str = Field(
        ...,
        description="ID of the department under which functions will be created"
    )
    names: List[str] = Field(
        ...,
        min_items=1,
        description="List of function names to create under this department"
    )

class CreateFunctionsResponse(BaseModel):
    status: str = Field(..., description="Status of the function creation operation")
    message: str = Field(..., description="Detailed message about the function creation result")
    data: List[dict] = Field(
        default_factory=list,
        description="List of created functions with their details"
    )