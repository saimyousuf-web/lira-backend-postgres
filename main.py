from fastapi import FastAPI
from shared.middleware import cors_middleware
from database import Base, engine
from models.user import User
from get_user_org_access_details.main import router as get_user_org_access_details_router
from register_learner.main import router as register_learner_router

Base.metadata.create_all(bind=engine)



def create_app() -> FastAPI:
    app = FastAPI()
    cors_middleware(app)

    app.include_router(register_learner_router, prefix="/register-learner")
    app.include_router(get_user_org_access_details_router, prefix="/get-user-org-access-details")

    return app


app = create_app()