# api/routes/health.py
# Health check endpoints

from fastapi import APIRouter
from api.config import settings

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@router.get("/ready")
async def readiness_check():
    """Readiness check for database and external services"""
    # TODO: Add database connectivity check
    # TODO: Add vector store connectivity check
    # TODO: Add OpenAI API connectivity check
    return {"status": "ready"}
