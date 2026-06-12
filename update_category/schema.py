from pydantic import BaseModel, model_validator
from typing import Optional


class UpdateCategoryRequest(BaseModel):
    nm: str = None
    dsc: str = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.nm and not self.dsc:
            raise ValueError("At least one field (nm or dsc) must be provided")
        return self
