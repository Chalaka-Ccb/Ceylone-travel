from fastapi import APIRouter
from app.api.v1.endpoints import trips
from app.api.v1.endpoints import users

api_router = APIRouter()
api_router.include_router(trips.router, prefix="/trips", tags=["Trips & Planning"])

# <-- 2. ADD THE NEW USER ROUTER -->
api_router.include_router(users.router, prefix="/users", tags=["User Profile"])