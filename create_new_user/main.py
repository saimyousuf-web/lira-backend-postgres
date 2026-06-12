from uuid import UUID
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from auth.main import get_current_user
from core.config import settings
from core.db import get_db_session
from create_new_user.schema import CreateUserRequest
from models.user import User
from models.roles import Role
from models.lira_access import LiraAccess
from models.nodes import Org, Dept, Func
import boto3

cognito = boto3.client(
    "cognito-idp",
    region_name=settings.REGION
)


router = APIRouter()



@router.post("")
async def create_user(
    payload: CreateUserRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    # cognito_created = False
    cognito_created = True
    try:
        # Check if email already exists
        # add cognito check also if either true return exception
        existing_user_result = await db.execute(
            select(User).where(
                User.email == payload.email
            )
        )

        existing_user = existing_user_result.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User already exists",
            )

        # validate org
        org_result = await db.execute(
            select(Org).where(
                Org.ndid == payload.organization_id,
                Org.isact.is_(True),
            )
        )

        org = org_result.scalars().first()

        if not org:
            raise HTTPException(
                status_code=404,
                detail="Organization not found",
            )

        role_name = payload.role.upper()

        target_node_id = None

        # ADMIN Validation
        if role_name == "ADMIN":
            target_node_id = payload.organization_id

        # SME & MANAGER Validation
        if role_name in ["SME", "MANAGER"]:

            if not payload.department_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"department_id is required for {role_name}",
                )

            dept_result = await db.execute(
                select(Dept).where(
                    Dept.ndid == payload.department_id,
                    Dept.orgid == payload.organization_id,
                    Dept.isact.is_(True),
                )
            )

            dept = dept_result.scalars().first()

            if not dept:
                raise HTTPException(
                    status_code=404,
                    detail="Department not found",
                )

            target_node_id = payload.department_id

        # LEARNER Validation
        elif role_name in ["LEARNER", "SUPERVISOR"]:

            if not payload.department_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"department_id is required for {role_name}",
                )

            if not payload.function_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"function_id is required for {role_name}",
                )

            func_result = await db.execute(
                select(Func).where(
                    Func.ndid == payload.function_id,
                    Func.orgid == payload.organization_id,
                    Func.prtndid == payload.department_id,
                    Func.isact.is_(True),
                )
            )

            func = func_result.scalars().first()

            if not func:
                raise HTTPException(
                    status_code=404,
                    detail="Function not found",
                )

            target_node_id = payload.function_id

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid role. Allowed values: ADMIN, SME, LEARNER",
            )

        # Get Role
        role_result = await db.execute(
            select(Role).where(
                Role.name == role_name
            )
        )

        role = role_result.scalars().first()

        if not role:
            raise HTTPException(
                status_code=404,
                detail="Role not found",
            )

        # Create Cognito User
        try:
            # cognito.admin_create_user(
            #     UserPoolId=settings.COGNITO_USER_POOL_ID,
            #     Username=payload.email,
            #     UserAttributes=[
            #         {
            #             "Name": "email",
            #             "Value": payload.email,
            #         },
            #         {
            #             "Name": "email_verified",
            #             "Value": "true",
            #         },
            #     ],
            #     DesiredDeliveryMediums=["EMAIL"],
            # )

            cognito_created = True

        except ClientError as e:
            raise HTTPException(
                status_code=400,
                detail=e.response["Error"]["Message"],
            )

        # Split Name
        name_parts = payload.name.strip().split(maxsplit=1)

        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Create User
        new_user = User(
            email=payload.email,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )

        db.add(new_user)

        await db.flush()

        # Create Access
        access = LiraAccess(
            uid=new_user.id,
            ndid=target_node_id,
            rlid=role.id,
            isact=True,
            isapr=True,
        )

        db.add(access)

        await db.commit()

        return {
            "status": "success",
            "message": "User created successfully",
            "user_id": str(new_user.id),
        }

    except HTTPException:
        raise

    except Exception as e:

        await db.rollback()

        if cognito_created:
            try:
                cognito.admin_delete_user(
                    UserPoolId=settings.COGNITO_USER_POOL_ID,
                    Username=payload.email,
                )
            except Exception:
                pass

        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}",
        )