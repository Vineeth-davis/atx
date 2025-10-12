# api/main.py
# Main FastAPI application entry point

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import logging
from contextlib import asynccontextmanager
from api.routes import health, ask, schema, logs
from api.routes import nl2sql
from api.config import settings
from api.logging_config import setup_logging, get_logger
from api.middleware import RequestIDMiddleware, QueryTracingMiddleware
from agents.orchestrator import rag_orchestrator
from core.connection_manager import get_connection_manager
from adapters.database_adapter import DatabaseType
try:
    from adapters.sqlserver_adapter import SQLServerAdapter
    _sqlserver_available = True
except Exception:
    SQLServerAdapter = None  # type: ignore
    _sqlserver_available = False

# Setup logging first
setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    try:
        logger.info("🚀 Starting RAG system initialization...")
        # Register known adapters (optional SQL Server adapter)
        cm = get_connection_manager()
        if _sqlserver_available and SQLServerAdapter is not None:
            cm.register_adapter(DatabaseType.SQLSERVER, SQLServerAdapter)
        else:
            logger.info("SQL Server adapter not available; skipping registration")
        await rag_orchestrator.initialize_rag_system()
        logger.info("✅ RAG system initialization completed successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG system: {e}")
        logger.warning("⚠️ Application starting without RAG initialization")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG system...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Synthetic Data Platform with RAG workflows and advanced agent capabilities",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(QueryTracingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(ask.router, prefix="/ask", tags=["ask"])
app.include_router(schema.router, prefix="/schema", tags=["schema"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])
app.include_router(nl2sql.router, prefix="/nl2sql", tags=["nl2sql"])

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )