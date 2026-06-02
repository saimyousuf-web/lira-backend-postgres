from models.nodes import Dept, Func, Org
from sqlalchemy import select
from models.roles import Role
from sqlalchemy.exc import IntegrityError
import uuid
from uuid import UUID
from botocore.exceptions import ClientError
from models.lira_access import LiraAccess
from pydantic import BaseModel, EmailStr, Field
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
    name: str
    org_id: UUID = Field(alias="organization_id")
    dept_id: UUID = Field(alias="department_id")
    function_id: UUID
    role: str
    is_approved: bool = False

    class Config:
        populate_by_name = True


@router.post("")
async def register_client_user(
    payload: RegisterClientUserRequest,
    db: AsyncSession = Depends(get_db_session),
):
    try:
        # 1) role for learner
        role_result = await db.execute(
            select(Role).where(Role.name == "LEARNER")
        )
        role = role_result.scalar_one_or_none()

        if not role:
            raise HTTPException(status_code=404, detail="Role 'LEARNER' not found")

        # 2) validate org
        org = await db.scalar(
            select(Org).where(Org.ndid == payload.org_id)
        )
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # 3) validate dept belongs to org
        dept = await db.scalar(
            select(Dept).where(
                Dept.ndid == payload.dept_id,
                Dept.orgid == payload.org_id,
                Dept.prtndid == payload.org_id,
            )
        )
        if not dept:
            raise HTTPException(
                status_code=404,
                detail="Department not found for the selected organization",
            )

        # 4) validate function belongs to dept
        func = await db.scalar(
            select(Func).where(
                Func.ndid == payload.function_id,
                Func.orgid == payload.org_id,
                Func.prtndid == payload.dept_id,
            )
        )
        if not func:
            raise HTTPException(
                status_code=404,
                detail="Function not found for the selected department",
            )

        # 5) create user if not exists
        user = await db.scalar(
            select(User).where(User.id == payload.userId)
        )

        if not user:
            user = User(
                id=payload.userId,
                email=payload.email,
                first_name=payload.name,
                last_name="",
                is_active=True,
            )
            db.add(user)
            await db.flush()
        else:
            user.email = payload.email
            user.first_name = payload.name
            user.is_active = True

        # 6) attach learner at function level
        existing_access = await db.scalar(
            select(LiraAccess).where(
                LiraAccess.uid == payload.userId,
                LiraAccess.ndid == payload.function_id,
            )
        )

        if existing_access:
            existing_access.rlid = role.id
            existing_access.isact = True
            existing_access.isapr = payload.is_approved
        else:
            access = LiraAccess(
                uid=payload.userId,
                ndid=payload.function_id,
                rlid=role.id,
                isact=True,
                isapr=payload.is_approved,
            )
            db.add(access)

        await db.commit()

        return {
            "success": True,
            "message": "User registered successfully at function level",
            "userId": str(payload.userId),
            "orgId": str(payload.org_id),
            "deptId": str(payload.dept_id),
            "functionId": str(payload.function_id),
        }

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(e))

    except HTTPException:
        await db.rollback()
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))