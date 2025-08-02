"""
Philosophy Schools API router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from ..database import DatabaseManager
from ..models import PhilosophySchool, PhilosophySchoolResponse, PhilosopherWithSchool, PhilosopherWithSchoolResponse, PhilosopherSummary

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_db_manager():
    """Dependency to get database manager"""
    from ..main import app
    return app.state.db_manager

@router.get("/", response_model=PhilosophySchoolResponse)
async def get_philosophy_schools(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get all philosophy schools with pagination"""
    try:
        schools = await db_manager.get_philosophy_schools(skip=skip, limit=limit)
        
        # Convert to Pydantic models
        school_models = []
        for school in schools:
            try:
                school_models.append(PhilosophySchool(**school))
            except Exception as e:
                logger.warning(f"Failed to parse school {school.get('_id', 'unknown')}: {e}")
                continue
        
        return PhilosophySchoolResponse(
            data=school_models,
            total_count=len(school_models),
            message=f"Retrieved {len(school_models)} philosophy schools"
        )
    
    except Exception as e:
        logger.error(f"Failed to get philosophy schools: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve philosophy schools")

@router.get("/{idea}", response_model=PhilosophySchoolResponse)
async def get_philosophy_school_by_idea(
    idea: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get philosophy schools related to a specific idea"""
    try:
        # Search for philosophy schools that contain the idea in their content
        schools = await db_manager.search_philosophy_schools(query=idea, limit=10)
        
        if not schools:
            raise HTTPException(status_code=404, detail=f"No philosophy schools found related to idea '{idea}'")
        
        # Convert to Pydantic models
        school_models = []
        for school in schools:
            try:
                school_models.append(PhilosophySchool(**school))
            except Exception as e:
                logger.warning(f"Failed to parse school {school.get('_id', 'unknown')}: {e}")
                continue
        
        return PhilosophySchoolResponse(
            data=school_models,
            total_count=len(school_models),
            message=f"Found {len(school_models)} philosophy schools related to idea '{idea}'"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get philosophy schools for idea {idea}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve philosophy schools for idea")

@router.get("/search/", response_model=PhilosophySchoolResponse)
async def search_philosophy_schools(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Search philosophy schools by name, category, or content"""
    try:
        schools = await db_manager.search_philosophy_schools(query=query, limit=limit)
        
        # Convert to Pydantic models
        school_models = []
        for school in schools:
            try:
                school_models.append(PhilosophySchool(**school))
            except Exception as e:
                logger.warning(f"Failed to parse school {school.get('_id', 'unknown')}: {e}")
                continue
        
        return PhilosophySchoolResponse(
            data=school_models,
            total_count=len(school_models),
            message=f"Found {len(school_models)} philosophy schools matching '{query}'"
        )
    
    except Exception as e:
        logger.error(f"Failed to search philosophy schools: {e}")
        raise HTTPException(status_code=500, detail="Failed to search philosophy schools")

@router.get("/{keyword}/philosophers", response_model=PhilosopherWithSchoolResponse)
async def get_philosophers_by_keyword(
    keyword: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of philosophers to return"),
    is_active_chat: Optional[int] = Query(None, description="Filter by active chat availability (0 or 1)"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get philosophers related to a specific keyword"""
    try:
        # Search for philosophers related to the keyword
        philosophers = await db_manager.search_philosophers(
            query=keyword, 
            limit=limit, 
            is_active_chat=is_active_chat
        )
        
        if not philosophers:
            raise HTTPException(status_code=404, detail=f"No philosophers found related to keyword '{keyword}'")
        
        # Convert to Pydantic models (without school information since we're searching by keyword)
        philosopher_models = []
        for philosopher in philosophers:
            try:
                philosopher_model = PhilosopherSummary(**philosopher)
                # Create a simplified response without school information
                philosopher_with_school = PhilosopherWithSchool(
                    philosopher=philosopher_model,
                    school=None  # No specific school since we're searching by keyword
                )
                philosopher_models.append(philosopher_with_school)
            except Exception as e:
                logger.warning(f"Failed to parse philosopher {philosopher.get('_id', 'unknown')}: {e}")
                continue
        
        return PhilosopherWithSchoolResponse(
            data=philosopher_models,
            total_count=len(philosopher_models),
            message=f"Found {len(philosopher_models)} philosophers related to keyword '{keyword}'"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get philosophers for keyword {keyword}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve philosophers for keyword")
