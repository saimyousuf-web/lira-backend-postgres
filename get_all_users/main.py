from uuid import UUID

from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.main import get_current_user
from core.db import get_db_session
from models.user import User
from models.lira_access import LiraAccess
from models.roles import Role
from models.nodes import Org, Dept, Func

router = APIRouter()


@router.get("/{orgid}/{ndid}/{ndty}")

async def get_all_users(
    orgid: UUID = Path(...),
    # user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        # Get Org
        org_result = await db.execute(
            select(Org).where(
                Org.ndid == orgid,
                Org.isact.is_(True),
            )
        )

        org = org_result.scalars().first()

        if not org:
            raise HTTPException(
                status_code=404,
                detail="Organization not found",
            )

        # Get all departments in the org
        dept_result = await db.execute(
            select(
                Dept.ndid,
                Dept.nm,
            ).where(
                Dept.orgid == orgid,
                Dept.isact.is_(True),
            )
        )

        depts = dept_result.all()

        # Get all functions in the org
        func_result = await db.execute(
            select(
                Func.ndid,
                Func.nm,
            ).where(
                Func.orgid == orgid,
                Func.isact.is_(True),
            )
        )

        funcs = func_result.all()

        # Build node lookup map
        node_name_map = {
            org.ndid: org.nm,
        }

        for dept in depts:
            node_name_map[dept.ndid] = dept.nm

        for func in funcs:
            node_name_map[func.ndid] = func.nm

        # Build all node ids belonging to this org
        node_ids = [orgid]

        node_ids.extend(
            [dept.ndid for dept in depts]
        )

        node_ids.extend(
            [func.ndid for func in funcs]
        )

        # Get users assigned to any node in this org
        stmt = (
            select(
                User.first_name,
                User.last_name,
                User.email,
                Role.name.label("role"),
                LiraAccess.ndid.label("node_id"),
            )
            .join(
                LiraAccess,
                User.id == LiraAccess.uid,
            )
            .join(
                Role,
                LiraAccess.rlid == Role.id,
            )
            .where(
                LiraAccess.ndid.in_(node_ids),
            )
            .order_by(
                User.first_name,
                User.last_name,
            )
        )

        result = await db.execute(stmt)
        rows = result.all()

        users = []

        for row in rows:
            users.append(
                {
                    "name": f"{row.first_name} {row.last_name}",
                    "email": row.email,
                    "role": row.role,
                    "node_name": node_name_map.get(row.node_id),
                }
            )

        return {
            "count": len(users),
            "users": users,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch users: {str(e)}",
        )
    


    # 834236b7-a4dd-45fa-894c-82fc09c1f6ef