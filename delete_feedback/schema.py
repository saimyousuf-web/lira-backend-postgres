from pydantic import BaseModel
from datetime import datetime
from models.enums.feedback_status import FeedbackStatus


class UpdateFeedbackStatusRequest(BaseModel):
    status: FeedbackStatus
    sme_response: str | None = None
    created_at: datetime

class DeleteFeedbackResponse(BaseModel):
    success: bool
    message: str
    deleted: dict