import uuid
from xml.dom import Node
from auth.main import get_current_user
from get_user_org_access_details.schema import UserOrgAccessResponse
from models.lira_access import LiraAccess
from models.nodes import Dept, Func, NodeType, Org
from models.user import User
from models.permissions import Permission
from models.role_permissions import RolePermission
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Depends
from core.db import get_db_session
from sqlalchemy import select,union

router = APIRouter()


@router.get("")
async def get_user_details(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    user_id = uuid.UUID(user.get("sub"))
    print("hello")
    try:
        user_row = await db.scalar(
            select(User).where(User.id == user_id)
        )

        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")

        user_name = user_row.first_name
        user_email = user_row.email

        access_response = await db.execute(
            select(LiraAccess).where(LiraAccess.uid == user_id)
        )
        access_items = access_response.scalars().all()

        if not access_items:
            return []

        role_ids = list({item.rlid for item in access_items if item.rlid})

        permission_names = []
        if role_ids:
            permission_response = await db.execute(
                select(Permission)
                .join(RolePermission, Permission.id == RolePermission.permission_id)
                .where(RolePermission.role_id.in_(role_ids))
            )
            permissions = permission_response.scalars().all()
            permission_names = [p.name for p in permissions]

        org_query = union(
            # direct org access
            select(Org.ndid.label("org_ndid"), Org.nm.label("org_name"), Org.prtndid.label("prtndid"))
            .join(LiraAccess, LiraAccess.ndid == Org.ndid)
            .where(LiraAccess.uid == user_id),

            # dept access -> org
            select(Org.ndid.label("org_ndid"), Org.nm.label("org_name"), Org.prtndid.label("prtndid"))
            .join(Dept, Dept.orgid == Org.ndid)
            .join(LiraAccess, LiraAccess.ndid == Dept.ndid)
            .where(LiraAccess.uid == user_id),

            # func access -> org
            select(Org.ndid.label("org_ndid"), Org.nm.label("org_name"), Org.prtndid.label("prtndid"))
            .join(Func, Func.orgid == Org.ndid)
            .join(LiraAccess, LiraAccess.ndid == Func.ndid)
            .where(LiraAccess.uid == user_id),
        ).subquery()

        org_response = await db.execute(select(org_query))
        org_rows = org_response.all()

        result = []
        seen_orgs = set()

        for row in org_rows:
            orgid = row.org_ndid
            if orgid in seen_orgs:
                continue
            seen_orgs.add(orgid)

            result.append(
                UserOrgAccessResponse(
                    userId=user_id,
                    name=user_name,
                    user_email=user_email,
                    orgid=orgid,
                    ndid=orgid,
                    ndty="ORG",
                    ndname=row.org_name,
                    prtndid=str(row.prtndid) if row.prtndid else "ROOT",
                    role="ADMIN",
                    permissions=permission_names,
                )
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"server error: {e}")