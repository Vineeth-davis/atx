# api/main.py
# Main FastAPI application entry point

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api.routes import health, ask, schema, logs
from api.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Synthetic Data Platform with RAG workflows and advanced agent capabilities"
)

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

def main():
    """Main entry point for the FastAPI application"""
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    main()
