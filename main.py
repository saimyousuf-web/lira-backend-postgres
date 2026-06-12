from fastapi import FastAPI
from get_pending_users.main import router as get_pending_users_router
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
from get_list_nodes.main import router as get_list_nodes_router
from get_all_feedback.main import router as get_all_feedback_router
from health import router as health_router
from ingest.main import router as ingest_router
from update_feedback_status.main import router as update_feedback_status_router 
from delete_feedback.main import router as delete_feedback_router
from get_all_users.main import router as get_all_users_router 
from get_all_dept_func_by_org.main import router as get_all_dept_func_by_org_router
from approve_user.main import router as approve_user_router 
from create_new_user.main import router as create_new_user_router 
from get_chat_history_by_id.main import router as get_chat_history_by_id_router 
from get_course_by_catid.main import router as get_course_by_catid_router
from get_module_by_cid.main import router as get_module_by_cid_router
from approve_module.main import router as approve_module_router
from get_course_by_catid.main import router as get_course_by_catid_router
from create_catcourse.main import router as create_catcourse_router
from health import router as health_router
from ingest.main import router as ingest_router
from chat_stream.main import router as chat_stream_router
from dashboard_chat.main import router as dashboard_chat_router

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def create_app() -> FastAPI:
    app = FastAPI()
    cors_middleware(app)

    @app.on_event("startup")
    async def on_startup():
        await init_db()

    #Auth APIs
    app.include_router(get_user_org_access_details_router, prefix="/get-user-org-access-details",tags=["Authentication APIs"])
    app.include_router(register_learner_router, prefix="/register-learner",tags=["Authentication APIs"])
    app.include_router(get_all_organization_router,prefix="/get-all-organization",tags=["Authentication APIs"])

    # Nodes APIs
    app.include_router(get_all_dept_func_by_org_router, prefix="/get-all-dept-func-by-org",tags=["Nodes APIs"])
    app.include_router(get_all_departments_by_org_router, prefix="/get-all-departments-by-org",tags=["Nodes APIs"])
    app.include_router(get_all_functions_by_dept_router, prefix="/get-all-functions-by-dept",tags=["Nodes APIs"])
    
    
    #User APIs
    app.include_router(get_user_current_info_router, prefix="/get-user-current-info",tags=["User Management"])
    app.include_router(get_all_users_router, prefix="/get-all-users",tags=["User Management"])
    app.include_router(get_pending_users_router,prefix="/get-pending-users",tags=["User Management"])
    app.include_router(approve_user_router,prefix="/approve-user",tags=["User Management"])
    app.include_router(create_new_user_router,prefix="/create-user",tags=["User Management"])


    app.include_router(ingest_router, prefix="/ingest", tags=["Ingestion"])
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
    app.include_router(get_chat_history_router, prefix = "/chats"  ,tags=["Query Orchestration APIs"])
    app.include_router(get_chat_history_by_id_router, prefix = "/session-history" ,tags=["Query Orchestration APIs"])


    #Profile
    app.include_router(get_org_logo_router, prefix='/get-logo')


    #Feedback
    app.include_router(get_all_feedback_router, prefix='/get-all-feedback')
    app.include_router(update_feedback_status_router,prefix='/update-feedback-status')
    app.include_router(delete_feedback_router,prefix='/delete-feedback-by-id')

    # Health Check
    app.include_router(health_router, prefix="/health", tags=["Health Check"])
    app.include_router(get_list_nodes_router, prefix="/get-list-nodes", tags=["Node Management"])
    
    app.include_router(chat_stream_router, prefix="/rag")
    app.include_router(dashboard_chat_router, prefix="/dashboard-chat")
    app.include_router(get_course_by_catid_router, prefix="/get-course-by-catid", tags=["Course Management"])
    app.include_router(approve_module_router, prefix="/approve-module", tags=["Module Management"])
    app.include_router(get_module_by_cid_router, prefix="/get-modules-by-course-id", tags=["Module Management"])
    app.include_router(get_course_by_catid_router, prefix="/get-course-by-catid", tags=["Course Management"])
    app.include_router(create_catcourse_router, prefix="/create-catcourse", tags=["Category Management"])
    return app


app = create_app()
app.title = "Lira API"
app.version = "1.0.0"