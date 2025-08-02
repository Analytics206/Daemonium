"""
Aphorisms API router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from ..database import DatabaseManager
from ..models import AphorismResponse, Aphorism

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_db_manager():
    """Dependency to get database manager"""
    from ..main import app
    return app.state.db_manager

@router.get("/", response_model=AphorismResponse)
async def get_aphorisms(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    philosopher: Optional[str] = Query(None, description="Filter by philosopher"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get all aphorisms with pagination and optional philosopher filter"""
    try:
        aphorisms = await db_manager.get_aphorisms(skip=skip, limit=limit, philosopher=philosopher)
        
        # Convert to Pydantic models
        aphorism_models = []
        for aphorism in aphorisms:
            try:
                aphorism_models.append(Aphorism(**aphorism))
            except Exception as e:
                logger.warning(f"Failed to parse aphorism {aphorism.get('_id', 'unknown')}: {e}")
                continue
        
        filter_msg = f" by philosopher '{philosopher}'" if philosopher else ""
        return AphorismResponse(
            data=aphorism_models,
            total_count=len(aphorism_models),
            message=f"Retrieved {len(aphorism_models)} aphorisms{filter_msg}"
        )
    
    except Exception as e:
        logger.error(f"Failed to get aphorisms: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve aphorisms")

@router.get("/random", response_model=AphorismResponse)
async def get_random_aphorisms(
    count: int = Query(5, ge=1, le=20, description="Number of random aphorisms to return"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get random aphorisms"""
    try:
        aphorisms = await db_manager.get_random_aphorisms(count=count)
        
        # Convert to Pydantic models
        aphorism_models = []
        for aphorism in aphorisms:
            try:
                aphorism_models.append(Aphorism(**aphorism))
            except Exception as e:
                logger.warning(f"Failed to parse aphorism {aphorism.get('_id', 'unknown')}: {e}")
                continue
        
        return AphorismResponse(
            data=aphorism_models,
            total_count=len(aphorism_models),
            message=f"Retrieved {len(aphorism_models)} random aphorisms"
        )
    
    except Exception as e:
        logger.error(f"Failed to get random aphorisms: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve random aphorisms")

@router.get("/by-philosopher/{philosopher}", response_model=AphorismResponse)
async def get_aphorisms_by_philosopher(
    philosopher: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get aphorisms by a specific philosopher"""
    try:
        aphorisms = await db_manager.get_aphorisms(skip=skip, limit=limit, philosopher=philosopher)
        
        if not aphorisms:
            raise HTTPException(status_code=404, detail=f"No aphorisms found for philosopher '{philosopher}'")
        
        # Convert to Pydantic models
        aphorism_models = []
        for aphorism in aphorisms:
            try:
                aphorism_models.append(Aphorism(**aphorism))
            except Exception as e:
                logger.warning(f"Failed to parse aphorism {aphorism.get('_id', 'unknown')}: {e}")
                continue
        
        return AphorismResponse(
            data=aphorism_models,
            total_count=len(aphorism_models),
            message=f"Retrieved {len(aphorism_models)} aphorisms by {philosopher}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get aphorisms by philosopher {philosopher}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve aphorisms by philosopher")

@router.get("/by-theme/{theme}", response_model=AphorismResponse)
async def get_aphorisms_by_theme(
    theme: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get aphorisms by theme"""
    try:
        # Search for aphorisms containing the theme in their themes array or text
        collection = db_manager.get_collection("aphorisms")
        
        search_filter = {
            "$or": [
                {"themes": {"$regex": theme, "$options": "i"}},
                {"text": {"$regex": theme, "$options": "i"}},
                {"context": {"$regex": theme, "$options": "i"}}
            ]
        }
        
        cursor = collection.find(search_filter).skip(skip).limit(limit)
        aphorisms = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string and ensure proper field mapping
        for aphorism in aphorisms:
            if "_id" in aphorism:
                aphorism["_id"] = str(aphorism["_id"])
            # Ensure we have the required fields
            if "author" not in aphorism and "philosopher" in aphorism:
                aphorism["author"] = aphorism["philosopher"]
        
        if not aphorisms:
            raise HTTPException(status_code=404, detail=f"No aphorisms found for theme '{theme}'")
        
        # Convert to Pydantic models
        aphorism_models = []
        for aphorism in aphorisms:
            try:
                aphorism_models.append(Aphorism(**aphorism))
            except Exception as e:
                logger.warning(f"Failed to parse aphorism {aphorism.get('_id', 'unknown')}: {e}")
                continue
        
        return AphorismResponse(
            data=aphorism_models,
            total_count=len(aphorism_models),
            message=f"Retrieved {len(aphorism_models)} aphorisms related to theme '{theme}'"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get aphorisms by theme {theme}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve aphorisms by theme")

@router.get("/{aphorism_id}", response_model=AphorismResponse)
async def get_aphorism_by_id(
    aphorism_id: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get a specific aphorism by ID"""
    try:
        from bson import ObjectId
        collection = db_manager.get_collection("aphorisms")
        
        # Try to find by ObjectId first, then by string ID
        aphorism = None
        try:
            aphorism = await collection.find_one({"_id": ObjectId(aphorism_id)})
        except:
            # If ObjectId conversion fails, try as string
            aphorism = await collection.find_one({"_id": aphorism_id})
        
        if not aphorism:
            raise HTTPException(status_code=404, detail=f"Aphorism with ID '{aphorism_id}' not found")
        
        # Convert ObjectId to string and ensure proper field mapping
        if "_id" in aphorism:
            aphorism["_id"] = str(aphorism["_id"])
        # Ensure we have the required fields
        if "author" not in aphorism and "philosopher" in aphorism:
            aphorism["author"] = aphorism["philosopher"]
        
        aphorism_model = Aphorism(**aphorism)
        
        return AphorismResponse(
            data=aphorism_model,
            message=f"Retrieved aphorism by {aphorism_model.philosopher}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get aphorism {aphorism_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve aphorism")
