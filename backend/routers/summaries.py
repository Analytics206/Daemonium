"""
Summaries API router - for various summary collections
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
import logging

from ..database import DatabaseManager

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_db_manager():
    """Dependency to get database manager"""
    from ..main import app
    return app.state.db_manager

@router.get("/philosophy-themes", response_model=dict)
async def get_philosophy_themes(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get philosophy themes"""
    try:
        collection = db_manager.get_collection("philosophy_themes")
        cursor = collection.find({}).skip(skip).limit(limit)
        themes = await cursor.to_list(length=limit)
        
        return {
            "success": True,
            "data": themes,
            "total_count": len(themes),
            "message": f"Retrieved {len(themes)} philosophy themes"
        }
    
    except Exception as e:
        logger.error(f"Failed to get philosophy themes: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve philosophy themes")

@router.get("/modern-adaptations", response_model=dict)
async def get_modern_adaptations(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    philosopher: Optional[str] = Query(None, description="Filter by philosopher"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get modern adaptations of philosophical ideas"""
    try:
        collection = db_manager.get_collection("modern_adaptation")
        
        filter_query = {}
        if philosopher:
            filter_query["author"] = {"$regex": philosopher, "$options": "i"}
        
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        adaptations = await cursor.to_list(length=limit)
        
        filter_msg = f" by philosopher '{philosopher}'" if philosopher else ""
        return {
            "success": True,
            "data": adaptations,
            "total_count": len(adaptations),
            "message": f"Retrieved {len(adaptations)} modern adaptation{filter_msg}"
        }
    
    except Exception as e:
        logger.error(f"Failed to get modern adaptations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve modern adaptations")

@router.get("/discussion-hooks", response_model=dict)
async def get_discussion_hooks(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get discussion hooks for philosophical conversations"""
    try:
        collection = db_manager.get_collection("discussion_hook")
        
        filter_query = {}
        if topic:
            filter_query = {
                "$or": [
                    {"topic": {"$regex": topic, "$options": "i"}},
                    {"content": {"$regex": topic, "$options": "i"}},
                    {"themes": {"$regex": topic, "$options": "i"}}
                ]
            }
        
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        hooks = await cursor.to_list(length=limit)
        
        filter_msg = f" related to topic '{topic}'" if topic else ""
        return {
            "success": True,
            "data": hooks,
            "total_count": len(hooks),
            "message": f"Retrieved {len(hooks)} discussion hooks{filter_msg}"
        }
    
    except Exception as e:
        logger.error(f"Failed to get discussion hooks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discussion hooks")

@router.get("/philosopher-bios", response_model=dict)
async def get_philosopher_bios(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    era: Optional[str] = Query(None, description="Filter by historical era"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get philosopher biographical information"""
    try:
        collection = db_manager.get_collection("philosopher_bio")
        
        filter_query = {}
        if era:
            filter_query = {
                "$or": [
                    {"era": {"$regex": era, "$options": "i"}},
                    {"time_period": {"$regex": era, "$options": "i"}},
                    {"historical_context": {"$regex": era, "$options": "i"}}
                ]
            }
        
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        bios = await cursor.to_list(length=limit)
        
        filter_msg = f" from era '{era}'" if era else ""
        return {
            "success": True,
            "data": bios,
            "total_count": len(bios),
            "message": f"Retrieved {len(bios)} philosopher biography{filter_msg}"
        }
    
    except Exception as e:
        logger.error(f"Failed to get philosopher bio: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve philosopher bio")

@router.get("/philosopher-bios/search/{author}", response_model=dict)
async def search_philosopher_bios_by_author(
    author: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Search philosopher biographical information by author name"""
    try:
        collection = db_manager.get_collection("philosopher_bio")
        
        # Search filter for philosopher bio collection
        search_filter = {
            "$or": [
                {"author": {"$regex": author, "$options": "i"}},
                {"description": {"$regex": author, "$options": "i"}},
                {"sections.1_life_and_works.content": {"$regex": author, "$options": "i"}},
                {"sections.2_philosophical_development.content": {"$regex": author, "$options": "i"}},
                {"sections.3_major_works.content": {"$regex": author, "$options": "i"}},
                {"sections.4_philosophical_themes.content": {"$regex": author, "$options": "i"}},
                {"sections.5_influence_and_legacy.content": {"$regex": author, "$options": "i"}},
                {"sections.6_personal_life.content": {"$regex": author, "$options": "i"}},
                {"sections.7_criticism_and_controversies.content": {"$regex": author, "$options": "i"}},
                {"sections.8_quotes_and_aphorisms.content": {"$regex": author, "$options": "i"}}
            ]
        }
        
        cursor = collection.find(search_filter).skip(skip).limit(limit)
        bios = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for bio in bios:
            if "_id" in bio:
                bio["_id"] = str(bio["_id"])
        
        if not bios:
            raise HTTPException(status_code=404, detail=f"No philosopher biographies found matching '{author}'")
        
        return {
            "success": True,
            "data": bios,
            "total_count": len(bios),
            "message": f"Found {len(bios)} philosopher biographies matching '{author}'"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search philosopher bios for {author}: {e}")
        raise HTTPException(status_code=500, detail="Failed to search philosopher biographies")

@router.get("/by-collection/{collection_name}", response_model=dict)
async def get_summaries_by_collection(
    collection_name: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get summaries from a specific collection"""
    
    # Valid summary collections (updated to match actual database collection names)
    valid_collections = [
        "philosophy_themes",
        "modern_adaptation", 
        "discussion_hook",
        "philosopher_bio",
        "persona_core",
        "philosopher_summary",
        "book_summary",
        "idea_summary"
    ]
    
    if collection_name not in valid_collections:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid collection. Valid options: {', '.join(valid_collections)}"
        )
    
    try:
        collection = db_manager.get_collection(collection_name)
        cursor = collection.find({}).skip(skip).limit(limit)
        documents = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for doc in documents:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            # Ensure author field mapping for consistency
            if "author" not in doc and "philosopher" in doc:
                doc["author"] = doc["philosopher"]
        
        return {
            "success": True,
            "collection": collection_name,
            "data": documents,
            "total_count": len(documents),
            "message": f"Retrieved {len(documents)} documents from {collection_name}"
        }
    
    except Exception as e:
        logger.error(f"Failed to get summaries from collection {collection_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summaries from {collection_name}")

@router.get("/persona-cores", response_model=dict)
async def get_persona_cores(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    philosopher: Optional[str] = Query(None, description="Filter by philosopher"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get persona cores for philosopher chatbots"""
    try:
        collection = db_manager.get_collection("persona_core")
        
        filter_query = {}
        if philosopher:
            # Search in nested persona structure by author field
            filter_query["persona.author"] = {"$regex": philosopher, "$options": "i"}
        
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        cores = await cursor.to_list(length=limit)
        
        filter_msg = f" for philosopher '{philosopher}'" if philosopher else ""
        return {
            "success": True,
            "data": cores,
            "total_count": len(cores),
            "message": f"Retrieved {len(cores)} persona core{filter_msg}"
        }
    
    except Exception as e:
        logger.error(f"Failed to get persona core: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve persona core")

@router.get("/search/{collection_name}", response_model=dict)
async def search_summaries_collection(
    collection_name: str,
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Search within a specific summary collection"""
    
    # Valid summary collections (updated to match actual database collection names)
    valid_collections = [
        "philosophy_themes",
        "modern_adaptation", 
        "discussion_hook",
        "philosopher_bio",
        "persona_core",
        "philosopher_summary",
        "book_summary",
        "idea_summary"
    ]
    
    if collection_name not in valid_collections:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid collection. Valid options: {', '.join(valid_collections)}"
        )
    
    try:
        collection = db_manager.get_collection(collection_name)
        
        # Enhanced search filter based on collection type
        if collection_name == "book_summary":
            search_filter = {
                "$or": [
                    {"author": {"$regex": query, "$options": "i"}},
                    {"title": {"$regex": query, "$options": "i"}},
                    {"summary.section": {"$regex": query, "$options": "i"}},
                    {"summary.content": {"$regex": query, "$options": "i"}}
                ]
            }
        elif collection_name == "idea_summary":
            search_filter = {
                "$or": [
                    {"author": {"$regex": query, "$options": "i"}},
                    {"title": {"$regex": query, "$options": "i"}},
                    {"quote": {"$regex": query, "$options": "i"}},
                    {"summary.section": {"$regex": query, "$options": "i"}},
                    {"summary.content": {"$regex": query, "$options": "i"}}
                ]
            }
        elif collection_name == "philosopher_summary":
            search_filter = {
                "$or": [
                    {"author": {"$regex": query, "$options": "i"}},
                    {"philosopher": {"$regex": query, "$options": "i"}},
                    {"title": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"sections": {"$regex": query, "$options": "i"}}
                ]
            }
        elif collection_name == "persona_core":
            search_filter = {
                "$or": [
                    {"persona.author": {"$regex": query, "$options": "i"}},
                    {"persona.identity.full_name": {"$regex": query, "$options": "i"}},
                    {"persona.biography.overview": {"$regex": query, "$options": "i"}},
                    {"persona.voice.tone": {"$regex": query, "$options": "i"}},
                    {"persona.voice.style": {"$regex": query, "$options": "i"}}
                ]
            }
        elif collection_name == "philosopher_bio":
            search_filter = {
                "$or": [
                    {"author": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"sections.1_life_and_works.content": {"$regex": query, "$options": "i"}},
                    {"sections.2_philosophical_development.content": {"$regex": query, "$options": "i"}},
                    {"sections.3_major_works.content": {"$regex": query, "$options": "i"}},
                    {"sections.4_philosophical_themes.content": {"$regex": query, "$options": "i"}},
                    {"sections.5_influence_and_legacy.content": {"$regex": query, "$options": "i"}},
                    {"sections.6_personal_life.content": {"$regex": query, "$options": "i"}},
                    {"sections.7_criticism_and_controversies.content": {"$regex": query, "$options": "i"}},
                    {"sections.8_quotes_and_aphorisms.content": {"$regex": query, "$options": "i"}}
                ]
            }
        else:
            # Generic text search across common fields for other collections
            search_filter = {
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"content": {"$regex": query, "$options": "i"}},
                    {"summary": {"$regex": query, "$options": "i"}},
                    {"author": {"$regex": query, "$options": "i"}},
                    {"philosopher": {"$regex": query, "$options": "i"}},
                    {"themes": {"$regex": query, "$options": "i"}},
                    {"topic": {"$regex": query, "$options": "i"}}
                ]
            }
        
        cursor = collection.find(search_filter).limit(limit)
        results = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for doc in results:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            # Ensure author field mapping for consistency
            if "author" not in doc and "philosopher" in doc:
                doc["author"] = doc["philosopher"]
        
        return {
            "success": True,
            "collection": collection_name,
            "query": query,
            "data": results,
            "total_count": len(results),
            "message": f"Found {len(results)} results for '{query}' in {collection_name}"
        }
    
    except Exception as e:
        logger.error(f"Failed to search collection {collection_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search {collection_name}")
