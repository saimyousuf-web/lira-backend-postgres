from sqlite3 import IntegrityError
import uuid
from uuid import UUID
from botocore.exceptions import ClientError
from models.lira_access import LiraAccess
from pydantic import BaseModel, EmailStr
import boto3
from core.config import settings
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db_session
from auth.cognito import find_user
from models.user import User

router = APIRouter()

cognito = boto3.client("cognito-idp", region_name=settings.REGION)



class RegisterClientUserRequest(BaseModel):
    userId: UUID
    email: EmailStr
    function_id: UUID
    role_id: UUID
    is_approved: bool
    first_name: str
    last_name: str


@router.post("")
async def register_client_user(
    payload: RegisterClientUserRequest,
    db: AsyncSession = Depends(get_db_session),
):
    try:
        if not payload.userId or not payload.last_name or not payload.email or not payload.function_id or not payload.role_id:
            raise HTTPException(status_code=400, detail="Missing required fields")


        is_user = find_user(payload.userId, str(payload.email))
        if not is_user:
            raise HTTPException(
                status_code=404,
                detail=f"User '{payload.userId}' not found in Cognito user pool",
            )

        user = User(
            id=payload.userId,
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            is_active=True,
        )

        lira_access = LiraAccess(
            user_id=payload.userId,
            node_id=payload.function_id,
            role_id=payload.role_id,
            is_active=True,
            is_approved=payload.is_approved,
        )

        db.add(user)
        db.add(lira_access)
        await db.commit()

        return {
            "success": True,
            "message": "User added successfully",
        }

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="User already exists or invalid foreign key")

    except HTTPException:
        await db.rollback()
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


