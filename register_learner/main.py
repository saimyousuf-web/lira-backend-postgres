from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from auth.cognito import find_user
from datetime import datetime, timezone

# from models.user_access import UserAccess

router = APIRouter()

engine = create_engine(settings.DATABASE_URL)
connection = engine.connect()

class RegisterClientUserRequest(BaseModel):
    userId: str
    email: EmailStr
    name:str
    organization_id: str
    function_id:str
    role: str
    is_approved: bool


def add_user_to_access_table(
    db: Session,
    userId: str,
    organization_id: str,
    function_id: str,
    role: str,
    is_approved: bool
):
    access = UserAccess(
        user_id=userId,
        organization_id=organization_id,
        function_id=function_id,
        role=role,
        is_approved=is_approved,
        itc=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(access)
    db.flush()
    return access

@router.post("")
async def register_client_user(payload:RegisterClientUserRequest):
    try:
        print(payload)
        userId = payload.userId
        name = payload.name
        email = payload.email
        organization_id = payload.organization_id
        function_id = payload.function_id
        role = payload.role
        is_approved = payload.is_approved

        if not userId or not name or not email or not organization_id or not function_id or not role:
            raise HTTPException(status_code=400, detail="Missing required fields")
        is_user = find_user(userId, email)
        if not is_user:
            raise HTTPException(status_code=404, detail=f"User '{userId}' not found in Cognito user pool")