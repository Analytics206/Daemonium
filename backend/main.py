"""
Daemonium FastAPI Backend
Main application entry point for the philosopher chatbot API
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import List, Optional, Dict, Any
import uvicorn

from .database import DatabaseManager
from .models import *
from .routers import (
    philosophers,
    philosophy_schools,
    books,
    aphorisms,
    ideas,
    summaries,
    chat,
    search
)
from .config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database manager instance
db_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global db_manager
    
    # Startup
    logger.info("Starting Daemonium API...")
    settings = get_settings()
    db_manager = DatabaseManager(settings)
    
    try:
        await db_manager.connect()
        logger.info("Database connection established")
        
        # Store db_manager in app state
        app.state.db_manager = db_manager
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down Daemonium API...")
        if db_manager:
            await db_manager.disconnect()
        logger.info("Database connection closed")

# Create FastAPI app
app = FastAPI(
    title="Daemonium Philosopher Chatbot API",
    description="API for accessing philosophical content and powering the Daemonium chatbot experience",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database manager
async def get_db_manager() -> DatabaseManager:
    """Get database manager dependency"""
    return app.state.db_manager

# Include routers
app.include_router(
    philosophers.router,
    prefix="/api/v1/philosophers",
    tags=["philosophers"],
    dependencies=[Depends(get_db_manager)]
)

app.include_router(
    philosophy_schools.router,
    prefix="/api/v1/philosophy-schools",
    tags=["philosophy-schools"],
    dependencies=[Depends(get_db_manager)]
)

app.include_router(
    books.router,
    prefix="/api/v1/books",
    tags=["books"],
    dependencies=[Depends(get_db_manager)]
)

app.include_router(
    aphorisms.router,
    prefix="/api/v1/aphorisms",
    tags=["aphorisms"],
    dependencies=[Depends(get_db_manager)]
)

app.include_router(
    ideas.router,
    prefix="/api/v1/ideas",
    tags=["ideas"],
    dependencies=[Depends(get_db_manager)]
)

app.include_router(
    summaries.router,
    prefix="/api/v1/summaries",
    tags=["summaries"],
    dependencies=[Depends(get_db_manager)]
)

app.include_router(
    chat.router,
    prefix="/api/v1/chat",
    tags=["chat"],
    dependencies=[Depends(get_db_manager)]
)

app.include_router(
    search.router,
    prefix="/api/v1/search",
    tags=["search"],
    dependencies=[Depends(get_db_manager)]
)

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Daemonium Philosopher Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check(db_manager: DatabaseManager = Depends(get_db_manager)):
    """Health check endpoint"""
    try:
        # Test database connection
        is_connected = await db_manager.health_check()
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "database": "connected" if is_connected else "disconnected",
            "timestamp": "2025-07-31T12:00:32-05:00"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/api/v1/stats")
async def get_api_stats(db_manager: DatabaseManager = Depends(get_db_manager)):
    """Get API and database statistics"""
    try:
        stats = await db_manager.get_collection_stats()
        return {
            "api_version": "1.0.0",
            "collections": stats,
            "total_documents": sum(stats.values()),
            "timestamp": "2025-07-31T12:00:32-05:00"
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
