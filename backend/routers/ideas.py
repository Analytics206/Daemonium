"""
Ideas API router
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional
import logging

from ..database import DatabaseManager
from ..models import IdeasResponse, TopTenIdea, IdeaSummary

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_db_manager():
    """Dependency to get database manager"""
    from ..main import app
    return app.state.db_manager

@router.get("/top-ten", response_model=IdeasResponse)
async def get_top_ten_ideas(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get top ten philosophical ideas with pagination"""
    try:
        ideas = await db_manager.get_top_ideas(skip=skip, limit=limit)
        
        # Convert to Pydantic models
        idea_models = []
        for idea in ideas:
            try:
                idea_models.append(TopTenIdea(**idea))
            except Exception as e:
                logger.warning(f"Failed to parse top ten idea {idea.get('_id', 'unknown')}: {e}")
                continue
        
        # Sort by rank if available
        idea_models.sort(key=lambda x: x.rank if hasattr(x, 'rank') and x.rank else 999)
        
        return IdeasResponse(
            data=idea_models,
            total_count=len(idea_models),
            message=f"Retrieved {len(idea_models)} top philosophical ideas"
        )
    
    except Exception as e:
        logger.error(f"Failed to get top ten ideas: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve top ten ideas")

@router.get("/summaries", response_model=IdeasResponse)
async def get_idea_summaries(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    philosopher: Optional[str] = Query(None, description="Filter by philosopher"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get idea summaries with pagination and optional filters"""
    try:
        ideas = await db_manager.get_idea_summaries(skip=skip, limit=limit)
        
        # Apply filters if provided
        if philosopher or category:
            filtered_ideas = []
            for idea in ideas:
                include_idea = True
                
                if philosopher and idea.get('author'):
                    if philosopher.lower() not in idea['author'].lower():
                        include_idea = False
                
                if category and idea.get('category'):
                    if category.lower() not in idea['category'].lower():
                        include_idea = False
                
                if include_idea:
                    filtered_ideas.append(idea)
            
            ideas = filtered_ideas
        
        # Convert to Pydantic models
        idea_models = []
        for idea in ideas:
            try:
                idea_models.append(IdeaSummary(**idea))
            except Exception as e:
                logger.warning(f"Failed to parse idea summary {idea.get('_id', 'unknown')}: {e}")
                continue
        
        filter_msg = ""
        if philosopher:
            filter_msg += f" by philosopher '{philosopher}'"
        if category:
            filter_msg += f" in category '{category}'"
        
        return IdeasResponse(
            data=idea_models,
            total_count=len(idea_models),
            message=f"Retrieved {len(idea_models)} idea summaries{filter_msg}"
        )
    
    except Exception as e:
        logger.error(f"Failed to get idea summaries: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve idea summaries")

@router.get("/top-ten/{rank}", response_model=IdeasResponse)
async def get_top_idea_by_rank(
    rank: int = Path(..., ge=1, le=10, description="Rank of the idea (1-10)"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get a specific top ten idea by rank"""
    try:
        collection = db_manager.get_collection("top_10_ideas")
        idea = await collection.find_one({"rank": rank})
        
        if not idea:
            raise HTTPException(status_code=404, detail=f"No idea found with rank {rank}")
        
        # Convert ObjectId to string and ensure proper field mapping
        if "_id" in idea:
            idea["_id"] = str(idea["_id"])
        # Ensure we have the required fields
        if "author" not in idea and "philosopher" in idea:
            idea["author"] = idea["philosopher"]
        
        idea_model = TopTenIdea(**idea)
        
        return IdeasResponse(
            data=idea_model,
            message=f"Retrieved idea #{rank}: {idea_model.title}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get idea by rank {rank}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve idea by rank")

@router.get("/by-philosopher/{philosopher}", response_model=IdeasResponse)
async def get_ideas_by_philosopher(
    philosopher: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    include_summaries: bool = Query(True, description="Include idea summaries in results"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get ideas by a specific philosopher from both collections"""
    try:
        all_ideas = []
        
        # Get from top_10_ideas collection
        top_ten_collection = db_manager.get_collection("top_10_ideas")
        top_ten_cursor = top_ten_collection.find(
            {"$or": [
                {"author": {"$regex": philosopher, "$options": "i"}},
                {"philosopher": {"$regex": philosopher, "$options": "i"}}
            ]}
        ).limit(limit)
        top_ten_ideas = await top_ten_cursor.to_list(length=limit)
        
        # Convert ObjectId to string and ensure proper field mapping for top ten ideas
        for idea in top_ten_ideas:
            if "_id" in idea:
                idea["_id"] = str(idea["_id"])
            if "author" not in idea and "philosopher" in idea:
                idea["author"] = idea["philosopher"]
        
        # Get from idea_summaries collection if requested
        if include_summaries:
            summaries_collection = db_manager.get_collection("idea_summary")
            summaries_cursor = summaries_collection.find(
                {"$or": [
                    {"author": {"$regex": philosopher, "$options": "i"}},
                    {"philosopher": {"$regex": philosopher, "$options": "i"}}
                ]}
            ).limit(limit)
            idea_summaries = await summaries_cursor.to_list(length=limit)
            
            # Convert ObjectId to string and ensure proper field mapping for idea summaries
            for idea in idea_summaries:
                if "_id" in idea:
                    idea["_id"] = str(idea["_id"])
                if "author" not in idea and "philosopher" in idea:
                    idea["author"] = idea["philosopher"]
        else:
            idea_summaries = []
        
        # Convert to Pydantic models
        idea_models = []
        
        # Add top ten ideas
        for idea in top_ten_ideas:
            try:
                idea_models.append(TopTenIdea(**idea))
            except Exception as e:
                logger.warning(f"Failed to parse top ten idea {idea.get('_id', 'unknown')}: {e}")
                continue
        
        # Add idea summaries
        for idea in idea_summaries:
            try:
                idea_models.append(IdeaSummary(**idea))
            except Exception as e:
                logger.warning(f"Failed to parse idea summary {idea.get('_id', 'unknown')}: {e}")
                continue
        
        if not idea_models:
            raise HTTPException(status_code=404, detail=f"No ideas found for philosopher '{philosopher}'")
        
        return IdeasResponse(
            data=idea_models,
            total_count=len(idea_models),
            message=f"Retrieved {len(idea_models)} ideas by {philosopher}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ideas by philosopher {philosopher}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ideas by philosopher")

@router.get("/search/{keyword}", response_model=IdeasResponse)
async def search_ideas_by_keyword(
    keyword: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Search for ideas by keyword, searching through the JSON tree structure"""
    try:
        matching_ideas = []
        
        # Search in top_10_ideas collection
        top_ten_collection = db_manager.get_collection("top_10_ideas")
        top_ten_cursor = top_ten_collection.find({
            "$or": [
                {"author": {"$regex": keyword, "$options": "i"}},
                {"category": {"$regex": keyword, "$options": "i"}},
                {"top_ideas.idea": {"$regex": keyword, "$options": "i"}},
                {"top_ideas.description": {"$regex": keyword, "$options": "i"}},
                {"top_ideas.key_books": {"$regex": keyword, "$options": "i"}}
            ]
        })
        
        async for idea in top_ten_cursor:
            # Convert ObjectId to string and ensure proper field mapping
            if "_id" in idea:
                idea["_id"] = str(idea["_id"])
            if "author" not in idea and "philosopher" in idea:
                idea["author"] = idea["philosopher"]
            
            try:
                idea_model = TopTenIdea(**idea)
                matching_ideas.append(idea_model)
            except Exception as e:
                logger.warning(f"Failed to parse top ten idea {idea.get('_id', 'unknown')}: {e}")
                continue
        
        # Search in idea_summary collection
        summaries_collection = db_manager.get_collection("idea_summary")
        summaries_cursor = summaries_collection.find({
            "$or": [
                {"author": {"$regex": keyword, "$options": "i"}},
                {"category": {"$regex": keyword, "$options": "i"}},
                {"title": {"$regex": keyword, "$options": "i"}},
                {"quote": {"$regex": keyword, "$options": "i"}},
                {"summary.section": {"$regex": keyword, "$options": "i"}},
                {"summary.content": {"$regex": keyword, "$options": "i"}}
            ]
        })
        
        async for idea in summaries_cursor:
            # Convert ObjectId to string and ensure proper field mapping
            if "_id" in idea:
                idea["_id"] = str(idea["_id"])
            if "author" not in idea and "philosopher" in idea:
                idea["author"] = idea["philosopher"]
            
            try:
                idea_model = IdeaSummary(**idea)
                matching_ideas.append(idea_model)
            except Exception as e:
                logger.warning(f"Failed to parse idea summary {idea.get('_id', 'unknown')}: {e}")
                continue
        
        if not matching_ideas:
            raise HTTPException(status_code=404, detail=f"No ideas found matching keyword '{keyword}'")
        
        return IdeasResponse(
            data=matching_ideas,
            total_count=len(matching_ideas),
            message=f"Found {len(matching_ideas)} ideas matching keyword '{keyword}'"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search ideas with keyword {keyword}: {e}")
        raise HTTPException(status_code=500, detail="Failed to search ideas")
