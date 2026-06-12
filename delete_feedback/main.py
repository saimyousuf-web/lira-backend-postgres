from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from core.db import get_db_session
from models.feedback import Feedback
from delete_feedback.schema import DeleteFeedbackResponse

router = APIRouter()


@router.delete(
    "/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}/{course_id}/{feedback_id}",
    response_model=DeleteFeedbackResponse,
)
async def delete_feedback(
    ctx_orgid: uuid.UUID = Path(...),
    ctx_ndid: uuid.UUID = Path(...),
    ctx_ndty: str = Path(...),
    course_id: uuid.UUID = Path(...),
    feedback_id: uuid.UUID = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        result = await db.execute(
            select(Feedback).where(
                Feedback.id == feedback_id
            )
        )

        feedback = result.scalar_one_or_none()

        if not feedback:
            raise HTTPException(
                status_code=404,
                detail="Feedback not found."
            )

        deleted_feedback = {
            "id": str(feedback.id),
            "uid": str(feedback.uid),
            "cid": str(feedback.cid),
            "convid": str(feedback.convid),
            "sessid": str(feedback.sessid),
            "sessquery": feedback.sessquery,
            "feedtxt": feedback.feedtxt,
            "feedty": feedback.feedty,
            "rsn": feedback.rsn,
            "smeres": feedback.smeres,
            "sts": feedback.sts.value if feedback.sts else None,
            "isact": feedback.isact,
            "crtat": feedback.crtat.isoformat() if feedback.crtat else None,
            "updat": feedback.updat.isoformat() if feedback.updat else None,
            "crtby": str(feedback.crtby) if feedback.crtby else None,
            "updby": str(feedback.updby) if feedback.updby else None,
            "ndid": str(feedback.ndid),
        }

        await db.delete(feedback)
        await db.commit()

        return DeleteFeedbackResponse(
            success=True,
            message="Feedback deleted successfully.",
            deleted=deleted_feedback,
        )

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}",
        )