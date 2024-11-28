from fastapi import APIRouter

from app.views.routes import home, packages, search

api_router = APIRouter()
api_router.include_router(home.router, tags=["home"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(packages.router, tags=["search"])
