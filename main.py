from fastapi import FastAPI
from shared.middleware import cors_middleware
from auth.main import router as get_hello_router
from database import Base, engine
from models.user import User

Base.metadata.create_all(bind=engine)



def create_app() -> FastAPI:
    app = FastAPI()
    cors_middleware(app)


    app.include_router(get_hello_router, prefix="/token")


    return app


app = create_app()