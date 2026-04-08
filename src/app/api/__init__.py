from fastapi import APIRouter

from app.api.routes.users.router import router as users_router
from app.api.routes.time_codes.router import router as time_codes_router
from app.api.routes.timesheets.router import router as timesheets_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(time_codes_router, prefix="/time-codes", tags=["Time Codes"])
api_router.include_router(timesheets_router, prefix="/timesheets", tags=["Timesheets"])
