# api/routes/health.py
# Health check endpoints

from fastapi import APIRouter
from api.config import settings
from agents.orchestrator import rag_orchestrator

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
    try:
        # Check RAG system status
        rag_stats = rag_orchestrator.schema_retriever.vector_store.get_stats()
        
        return {
            "status": "ready",
            "rag_system": {
                "initialized": rag_stats['total_vectors'] > 0,
                "vector_count": rag_stats['total_vectors'],
                "dimension": rag_stats['dimension']
            }
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e),
            "rag_system": {
                "initialized": False,
                "error": "RAG system not available"
            }
        }

@router.post("/rag/initialize")
async def initialize_rag():
    """Manually initialize the RAG system"""
    try:
        await rag_orchestrator.initialize_rag_system()
        stats = rag_orchestrator.schema_retriever.vector_store.get_stats()
        return {
            "status": "success",
            "message": "RAG system initialized successfully",
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to initialize RAG system: {str(e)}"
        }
