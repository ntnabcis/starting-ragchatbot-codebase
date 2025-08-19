from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime


class HealthStatus(BaseModel):
    status: str
    timestamp: datetime
    version: str = "2.0.0"


health_router = APIRouter(prefix="/api", tags=["health"])


@health_router.get("/health", response_model=HealthStatus)
async def health_check():
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now()
    )