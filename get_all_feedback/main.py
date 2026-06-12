from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from core.db import get_db_session
from get_all_feedback.schema import FeedbackResponse
from models.feedback import Feedback
from models.course import Course
from models.session import Session

router = APIRouter()


@router.get(
    "/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}",
    response_model=list[FeedbackResponse],
)
async def get_all_feedback_router(
    ctx_orgid: uuid.UUID = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    try:

        stmt = (
            select(
                Feedback,
                Course.nm.label("course_name"),
                Session.msgtxt.label("event_message"),
            )
            .join(
                Course,
                Feedback.cid == Course.id,
            )
            .join(
                Session,
                Feedback.sessid == Session.id,
            )
            .where(
                Feedback.ndid == ctx_orgid
            )
            .order_by(
                Feedback.crtat.desc()
            )
        )

        result = await db.execute(stmt)
        rows = result.all()

        return [
            FeedbackResponse(
                fid=str(feedback.id),
                cid=str(feedback.cid),
                cnm=course_name,
                convid=str(feedback.convid),
                crtat=feedback.crtat,
                evtmsg=event_message,
                evtquery=feedback.sessquery,
                feedtxt=feedback.feedtxt,
                feedty=feedback.feedty,
                rsn=feedback.rsn,
                smeres=feedback.smeres,
                sts=feedback.sts.value,
            )
            for feedback, course_name, event_message in rows
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )