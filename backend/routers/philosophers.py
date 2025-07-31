"""
Philosophers API router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from ..database import DatabaseManager
from ..models import PhilosopherResponse, PhilosopherSummary, PaginationParams, SearchParams

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_db_manager():
    """Dependency to get database manager"""
    from ..main import app
    return app.state.db_manager

@router.get("/", response_model=PhilosopherResponse)
async def get_philosophers(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get all philosophers with pagination"""
    try:
        philosophers = await db_manager.get_philosophers(skip=skip, limit=limit)
        
        # Convert to Pydantic models
        philosopher_models = []
        for philosopher in philosophers:
            try:
                philosopher_models.append(PhilosopherSummary(**philosopher))
            except Exception as e:
                logger.warning(f"Failed to parse philosopher {philosopher.get('_id', 'unknown')}: {e}")
                continue
        
        return PhilosopherResponse(
            data=philosopher_models,
            total_count=len(philosopher_models),
            message=f"Retrieved {len(philosopher_models)} philosophers"
        )
    
    except Exception as e:
        logger.error(f"Failed to get philosophers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve philosophers")

@router.get("/{philosopher_id}", response_model=PhilosopherResponse)
async def get_philosopher_by_id(
    philosopher_id: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get a specific philosopher by ID"""
    try:
        philosopher = await db_manager.get_philosopher_by_id(philosopher_id)
        
        if not philosopher:
            raise HTTPException(status_code=404, detail=f"Philosopher with ID '{philosopher_id}' not found")
        
        philosopher_model = PhilosopherSummary(**philosopher)
        
        return PhilosopherResponse(
            data=philosopher_model,
            message=f"Retrieved philosopher: {philosopher_model.name}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get philosopher {philosopher_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve philosopher")

@router.get("/search/", response_model=PhilosopherResponse)
async def search_philosophers(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Search philosophers by name or content"""
    try:
        philosophers = await db_manager.search_philosophers(query=query, limit=limit)
        
        # Convert to Pydantic models
        philosopher_models = []
        for philosopher in philosophers:
            try:
                philosopher_models.append(PhilosopherSummary(**philosopher))
            except Exception as e:
                logger.warning(f"Failed to parse philosopher {philosopher.get('_id', 'unknown')}: {e}")
                continue
        
        return PhilosopherResponse(
            data=philosopher_models,
            total_count=len(philosopher_models),
            message=f"Found {len(philosopher_models)} philosophers matching '{query}'"
        )
    
    except Exception as e:
        logger.error(f"Failed to search philosophers: {e}")
        raise HTTPException(status_code=500, detail="Failed to search philosophers")

@router.get("/{philosopher_id}/related", response_model=PhilosopherResponse)
async def get_related_philosophers(
    philosopher_id: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of related philosophers"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get philosophers related to the specified philosopher"""
    try:
        # First get the target philosopher
        philosopher = await db_manager.get_philosopher_by_id(philosopher_id)
        
        if not philosopher:
            raise HTTPException(status_code=404, detail=f"Philosopher with ID '{philosopher_id}' not found")
        
        # Simple related philosophers logic - could be enhanced with ML/embeddings
        related_philosophers = []
        
        # Search by philosophical school if available
        if philosopher.get('philosophical_school'):
            school_philosophers = await db_manager.search_philosophers(
                query=philosopher['philosophical_school'], 
                limit=limit + 1  # +1 to account for the original philosopher
            )
            related_philosophers.extend([p for p in school_philosophers if p['_id'] != philosopher_id])
        
        # Search by influences/influenced if available
        if philosopher.get('influences'):
            for influence in philosopher['influences'][:2]:  # Limit to first 2 influences
                influence_philosophers = await db_manager.search_philosophers(
                    query=influence, 
                    limit=3
                )
                related_philosophers.extend([p for p in influence_philosophers if p['_id'] != philosopher_id])
        
        # Remove duplicates and limit results
        seen_ids = set()
        unique_related = []
        for p in related_philosophers:
            if p['_id'] not in seen_ids and len(unique_related) < limit:
                seen_ids.add(p['_id'])
                unique_related.append(p)
        
        # Convert to Pydantic models
        philosopher_models = []
        for related_philosopher in unique_related:
            try:
                philosopher_models.append(PhilosopherSummary(**related_philosopher))
            except Exception as e:
                logger.warning(f"Failed to parse philosopher {related_philosopher.get('_id', 'unknown')}: {e}")
                continue
        
        return PhilosopherResponse(
            data=philosopher_models,
            total_count=len(philosopher_models),
            message=f"Found {len(philosopher_models)} philosophers related to {philosopher.get('name', philosopher_id)}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get related philosophers for {philosopher_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve related philosophers")
