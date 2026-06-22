from pydantic import BaseModel, Field

class CreateCatCourseRequest(BaseModel):
    course_id: str = Field(..., description="ID of the course to be associated with the category")
    category_id: str = Field(..., description="ID of the category to which the course will be associated")