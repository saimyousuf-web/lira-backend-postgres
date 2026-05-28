from auth.main import get_current_user
from database import get_db
from fastapi import APIRouter, HTTPException, Depends
from core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine(settings.DATABASE_URL)

connection = engine.connect()

print("DB Connected!")

router = APIRouter()


@router.get('')
async def get_user_details(user=Depends(get_current_user),db:Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="user not authenticated")
    user_identifier = user.get("sub")



