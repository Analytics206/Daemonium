"""
Philosophers API router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
import logging

from ..database import DatabaseManager
from ..models import PhilosopherResponse, PhilosopherSummary, PhilosopherWithSchool, PhilosopherWithSchoolResponse, PaginationParams, SearchParams

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
    is_active_chat: Optional[int] = Query(None, description="Filter by active chat availability (0 or 1)"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get all philosophers with pagination and optional active chat filter"""
    try:
        philosophers = await db_manager.get_philosophers(skip=skip, limit=limit, is_active_chat=is_active_chat)
        
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

@router.get("/search/", response_model=PhilosopherResponse)
async def search_philosophers(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    is_active_chat: Optional[int] = Query(None, description="Filter by active chat availability (0 or 1)"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Search philosophers by name or content with optional active chat filter"""
    try:
        philosophers = await db_manager.search_philosophers(query=query, limit=limit, is_active_chat=is_active_chat)
        
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

@router.get("/{philosopher_name}/with-school", response_model=PhilosopherWithSchoolResponse)
async def get_philosopher_with_school(
    philosopher_name: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get philosopher with their associated philosophy school information by name"""
    try:
        philosopher_with_school = await db_manager.get_philosopher_with_school_by_name(philosopher_name)
        
        if not philosopher_with_school:
            raise HTTPException(status_code=404, detail=f"Philosopher '{philosopher_name}' not found")
        
        # Convert to Pydantic models
        philosopher_model = PhilosopherSummary(**philosopher_with_school["philosopher"])
        school_model = None
        
        if philosopher_with_school["school"]:
            from ..models import PhilosophySchool
            school_model = PhilosophySchool(**philosopher_with_school["school"])
        
        philosopher_with_school_model = PhilosopherWithSchool(
            philosopher=philosopher_model,
            school=school_model
        )
        
        return PhilosopherWithSchoolResponse(
            data=philosopher_with_school_model,
            message=f"Retrieved philosopher with school information: {philosopher_model.author}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get philosopher with school {philosopher_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve philosopher with school information")


@router.get("/{author}/related", response_model=PhilosopherResponse)
async def get_related_philosophers(
    author: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of related philosophers"),
    is_active_chat: Optional[int] = Query(None, description="Filter by active chat availability (0 or 1)"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get philosophers related to the specified author name"""
    try:
        # Search for philosophers related to the given author name
        # Use the author name directly as the search parameter
        related_philosophers = await db_manager.search_philosophers(
            query=author, 
            limit=limit,
            is_active_chat=is_active_chat
        )
        
        if not related_philosophers:
            raise HTTPException(status_code=404, detail=f"No philosophers found related to '{author}'")
        
        # Convert to Pydantic models
        philosopher_models = []
        for related_philosopher in related_philosophers:
            try:
                philosopher_models.append(PhilosopherSummary(**related_philosopher))
            except Exception as e:
                logger.warning(f"Failed to parse philosopher {related_philosopher.get('_id', 'unknown')}: {e}")
                continue
        
        return PhilosopherResponse(
            data=philosopher_models,
            total_count=len(philosopher_models),
            message=f"Found {len(philosopher_models)} philosophers related to '{author}'"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get related philosophers for {author}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve related philosophers")

@router.get("/by-author/{author}", response_model=Dict[str, Any])
async def get_all_content_by_author(
    author: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of items per collection"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get all content across collections for a specific author"""
    try:
        # Get data from all collections that use author as a field
        result = {
            "author": author,
            "philosophers": [],
            "aphorisms": [],
            "book_summary": [],
            "top_ten_ideas": [],
            "idea_summary": [],
            "philosophy_themes": [],
            "philosopher_summary": []
        }
        
        # Get philosophers
        philosophers = await db_manager.search_philosophers(query=author, limit=limit)
        result["philosophers"] = philosophers
        
        # Get aphorisms
        aphorisms = await db_manager.get_aphorisms_by_author(author, limit=limit)
        result["aphorisms"] = aphorisms
        
        # Get book summaries
        book_summaries = await db_manager.get_book_summaries_by_author(author, limit=limit)
        result["book_summary"] = book_summaries
        
        # Get top ten ideas
        top_ideas = await db_manager.get_top_ideas_by_author(author, limit=limit)
        result["top_ten_ideas"] = top_ideas
        
        # Get idea summaries
        idea_summaries = await db_manager.get_idea_summaries_by_author(author, limit=limit)
        result["idea_summary"] = idea_summaries
        
        # Get philosophy themes
        themes = await db_manager.get_philosophy_themes_by_author(author, limit=limit)
        result["philosophy_themes"] = themes
        
        # Get philosopher summaries
        summaries = await db_manager.get_philosopher_summaries_by_author(author, limit=limit)
        result["philosopher_summary"] = summaries
        
        # Calculate totals
        total_items = sum(len(items) for items in result.values() if isinstance(items, list))
        
        return {
            "success": True,
            "message": f"Retrieved {total_items} items for author: {author}",
            "data": result,
            "total_items": total_items
        }
    
    except Exception as e:
        logger.error(f"Failed to get content for author {author}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve content for author")
