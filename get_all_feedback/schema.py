from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_serializer

from core.id_cypher import encrypt_id


class FeedbackResponse(BaseModel):
    fid: UUID
    cid: UUID
    cnm: str
    convid: UUID
    crtat: datetime
    evtmsg: str | None
    evtquery: str | None
    feedtxt: str | None
    feedty: str | None
    rsn: str | None
    smeres: str | None
    sts: str

    @field_serializer("fid", "cid", "convid")
    def serialize_ids(self, value: UUID) -> str:
        return encrypt_id(value)