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
                "philosophers", "philosopher_summary", "books", "book_summary", "aphorisms",
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
    
    if collection_name == "philosophers":
        return {
            "$or": [
                {"author": {"$regex": query, "$options": "i"}},
                {"philosopher": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}}
            ]
        }
    
    elif collection_name == "philosopher_summary":
        return {
            "$or": [
                {"author": {"$regex": query, "$options": "i"}},
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"sections": {"$regex": query, "$options": "i"}}
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
    
    elif collection_name == "chat_blueprint":
        return {
            "$or": [
                {"author": {"$regex": query, "$options": "i"}},
                {"speaking_style": {"$regex": query, "$options": "i"}},
                {"personality_traits": {"$regex": query, "$options": "i"}},
                {"core_beliefs": {"$regex": query, "$options": "i"}}
            ]
        }
    
    elif collection_name == "conversation_logic":
        return {
            "$or": [
                {"author": {"$regex": query, "$options": "i"}},
                {"filename": {"$regex": query, "$options": "i"}},
                {"category": {"$regex": query, "$options": "i"}},
                {"conversation_logic.primary_goal": {"$regex": query, "$options": "i"}},
                {"conversation_logic.response_strategy.core_principles": {"$regex": query, "$options": "i"}},
                {"conversation_logic.response_strategy.response_structure": {"$regex": query, "$options": "i"}},
                {"conversation_logic.tone_selection.modes": {"$regex": query, "$options": "i"}},
                {"conversation_logic.provocation_methods.techniques": {"$regex": query, "$options": "i"}},
                {"conversation_logic.dynamic_response_templates": {"$regex": query, "$options": "i"}},
                {"conversation_logic.prohibited_patterns": {"$regex": query, "$options": "i"}},
                {"conversation_logic.conversation_flow.opening_moves": {"$regex": query, "$options": "i"}},
                {"conversation_logic.conversation_flow.closing_moves": {"$regex": query, "$options": "i"}},
                {"conversation_logic.fallbacks.when_unknown": {"$regex": query, "$options": "i"}}
            ]
        }
    
    elif collection_name == "philosopher_bot":
        return {
            "$or": [
                {"persona.author": {"$regex": query, "$options": "i"}},
                {"persona.style.speaking_style": {"$regex": query, "$options": "i"}},
                {"persona.personality_traits": {"$regex": query, "$options": "i"}},
                {"persona.philosophical_themes": {"$regex": query, "$options": "i"}},
                {"instructions.primary_goal": {"$regex": query, "$options": "i"}},
                {"instructions.behavior": {"$regex": query, "$options": "i"}}
            ]
        }
    
    elif collection_name == "philosopher_bio":
        return {
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
        
        # Get philosopher names for suggestions (correct collection and field names)
        philosopher_collection = db_manager.get_collection("philosophers")
        philosopher_cursor = philosopher_collection.find(
            {"$or": [
                {"author": {"$regex": f"^{query}", "$options": "i"}},
                {"philosopher": {"$regex": f"^{query}", "$options": "i"}}
            ]},
            {"author": 1, "philosopher": 1}
        ).limit(limit)
        philosophers = await philosopher_cursor.to_list(length=limit)
        
        for philosopher in philosophers:
            # Use author field or fallback to philosopher field
            name = philosopher.get("author") or philosopher.get("philosopher", "Unknown")
            suggestions.append({
                "text": name,
                "type": "philosopher",
                "category": "Philosophers"
            })
        
        # Get book titles for suggestions (try different field structures)
        if len(suggestions) < limit:
            remaining_limit = limit - len(suggestions)
            books_collection = db_manager.get_collection("books")
            # Try multiple field structures for books
            books_cursor = books_collection.find(
                {"$or": [
                    {"title": {"$regex": f"^{query}", "$options": "i"}},
                    {"metadata.title": {"$regex": f"^{query}", "$options": "i"}},
                    {"book_title": {"$regex": f"^{query}", "$options": "i"}}
                ]},
                {"title": 1, "metadata.title": 1, "book_title": 1}
            ).limit(remaining_limit)
            books = await books_cursor.to_list(length=remaining_limit)
            
            for book in books:
                # Try different field names for title
                title = book.get("title") or book.get("metadata", {}).get("title") or book.get("book_title", "Unknown Book")
                suggestions.append({
                    "text": title,
                    "type": "book",
                    "category": "Books"
                })
        
        # Get philosophical concepts for suggestions (correct collection name)
        if len(suggestions) < limit:
            remaining_limit = limit - len(suggestions)
            ideas_collection = db_manager.get_collection("top_10_ideas")
            # Handle nested structure for ideas
            ideas_cursor = ideas_collection.find(
                {"$or": [
                    {"title": {"$regex": f"^{query}", "$options": "i"}},
                    {"top_ideas.idea": {"$regex": f"^{query}", "$options": "i"}}
                ]},
                {"title": 1, "top_ideas": 1}
            ).limit(remaining_limit)
            ideas = await ideas_cursor.to_list(length=remaining_limit)
            
            for idea in ideas:
                # Handle both flat and nested structures
                if "title" in idea:
                    suggestions.append({
                        "text": idea["title"],
                        "type": "idea",
                        "category": "Philosophical Ideas"
                    })
                elif "top_ideas" in idea and isinstance(idea["top_ideas"], list):
                    for top_idea in idea["top_ideas"]:
                        if isinstance(top_idea, dict) and "idea" in top_idea:
                            suggestions.append({
                                "text": top_idea["idea"],
                                "type": "idea",
                                "category": "Philosophical Ideas"
                            })
                            if len(suggestions) >= limit:
                                break
        
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
