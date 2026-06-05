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
from get_category_by_cid.main import router as get_category_by_cid_router
from get_chat_history.main import router as get_chat_history_router
from get_logo.main import router as get_org_logo_router
from get_user_current_info.main import router as get_user_current_info_router
from health import router as health_router
from get_all_organization.main import router as get_all_organization_router
from get_all_departments_by_org.main import router as get_all_departments_by_org_router
from get_all_functions_by_dept.main import router as get_all_functions_by_dept_router
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
    app.include_router(get_user_org_access_details_router, prefix="/get-user-org-access-details",tags=["Authentication APIs"])
    app.include_router(register_learner_router, prefix="/register-learner",tags=["Authentication APIs"])
    app.include_router(get_all_organization_router,prefix="/get-all-organization",tags=["Authentication APIs"])
    app.include_router(get_all_departments_by_org_router, prefix="/get-all-departments-by-org",tags=["Authentication APIs"])
    app.include_router(get_all_functions_by_dept_router, prefix="/get-all-functions-by-dept",tags=["Authentication APIs"])
    app.include_router(get_user_current_info_router, prefix="/get-user-current-info",tags=["Authentication APIs"])


    app.include_router(create_departments_router, prefix="/create-departments", tags=["Department Management"])
    app.include_router(create_organization_router, prefix="/create-organizations", tags=["Organization Management"])
    app.include_router(create_functions_router, prefix="/create-functions", tags=["Function Management"])
    
    # Category Management
    app.include_router(create_category_router, prefix="/create-category", tags=["Category Management"])
    app.include_router(get_all_categories_router, prefix="/get-all-categories", tags=["Category Management"])
    app.include_router(get_category_by_cid_router,prefix="/get-category-by-course-id",tags=["Category Management"])
    app.include_router(get_all_courses_router, prefix="/get-all-courses", tags=["Course Management"])
    app.include_router(create_course_router, prefix="/create-course", tags=["Course Management"])

    # Chat
    app.include_router(get_chat_history_router, prefix = "/chats")


    #Profile
    app.include_router(get_org_logo_router, prefix='/get-logo')

    # Health Check
    app.include_router(health_router, prefix="/health", tags=["Health Check"])

    return app


app = create_app()
app.title = "Lira API"
app.version = "1.0.0"