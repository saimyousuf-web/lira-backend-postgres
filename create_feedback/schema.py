from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class CreateFeedbackRequest(BaseModel):
    course_id: UUID
    convid: UUID
    sessid: UUID

    cnm: str

    feedback_text: str | None = None
    reason: str | None = None
    event_query: str | None = None

    event_message: str

    feedback_type: Literal["Positive", "Negative"]


class CreateFeedbackResponse(BaseModel):
    status: str
    message: str
    feedback_id: UUID