import uuid
from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from auth.main import get_current_user
from core.db import get_db_session
from models.feedback import Feedback
from models.enums.feedback_status import FeedbackStatus
from update_feedback_status.schema import UpdateFeedbackStatusRequest

router = APIRouter()


@router.put("/{org_id}/{ndid}/{ndty}/{course_id}/{feedback_id}")
async def update_feedback_status(
    payload: UpdateFeedbackStatusRequest,
    org_id: uuid.UUID = Path(...),
    ndid: uuid.UUID = Path(...),
    ndty: str = Path(...),
    course_id: uuid.UUID = Path(...),
    feedback_id: uuid.UUID = Path(...),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Feedback).where(
        Feedback.id == feedback_id,
        Feedback.cid == course_id,
        Feedback.ndid == ndid,
        Feedback.isact.is_(True),
    )

    result = await db.execute(stmt)
    feedback = result.scalar_one_or_none()

    if not feedback:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found",
        )

    feedback.sts = payload.status
    feedback.smeres = payload.sme_response
    feedback.updby = user["sub"]  # adjust based on your token structure

    await db.commit()
    await db.refresh(feedback)

    return {
        "status": "success",
        "message": "Feedback status updated successfully",
        "data": {
            "fid": str(feedback.id),
            "cid": str(feedback.cid),
            "convid": str(feedback.convid),
            "feedtxt": feedback.feedtxt,
            "smeres": feedback.smeres,
            "updby": user["sub"],
            "crtby": str(feedback.crtby) if feedback.crtby else None,
            "crtat": feedback.crtat.isoformat(),
            "updat": feedback.updat.isoformat(),
            "rsn": feedback.rsn,
            "sts": feedback.sts.value,
            "feedty": feedback.feedty,
            "isact": feedback.isact,
        },
    }