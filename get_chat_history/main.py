from collections import defaultdict
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, Path,HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db_session
from auth.main import get_current_user
from core.id_cypher import decrypt_id
from get_chat_history.schema import ChatResponse, ConversationResponse, GetUserChatsResponse
from models.conversation import Conversation
from models.course import Course

router = APIRouter()

@router.get(
    "/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}",
    response_model=GetUserChatsResponse,
)
async def list_user_chats(
    ctx_orgid_enc: str = Path(..., alias="ctx_orgid", description="Organization ID"),
    ctx_ndid_enc: str = Path(..., alias="ctx_ndid",description="Node ID"),
    ctx_ndty: str = Path(..., description="Node Type"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    user_id = UUID(user.get("sub"))

    try:
        ctx_orgid = decrypt_id(ctx_orgid_enc)
        ctx_ndid = decrypt_id(ctx_ndid_enc)
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

            cid = row.cid

            if cid not in grouped:
                grouped[cid] = ChatResponse(
                    cid=cid,
                    cnm=row.course_name,
                    updat=row.updat,
                    conversations=[],
                )

            grouped[cid].conversations.append(
                ConversationResponse(
                    convid=row.id,
                    title=row.title,
                    updat=row.updat,
                )
            )

        chats = list(grouped.values())

        chats.sort(
            key=lambda chat: chat.updat,
            reverse=True,
        )

        return GetUserChatsResponse(
            status_code=200,
            chats=chats,
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"server error: {e}"
        )