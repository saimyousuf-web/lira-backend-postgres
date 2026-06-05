from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

from core.db import get_db_session
from dependencies.auth import authorize_user, get_current_user
from models.lira_access import LiraAccess
from models.nodes import Node,NodeType
from models.roles import Role
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
router = APIRouter()

@router.get("/{orgid}/{ndid}/{ndty}")
async def get_user_current_info(
    orgid: UUID,
    ndid: UUID,
    ndty: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    user_id = user.get("sub")

    # User details
    user_data = await db.scalar(
        select(User).where(User.id == user_id)
    )

    if not user_data:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user_name = f"{user_data.first_name} {user_data.last_name}"
    user_email = user_data.email
    is_approved = user_data.is_active

    # Role
    role_name = await db.scalar(
        select(Role.name)
        .join(LiraAccess, LiraAccess.rlid == Role.id)
        .where(
            LiraAccess.uid == user_id,
            LiraAccess.ndid == ndid
        )
    )

    if not role_name:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    # Node Type
    node_name = await db.scalar(
        select(NodeType.ty)
        .join(Node, Node.ndtyid == NodeType.id)
        .where(Node.id == ndid)
    )

    if not node_name:
        raise HTTPException(
            status_code=404,
            detail="Node type not found"
        )

    return {
        "status": "success",
        "status_code": 200,
        "message": "User current info fetched successfully",
        "data": {
            "userId": str(user_id),
            "name": user_name,
            "role": role_name,
            "is_approved": is_approved,
            "email": user_email,
            "node_name": node_name
        }
    }

    
    
    
