from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from auth.main import get_current_user
from dependencies.auth import require_permission
from core.db import get_db_session
from create_feedback.schema import CreateFeedbackRequest, CreateFeedbackResponse
from models.enums.feedback_status import FeedbackStatus
from models.feedback import Feedback

router = APIRouter()


@router.post("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}",response_model=CreateFeedbackResponse)
async def create_feedback(
    payload: CreateFeedbackRequest,
    ctx_orgid: uuid.UUID = Path(...),
    ctx_ndid: uuid.UUID = Path(...),
    ctx_ndty: str = Path(...),
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),

):
    try:
        user_id = uuid.UUID(user["sub"])

        feedback = Feedback(
            uid=user_id,
            cid=payload.course_id,
            convid=payload.convid,
            sessid=payload.sessid,

            cnm=payload.cnm,

            sessquery=payload.event_query,
            sessmsg=payload.event_message,

            feedtxt=payload.feedback_text,
            feedty=payload.feedback_type,
            rsn=payload.reason,

            sts=FeedbackStatus.PENDING,
            isact=True,

            crtby=user_id,
            updby=user_id,

            ndid=ctx_ndid,
        )

        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)

        return {
    "status": "success",
    "message": "Feedback inserted successfully",
    "feedback_id": feedback.id
}

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid UUID provided: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )