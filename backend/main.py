"""
Daemonium FastAPI Backend
Main application entry point for the philosopher chatbot API
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
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
from .auth import init_firebase_if_enabled

# Configure logging (env override)
level_name = os.getenv("LOG_LEVEL", "INFO").upper()
level = getattr(logging, level_name, logging.INFO)
logging.basicConfig(level=level)

# Enable verbose MCP client logs when requested
if os.getenv("MCP_DEBUG", "0").lower() in ("1", "true", "yes"): 
    logging.getLogger("backend.mcp_client").setLevel(logging.DEBUG)

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
    
    # Make db_manager available immediately so /health can run even if initial connect fails
    app.state.db_manager = db_manager
    
    # Initialize Firebase Admin SDK if enabled (non-fatal on failure/disabled)
    try:
        init_ok = init_firebase_if_enabled(settings)
        if init_ok:
            logger.info("Firebase authentication initialized")
        else:
            logger.info("Firebase authentication not initialized (disabled or missing packages)")
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
    
    try:
        try:
            await db_manager.connect()
            logger.info("Database connection established")
        except Exception as e:
            # Don't crash app startup if DB isn't ready yet; /health will retry
            logger.error(f"Database connection failed on startup: {e}")
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down Daemonium API...")
        if db_manager and getattr(db_manager, "client", None):
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
        # Ensure db_manager exists and attempt lazy connect if not connected yet
        if db_manager and getattr(db_manager, "client", None) is None:
            try:
                await db_manager.connect()
                logger.info("Database connection established via health check")
            except Exception as conn_err:
                logger.error(f"Health check connect attempt failed: {conn_err}")
        
        # Test database connection
        is_connected = False
        if db_manager:
            is_connected = await db_manager.health_check()
        
        if not is_connected:
            # Report service unavailable until DB is reachable
            raise HTTPException(status_code=503, detail="Service unavailable")
        
        return {
            "status": "healthy",
            "database": "connected",
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
