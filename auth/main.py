# from datetime import datetime, timedelta, timezone
# from typing import Annotated
# from core.config import settings
# from fastapi import Depends, APIRouter,status, HTTPException
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from pydantic import BaseModel
# from pwdlib import PasswordHash
# import jwt
# from jwt.exceptions import InvalidTokenError
# from sqlalchemy import create_engine

# from sqlalchemy.orm import Session
# from database import get_db
# from models.user import User as UserDB

# print(settings.DATABASE_URL)
# SECRET_KEY = "de1bd0bb3c1de2ded6f5f332d4d80d99e5cce6a1766b8e4ec2a2d80c80f73073"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30




# engine = create_engine(settings.DATABASE_URL)

# connection = engine.connect()

# print("DB Connected!")

# router = APIRouter()

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# password_hash = PasswordHash.recommended()

# DUMMY_HASH = password_hash.hash("dummypassword")

# class Token(BaseModel):
#     access_token : str
#     token_type : str

# class TokenData(BaseModel):
#     username: str | None = None    


# class User(BaseModel):
#     username : str
#     email : str | None = None
#     full_name : str | None = None
#     disabled : bool | None = None





# def verify_password(plain_password, hashed_password):
#     return password_hash.verify(plain_password, hashed_password)

# def get_password_hash(password):
#     return password_hash.hash(password)

# def get_user(db: Session, email: str):
#     return db.query(UserDB).filter(UserDB.email == email).first()

# def authenticate_user(db: Session, email: str, password: str):
#     user = get_user(db, email)
#     #When authenticate_user is called with a username that doesn't exist in the database, we still run verify_password against a dummy hash.
#     # This ensures the endpoint takes roughly the same amount of time to respond whether the username is valid or not, preventing timing attacks that could be used to enumerate existing usernames.

#     if not user:
#             verify_password(password, DUMMY_HASH)
#             return False

#     if not verify_password(password, user.password):
#             return False
#     return user


# def create_access_token(data: dict, expires_delta: timedelta | None = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.now(timezone.utc) + expires_delta
#     else:
#         expire = datetime.now(timezone.utc) + timedelta(minutes=15)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt




# async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except InvalidTokenError:
#         raise credentials_exception
#     user = get_user(db, username=token_data.username)
#     if user is None:
#         raise credentials_exception
#     return user


# async def get_current_active_user(
#     current_user: Annotated[User, Depends(get_current_user)],
# ):
#     if current_user.is_active:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user


# @router.post("/")
# async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],db: Session = Depends(get_db)) -> Token:
#     user = authenticate_user(db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user.email}, expires_delta=access_token_expires
#     )
#     print(Token(access_token=access_token, token_type="bearer"))
#     return Token(access_token=access_token, token_type="bearer")



# @router.get("/users/me")
# async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
#     return current_user


# password_hash = PasswordHash.recommended()
# print(password_hash.hash("Maestro123%"))