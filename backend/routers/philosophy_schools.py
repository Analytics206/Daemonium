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

@router.get("/{school_id}", response_model=PhilosophySchoolResponse)
async def get_philosophy_school_by_id(
    school_id: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get a specific philosophy school by ID"""
    try:
        # Handle both formats: direct school_id or prefixed with "school_"
        if not school_id.startswith("school_"):
            school_id = f"school_{school_id}"
            
        school = await db_manager.get_philosophy_school_by_id(school_id)
        
        if not school:
            raise HTTPException(status_code=404, detail=f"Philosophy school with ID '{school_id}' not found")
        
        school_model = PhilosophySchool(**school)
        
        return PhilosophySchoolResponse(
            data=school_model,
            message=f"Retrieved philosophy school: {school_model.name}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get philosophy school {school_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve philosophy school")

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

@router.get("/{school_id}/philosophers", response_model=PhilosopherWithSchoolResponse)
async def get_philosophers_by_school(
    school_id: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of philosophers to return"),
    is_active_chat: Optional[int] = Query(None, description="Filter by active chat availability (0 or 1)"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get philosophers belonging to a specific philosophy school with optional active chat filter"""
    try:
        # First verify the school exists
        school_lookup_id = school_id if school_id.startswith("school_") else f"school_{school_id}"
        school = await db_manager.get_philosophy_school_by_id(school_lookup_id)
        
        if not school:
            raise HTTPException(status_code=404, detail=f"Philosophy school with ID '{school_id}' not found")
        
        # Get philosophers by school_id (without the "school_" prefix)
        clean_school_id = school_id.replace("school_", "") if school_id.startswith("school_") else school_id
        philosophers = await db_manager.get_philosophers_by_school(clean_school_id, skip=skip, limit=limit, is_active_chat=is_active_chat)
        
        # Convert to Pydantic models with school information
        philosopher_with_school_models = []
        school_model = PhilosophySchool(**school)
        
        for philosopher in philosophers:
            try:
                philosopher_model = PhilosopherSummary(**philosopher)
                philosopher_with_school = PhilosopherWithSchool(
                    philosopher=philosopher_model,
                    school=school_model
                )
                philosopher_with_school_models.append(philosopher_with_school)
            except Exception as e:
                logger.warning(f"Failed to parse philosopher {philosopher.get('_id', 'unknown')}: {e}")
                continue
        
        return PhilosopherWithSchoolResponse(
            data=philosopher_with_school_models,
            total_count=len(philosopher_with_school_models),
            message=f"Found {len(philosopher_with_school_models)} philosophers in {school_model.name}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get philosophers for school {school_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve philosophers for school")
