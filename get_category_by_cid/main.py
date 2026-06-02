from fastapi import APIRouter,Path,Depends
from core.db import get_db_session
from dependencies.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get('/{ctx_orgid}/{ctx_ndid}/{cid}')
async def get_category_by_cid(ctx_orgid:str = Path(...),ctx_ndid:str=Path(...),cid:str=Path(...),user = Depends(get_current_user),db:AsyncSession =  Depends(get_db_session)):
    # add depencey if needed to check permission view categories)
    





