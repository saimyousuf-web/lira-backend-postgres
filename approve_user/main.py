from uuid import UUID
from dependencies.auth import require_permission
from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db_session
from models.user import User
from models.lira_access import LiraAccess

router = APIRouter()


@router.post("/{orgid}/{ndid}/{ndty}/{userId}")
async def approve_user(
    orgid: UUID = Path(...),
    ndid: UUID = Path(...),
    ndty: str = Path(...),
    userId: UUID = Path(...),
    # auth=Depends(require_permission("approve_user")),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        # Find user
        user_stmt = select(User).where(
            User.id == userId
        )

        result = await db.execute(user_stmt)
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        # Find access record for this node
        access_stmt = select(LiraAccess).where(
            LiraAccess.uid == userId,
            LiraAccess.ndid == ndid,
        )

        result = await db.execute(access_stmt)
        access = result.scalars().first()

        if not access:
            raise HTTPException(
                status_code=404,
                detail="User access not found",
            )

        user.is_active = True

        # Approve user
        access.isapr = True

        await db.commit()

        return {
            "status": "success",
            "message": "User approved successfully",
        }

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve user: {str(e)}",
        )