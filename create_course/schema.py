from pydantic import BaseModel, Field

class CreateCourseRequest(BaseModel):
    name: str = Field(default="Name of the course")
    description: str = Field(default="Description of the course")
    category_id: str = Field(default="Category ID to associate with the course")
    node_ids: list[str] = Field(default="List of node IDs to associate with the course")