from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from dependencies.auth import require_permission
from core.db import get_db_session
from models.nodes import Node, NodeType, Org, Dept, Func

router = APIRouter()


@router.get("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}/node/{target_ndty}/{target_ndid}/children")
async def list_nodes(
    ctx_orgid: str,
    ctx_ndid: str,
    ctx_ndty: str,
    target_ndty: str,
    target_ndid: str,
    db: AsyncSession = Depends(get_db_session),
):
    try:
        response = []

        if target_ndty == "ORG":
            target_stmt = select(Org).where(
                Org.ndid == target_ndid,
                Org.isact.is_(True),
            )
            result = await db.execute(target_stmt)
            target = result.scalars().first()

            if not target or str(target.ndid) != str(ctx_orgid):
                raise HTTPException(status_code=404, detail="Node not found")

            children_stmt = (
                select(
                    Dept.ndid.label("ndid"),
                    NodeType.ty.label("ndty"),
                    Dept.nm.label("name"),
                    Dept.crtat.label("crtat"),
                    Dept.updat.label("updtat"),
                    Dept.isact.label("isact"),
                )
                .join(Node, Node.id == Dept.ndid)
                .join(NodeType, NodeType.id == Node.ndtyid)
                .where(
                    Dept.prtndid == target_ndid,
                    Dept.isact.is_(True),
                )
            )

            result = await db.execute(children_stmt)
            children = result.all()

        elif target_ndty == "DEPT":
            target_stmt = select(Dept).where(
                Dept.ndid == target_ndid,
                Dept.isact.is_(True),
            )
            result = await db.execute(target_stmt)
            target = result.scalars().first()

            if not target or str(target.prtndid) != str(ctx_orgid):
                raise HTTPException(status_code=404, detail="Node not found")

            children_stmt = (
                select(
                    Func.ndid.label("ndid"),
                    NodeType.ty.label("ndty"),
                    Func.nm.label("name"),
                    Func.crtat.label("crtat"),
                    Func.updat.label("updtat"),
                    Func.isact.label("isact"),
                )
                .join(Node, Node.id == Func.ndid)
                .join(NodeType, NodeType.id == Node.ndtyid)
                .where(
                    Func.prtndid == target_ndid,
                    Func.isact.is_(True),
                )
            )

            result = await db.execute(children_stmt)
            children = result.all()

        elif target_ndty == "FUNC":
            target_stmt = select(Func).where(
                Func.ndid == target_ndid,
                Func.isact.is_(True),
            )
            result = await db.execute(target_stmt)
            target = result.scalars().first()

            if not target:
                raise HTTPException(status_code=404, detail="Node not found")

            parent_dept_stmt = select(Dept).where(
                Dept.ndid == target.prtndid,
                Dept.isact.is_(True),
            )
            result = await db.execute(parent_dept_stmt)
            parent_dept = result.scalars().first()

            if not parent_dept or str(parent_dept.prtndid) != str(ctx_orgid):
                raise HTTPException(status_code=404, detail="Node not found")

            children = []

        else:
            raise HTTPException(status_code=400, detail="Invalid target node type")

        response = [
            {
                "ndid": str(row.ndid),
                "ndty": row.ndty,
                "name": row.name,
                "crtat": row.crtat,
                "updtat": row.updtat,
                "isact": row.isact,
            }
            for row in children
        ]

        return {
            "status": "success",
            "message": "child nodes retrieved successfully",
            "data": response,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")