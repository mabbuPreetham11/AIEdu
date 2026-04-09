from fastapi import APIRouter

from app.api.v1.endpoints import assignments, auth, chat, classrooms, courses, grades, sessions

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(classrooms.router, prefix="/classrooms", tags=["classrooms"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(grades.router, prefix="/grades", tags=["grades"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
