from pydantic import BaseModel,Field
from datetime import datetime
from models.enums.feedback_status import FeedbackStatus


class UpdateFeedbackStatusRequest(BaseModel):
    status: FeedbackStatus
    sme_response: str | None = Field(
        default=None,
        alias="sme_resposne"
    )
    # needs to fixed on Frontend its a typo
    created_at: datetime