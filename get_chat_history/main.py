from collections import defaultdict
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, Path,HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db_session
from dependencies.auth import get_current_user
from models.conversation import Conversation
from models.course import Course

router = APIRouter()

@router.get("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}")
async def get_conversations(
    ctx_orgid: UUID = Path(..., description="Organization ID"),
    ctx_ndid: UUID = Path(..., description="Node ID"),
    ctx_ndty: str = Path(..., description="Node Type"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    user_id = UUID(user.get("sub"))

    try:
        response = await db.execute(
            select(
                Conversation.id,
                Conversation.title,
                Conversation.updat,
                Conversation.cid,
                Course.nm.label("course_name")
            )
            .join(
                Course,
                Course.id == Conversation.cid
            )
            .where(
                Conversation.uid == user_id,
                Conversation.ndid == ctx_ndid,
                Conversation.sts == "ACTIVE"
            )
            .order_by(
                Conversation.updat.desc()
            )
        )

        rows = response.all()

        if not rows:
            return {
                "status_code": 200,
                "chats": []
            }

        grouped = {}

        for row in rows:

            cid = str(row.cid)

            if cid not in grouped:
                grouped[cid] = {
                    "cid": cid,
                    "cnm": row.course_name,
                    "updat": row.updat,
                    "conversations": []
                }

            grouped[cid]["conversations"].append(
                {
                    "convid": str(row.id),
                    "title": row.title,
                    "updat": row.updat
                }
            )

        chats = list(grouped.values())

        chats.sort(
            key=lambda chat: chat["updat"],
            reverse=True
        )

        return {
            "status_code": 200,
            "chats": chats
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"server error: {e}"
        )