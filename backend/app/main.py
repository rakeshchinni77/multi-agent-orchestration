from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.session import init_db
from app.api.routes.tasks import router as tasks_router
from app.api.routes.websocket import router as ws_router

# Configure logging on boot
setup_logging()
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown routines."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    try:
        # Initialize PostgreSQL database tables
        await init_db()
        logger.info("Database schema initialized and ready.")
    except Exception as e:
        logger.warning(f"Database auto-initialization skipped or encountered issue: {e}")

    yield

    logger.info("Shutting down Multi-Agent Orchestrator backend.")


# Initialize primary FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Stateful Multi-Agent AI Orchestration System with LangGraph, Celery, and WebSockets.",
    lifespan=lifespan
)

# Configure CORS Middleware
# Allows React UI (http://localhost:3000) and other configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check endpoint"
)
async def health_check():
    """
    Service health check endpoint.
    
    Verifies API availability and returns system metadata.
    """
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Include REST and WebSocket Routers
app.include_router(tasks_router)
app.include_router(ws_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)
