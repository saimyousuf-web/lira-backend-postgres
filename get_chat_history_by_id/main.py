from uuid import UUID
from fastapi import APIRouter, Depends,Path, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from auth.main import get_current_user
from core.db import get_db_session
from models.session import Session

router = APIRouter()


@router.get("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}/{course_id}/{chat_id}")
async def get_history(
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    course_id: str = Path(...),
    chat_id: str = Path(...),
    # user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        stmt = (
            select(Session)
            .where(Session.convid == UUID(chat_id))
            .order_by(Session.crtat.asc())
        )

        result = await db.execute(stmt)
        messages = result.scalars().all()

        print(f"Fetched {len(messages)} messages for chat_id: {chat_id}")

        formatted_messages = [
            {
                "messageId": str(msg.id),
                "sender": "user" if msg.sender == "USER" else "bot",
                "text": msg.msgtxt,
                "timestamp": msg.crtat if msg.crtat else None,
                "courseId": course_id,
            }
            for msg in messages
        ]

        return {
            "chatId": chat_id,
            "messages": formatted_messages,
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat_id format")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))