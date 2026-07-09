from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db_session
from core.id_cypher import decrypt_id
from get_chat_history_by_id.schema import ChatHistoryResponse, MessageResponse
from models.session import Session


router = APIRouter()


@router.get(
    "/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}/{course_id}/{chat_id}",
    response_model=ChatHistoryResponse,
)
async def get_history(
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    course_id: str = Path(...),
    chat_id: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        org_id = decrypt_id(ctx_orgid)
        node_id = decrypt_id(ctx_ndid)
        course_uuid = decrypt_id(course_id)
        chat_uuid = decrypt_id(chat_id)

        stmt = (
            select(Session)
            .where(Session.convid == chat_uuid)
            .order_by(Session.crtat.asc())
        )

        result = await db.execute(stmt)
        messages = result.scalars().all()

        return ChatHistoryResponse(
            chatId=chat_uuid,
            messages=[
                MessageResponse(
                    messageId=msg.id,
                    sender="user" if msg.sender == "USER" else "bot",
                    text=msg.msgtxt,
                    timestamp=msg.crtat,
                    courseId=course_uuid,
                )
                for msg in messages
            ],
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))