from datetime import datetime
from pydantic import BaseModel

class FeedbackResponse(BaseModel):
    fid: str
    cid: str
    cnm: str
    convid: str
    crtat: datetime
    evtmsg: str | None
    evtquery: str | None
    feedtxt: str | None
    feedty: str | None
    rsn: str | None
    smeres: str | None
    sts: str