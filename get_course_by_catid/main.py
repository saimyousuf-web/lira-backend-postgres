from cryptography.fernet import InvalidToken

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db_session
from core.id_cypher import decrypt_id
from dependencies.auth import get_current_user
from models.lira_access import LiraAccess
from models.nodes import Node, NodeType
from models.roles import Role
from models.user import User

from get_user_current_info.schema import UserCurrentInfoResponse

router = APIRouter()


@router.get(
    "/{orgid}/{ndid}/{ndty}",
    response_model=UserCurrentInfoResponse,
)
async def get_user_current_info(
    orgid: str,
    ndid: str,
    ndty: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        node_id = decrypt_id(ndid)

        user_id = user.get("sub")

        # User details
        user_data = await db.scalar(
            select(User).where(User.id == user_id)
        )

        if not user_data:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        # Role
        role_name = await db.scalar(
            select(Role.name)
            .join(LiraAccess, LiraAccess.rlid == Role.id)
            .where(
                LiraAccess.uid == user_id,
                LiraAccess.ndid == node_id,
            )
        )

        if not role_name:
            raise HTTPException(
                status_code=404,
                detail="Role not found",
            )

        # Node Type
        node_name = await db.scalar(
            select(NodeType.ty)
            .join(Node, Node.ndtyid == NodeType.id)
            .where(Node.id == node_id)
        )

        if not node_name:
            raise HTTPException(
                status_code=404,
                detail="Node type not found",
            )

        return UserCurrentInfoResponse(
            userId=user_data.id,
            name=f"{user_data.first_name} {user_data.last_name}",
            role=role_name,
            is_approved=user_data.is_active,
            email=user_data.email,
            node_name=node_name,
        )

    except InvalidToken:
        raise HTTPException(
            status_code=400,
            detail="Invalid encrypted ID",
        )