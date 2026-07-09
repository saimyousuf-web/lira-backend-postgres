from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.db import get_db_session
from core.id_cypher import decrypt_id
from models.nodes import Node, NodeType, Org, Dept, Func
from get_list_nodes.schema import ListNodesResponse, ChildNodeResponse

router = APIRouter()


@router.get(
    "/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}/node/{target_ndty}/{target_ndid}/children",
    response_model=ListNodesResponse,
)
async def list_nodes(
    ctx_orgid_enc: str = Path(..., alias="ctx_orgid"),
    ctx_ndid_enc: str = Path(..., alias="ctx_ndid"),
    ctx_ndty: str = Path(...),
    target_ndty: str = Path(...),
    target_ndid_enc: str = Path(..., alias="target_ndid"),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        ctx_orgid = decrypt_id(ctx_orgid_enc)
        ctx_ndid = decrypt_id(ctx_ndid_enc)
        target_ndid = decrypt_id(target_ndid_enc)

        if target_ndty == "ORG":
            target_stmt = select(Org).where(
                Org.ndid == target_ndid,
                Org.isact.is_(True),
            )
            result = await db.execute(target_stmt)
            target = result.scalars().first()

            if not target or target.ndid != ctx_orgid:
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

            if not target or target.prtndid != ctx_orgid:
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

            if not parent_dept or parent_dept.prtndid != ctx_orgid:
                raise HTTPException(status_code=404, detail="Node not found")

            children = []

        else:
            raise HTTPException(status_code=400, detail="Invalid target node type")

        response = [
            ChildNodeResponse(
                ndid=row.ndid,
                ndty=row.ndty,
                name=row.name,
                crtat=row.crtat,
                updtat=row.updtat,
                isact=row.isact,
            )
            for row in children
        ]

        return ListNodesResponse(
            status="success",
            message="child nodes retrieved successfully",
            data=response,
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}",
        )