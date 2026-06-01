from pydantic import BaseModel, Field

class CreateCourseRequest(BaseModel):
    name: str
    description: str = Field(default="")