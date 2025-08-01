"""
Search API router - for global search functionality
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
import logging
import time

from ..database import DatabaseManager
from ..models import SearchResponse

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_db_manager():
    """Dependency to get database manager"""
    from ..main import app
    return app.state.db_manager

@router.get("/", response_model=SearchResponse)
async def global_search(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    collections: Optional[str] = Query(None, description="Comma-separated list of collections to search"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Search across all collections or specified collections"""
    try:
        start_time = time.time()
        
        # Parse collections filter if provided
        target_collections = None
        if collections:
            target_collections = [c.strip() for c in collections.split(',')]
            # Validate collection names
            valid_collections = [
                "philosopher_summary", "books", "book_summary", "aphorisms",
                "top_ten_ideas", "idea_summary", "philosophy_themes",
                "modern_adaptation", "discussion_hook", "philosopher_bio",
                "persona_core", "chat_blueprint", "conversation_logic", "philosopher_bot"
            ]
            invalid_collections = [c for c in target_collections if c not in valid_collections]
            if invalid_collections:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid collections: {', '.join(invalid_collections)}. Valid options: {', '.join(valid_collections)}"
                )
        
        # Perform search
        if target_collections:
            # Custom search for specific collections
            results = await search_specific_collections(db_manager, query, target_collections, limit)
        else:
            # Use the global search method
            results = await db_manager.global_search(query, limit)
        
        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        total_results = sum(len(collection_results) for collection_results in results.values())
        
        return SearchResponse(
            query=query,
            results=results,
            total_results=total_results,
            search_time_ms=round(search_time, 2),
            message=f"Found {total_results} results across {len(results)} collections"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform global search: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform search")

async def search_specific_collections(
    db_manager: DatabaseManager, 
    query: str, 
    collections: List[str], 
    limit: int
) -> Dict[str, List[Dict[str, Any]]]:
    """Search within specific collections"""
    results = {}
    per_collection_limit = max(1, limit // len(collections))
    
    for collection_name in collections:
        try:
            collection = db_manager.get_collection(collection_name)
            
            # Create search filter based on collection type
            search_filter = create_search_filter(collection_name, query)
            
            cursor = collection.find(search_filter).limit(per_collection_limit)
            collection_results = await cursor.to_list(length=per_collection_limit)
            
            if collection_results:
                results[collection_name] = collection_results
                
        except Exception as e:
            logger.error(f"Search failed for collection {collection_name}: {e}")
            continue
    
    return results

def create_search_filter(collection_name: str, query: str) -> Dict[str, Any]:
    """Create search filter based on collection structure"""
    
    if collection_name == "philosopher_summary":
        return {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}},
                {"key_concepts": {"$regex": query, "$options": "i"}},
                {"philosophical_schools": {"$regex": query, "$options": "i"}}
            ]
        }
    
    elif collection_name in ["books", "book_summary"]:
        return {
            "$or": [
                {"metadata.title": {"$regex": query, "$options": "i"}},
                {"metadata.author": {"$regex": query, "$options": "i"}},
                {"title": {"$regex": query, "$options": "i"}},
                {"author": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}}
            ]
        }
    
    elif collection_name == "aphorisms":
        return {
            "$or": [
                {"text": {"$regex": query, "$options": "i"}},
                {"author": {"$regex": query, "$options": "i"}},
                {"context": {"$regex": query, "$options": "i"}},
                {"themes": {"$regex": query, "$options": "i"}}
            ]
        }
    
    elif collection_name in ["top_ten_ideas", "idea_summary"]:
        return {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"author": {"$regex": query, "$options": "i"}},
                {"significance": {"$regex": query, "$options": "i"}}
            ]
        }
    
    elif collection_name in ["chat_blueprint", "conversation_logic", "philosopher_bot"]:
        return {
            "$or": [
                {"author": {"$regex": query, "$options": "i"}},
                {"speaking_style": {"$regex": query, "$options": "i"}},
                {"personality_traits": {"$regex": query, "$options": "i"}},
                {"core_beliefs": {"$regex": query, "$options": "i"}}
            ]
        }
    
    else:
        # Generic search for other collections
        return {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}},
                {"author": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}},
                {"themes": {"$regex": query, "$options": "i"}}
            ]
        }

