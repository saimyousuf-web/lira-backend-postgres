from fastapi import FastAPI
from shared.middleware import cors_middleware
from core.db import Base, engine
from create_departments.main import router as create_departments_router
from create_organization.main import router as create_organization_router
from create_functions.main import router as create_functions_router
from create_category.main import router as create_category_router
from get_user_org_access_details.main import router as get_user_org_access_details_router
from register_learner_router.main import router as register_learner_router
from get_all_categories.main import router as get_all_categories_router
from get_all_courses.main import router as get_all_courses_router
from create_course.main import router as create_course_router

from health import router as health_router


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def create_app() -> FastAPI:
    app = FastAPI()
    cors_middleware(app)

    @app.on_event("startup")
    async def on_startup():
        await init_db()

    #auth apis
    app.include_router(get_user_org_access_details_router, prefix="/get-user-org-access-details")
    app.include_router(register_learner_router, prefix="/register-learner")


    app.include_router(create_departments_router, prefix="/create-departments", tags=["Department Management"])
    app.include_router(create_organization_router, prefix="/create-organizations", tags=["Organization Management"])
    app.include_router(create_functions_router, prefix="/create-functions", tags=["Function Management"])
    app.include_router(create_category_router, prefix="/create-categories", tags=["Category Management"])
    app.include_router(get_all_categories_router, prefix="/get-all-categories", tags=["Category Management"])
    app.include_router(get_all_courses_router, prefix="/get-all-courses", tags=["Course Management"])
    app.include_router(create_course_router, prefix="/create-course", tags=["Course Management"])
    app.include_router(health_router, prefix="/health", tags=["Health Check"])

    return app


app = create_app()
app.title = "Lira API"
app.version = "1.0.0"