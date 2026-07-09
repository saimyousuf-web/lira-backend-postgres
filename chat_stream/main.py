from fastapi import APIRouter, Body, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Optional
import asyncio
from datetime import datetime
import uuid
from core.db import get_db_session
from auth.main import get_current_user
from chat_stream.services.rag_service import RagService
from pydantic import BaseModel
from chat_stream.repositories.postgres.course_repository import PostgresCourseRepository
from chat_stream.repositories.postgres.conversation_repository import PostgresConversationRepository
from chat_stream.repositories.postgres.feedback_repository import PostgresFeedbackRepository
from chat_stream.services.conversation_service import ConversationService
from core.id_cypher import decrypt_id
from cryptography.fernet import InvalidToken
router = APIRouter()

class ChatRequest(BaseModel):
    chat_id: Optional[str] = None
    orgid: str
    ndid: str
    ndty: str
    active_message: str
    active_message_checkbox: Optional[Dict[str, str]] = None
    coach_mode:bool
    voice_mode: Optional[bool] = False
    initial_message: Optional[str] = None
    course_id: str 


@router.post("")
async def stream_chat(
    data: ChatRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = data.model_dump()

        payload["orgid"] = decrypt_id(payload["orgid"])
        payload["ndid"] = decrypt_id(payload["ndid"])
        payload["course_id"] = decrypt_id(payload["course_id"])

        if payload.get("chat_id"):
            payload["chat_id"] = decrypt_id(payload["chat_id"])

        conversation_repo = PostgresConversationRepository(db)
        feedback_repo = PostgresFeedbackRepository(db)

        conversation_service = ConversationService(
            conversation_repo,
            db,
        )

        rag_service = RagService(
            conversation_service=conversation_service,
            feedback_repo=feedback_repo,
        )

        return await rag_service.execute(
            data=payload,
            user=user,
        )

    except InvalidToken:
        raise HTTPException(
            status_code=400,
            detail="Invalid encrypted ID",
        )

@router.post("/save")
async def save_response(
    data: Dict,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = dict(data)

        if payload.get("orgid"):
            payload["orgid"] = decrypt_id(payload["orgid"])

        if payload.get("ndid"):
            payload["ndid"] = decrypt_id(payload["ndid"])

        if payload.get("course_id"):
            payload["course_id"] = decrypt_id(payload["course_id"])

        if payload.get("chat_id"):
            payload["chat_id"] = decrypt_id(payload["chat_id"])

        conversation_repo = PostgresConversationRepository(db)
        feedback_repo = PostgresFeedbackRepository(db)

        conversation_service = ConversationService(
            conversation_repo,
            db,
        )

        rag_service = RagService(
            conversation_service=conversation_service,
            feedback_repo=feedback_repo,
        )

        return await rag_service.save(
            data=payload,
            user=user,
        )

    except InvalidToken:
        raise HTTPException(
            status_code=400,
            detail="Invalid encrypted ID",
        )