@router.get("/philosophers", response_model=SearchResponse)
async def search_philosophers(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    is_active_chat: Optional[int] = Query(None, description="Filter by active chat availability (0 or 1)"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Search specifically within philosopher-related collections with optional active chat filter"""
    try:
        start_time = time.time()
        
        # Include philosophers collection and apply is_active_chat filter if specified
        if is_active_chat is not None:
            # Use the database manager's search_philosophers method for filtering
            philosophers_results = await db_manager.search_philosophers(query=query, limit=limit, is_active_chat=is_active_chat)
            results = {"philosophers": philosophers_results} if philosophers_results else {}
        else:
            # Search across all philosopher-related collections
            philosopher_collections = ["philosophers", "philosopher_summary", "philosopher_bio", "philosopher_bot"]
            results = await search_specific_collections(db_manager, query, philosopher_collections, limit)
        
        search_time = (time.time() - start_time) * 1000
        total_results = sum(len(collection_results) for collection_results in results.values())
        
        return SearchResponse(
            query=query,
            results=results,
            total_results=total_results,
            search_time_ms=round(search_time, 2),
            message=f"Found {total_results} philosopher-related results"
        )
    
    except Exception as e:
        logger.error(f"Failed to search philosophers: {e}")
        raise HTTPException(status_code=500, detail="Failed to search philosophers")

@router.get("/content", response_model=SearchResponse)
async def search_content(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Search specifically within content collections (books, aphorisms, ideas)"""
    try:
        start_time = time.time()
        
        content_collections = ["books", "book_summary", "aphorisms", "top_ten_ideas", "idea_summary"]
        results = await search_specific_collections(db_manager, query, content_collections, limit)
        
        search_time = (time.time() - start_time) * 1000
        total_results = sum(len(collection_results) for collection_results in results.values())
        
        return SearchResponse(
            query=query,
            results=results,
            total_results=total_results,
            search_time_ms=round(search_time, 2),
            message=f"Found {total_results} content results"
        )
    
    except Exception as e:
        logger.error(f"Failed to search content: {e}")
        raise HTTPException(status_code=500, detail="Failed to search content")

@router.get("/suggestions", response_model=dict)
async def get_search_suggestions(
    query: str = Query(..., min_length=1, description="Partial search query"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of suggestions"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get search suggestions based on partial query"""
    try:
        suggestions = []
        
        # Get philosopher names for suggestions
        philosopher_collection = db_manager.get_collection("philosopher_summary")
        philosopher_cursor = philosopher_collection.find(
            {"name": {"$regex": f"^{query}", "$options": "i"}},
            {"name": 1}
        ).limit(limit)
        philosophers = await philosopher_cursor.to_list(length=limit)
        
        for philosopher in philosophers:
            suggestions.append({
                "text": philosopher["name"],
                "type": "philosopher",
                "category": "Philosophers"
            })
        
        # Get book titles for suggestions
        if len(suggestions) < limit:
            remaining_limit = limit - len(suggestions)
            books_collection = db_manager.get_collection("books")
            books_cursor = books_collection.find(
                {"metadata.title": {"$regex": f"^{query}", "$options": "i"}},
                {"metadata.title": 1}
            ).limit(remaining_limit)
            books = await books_cursor.to_list(length=remaining_limit)
            
            for book in books:
                suggestions.append({
                    "text": book["metadata"]["title"],
                    "type": "book",
                    "category": "Books"
                })
        
        # Get philosophical concepts for suggestions
        if len(suggestions) < limit:
            remaining_limit = limit - len(suggestions)
            ideas_collection = db_manager.get_collection("top_ten_ideas")
            ideas_cursor = ideas_collection.find(
                {"title": {"$regex": f"^{query}", "$options": "i"}},
                {"title": 1}
            ).limit(remaining_limit)
            ideas = await ideas_cursor.to_list(length=remaining_limit)
            
            for idea in ideas:
                suggestions.append({
                    "text": idea["title"],
                    "type": "idea",
                    "category": "Philosophical Ideas"
                })
        
        return {
            "success": True,
            "query": query,
            "suggestions": suggestions[:limit],
            "total_count": len(suggestions[:limit]),
            "message": f"Generated {len(suggestions[:limit])} search suggestions"
        }
    
    except Exception as e:
        logger.error(f"Failed to get search suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate search suggestions")
