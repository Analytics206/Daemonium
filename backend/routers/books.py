"""
Books API router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from ..database import DatabaseManager
from ..models import BookResponse, Book, BookSummary

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_db_manager():
    """Dependency to get database manager"""
    from ..main import app
    return app.state.db_manager

@router.get("/", response_model=BookResponse)
async def get_books(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    author: Optional[str] = Query(None, description="Filter by author"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get all books with pagination and optional author filter"""
    try:
        books = await db_manager.get_books(skip=skip, limit=limit, author=author)
        
        # Convert to Pydantic models
        book_models = []
        for book in books:
            try:
                book_models.append(Book(**book))
            except Exception as e:
                logger.warning(f"Failed to parse book {book.get('_id', 'unknown')}: {e}")
                continue
        
        filter_msg = f" by author '{author}'" if author else ""
        return BookResponse(
            data=book_models,
            total_count=len(book_models),
            message=f"Retrieved {len(book_models)} books{filter_msg}"
        )
    
    except Exception as e:
        logger.error(f"Failed to get books: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve books")

@router.get("/{book_id}", response_model=BookResponse)
async def get_book_by_id(
    book_id: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get a specific book by ID"""
    try:
        book = await db_manager.get_book_by_id(book_id)
        
        if not book:
            raise HTTPException(status_code=404, detail=f"Book with ID '{book_id}' not found")
        
        book_model = Book(**book)
        
        return BookResponse(
            data=book_model,
            message=f"Retrieved book: {book_model.metadata.title}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve book")

@router.get("/summaries/", response_model=BookResponse)
async def get_book_summaries(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get all book summaries with pagination"""
    try:
        summaries = await db_manager.get_book_summaries(skip=skip, limit=limit)
        
        # Convert to Pydantic models
        summary_models = []
        for summary in summaries:
            try:
                summary_models.append(BookSummary(**summary))
            except Exception as e:
                logger.warning(f"Failed to parse book summary {summary.get('_id', 'unknown')}: {e}")
                continue
        
        return BookResponse(
            data=summary_models,
            total_count=len(summary_models),
            message=f"Retrieved {len(summary_models)} book summaries"
        )
    
    except Exception as e:
        logger.error(f"Failed to get book summaries: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve book summaries")

@router.get("/by-author/{author}", response_model=BookResponse)
async def get_books_by_author(
    author: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get books by a specific author"""
    try:
        books = await db_manager.get_books(skip=skip, limit=limit, author=author)
        
        if not books:
            raise HTTPException(status_code=404, detail=f"No books found for author '{author}'")
        
        # Convert to Pydantic models
        book_models = []
        for book in books:
            try:
                book_models.append(Book(**book))
            except Exception as e:
                logger.warning(f"Failed to parse book {book.get('_id', 'unknown')}: {e}")
                continue
        
        return BookResponse(
            data=book_models,
            total_count=len(book_models),
            message=f"Retrieved {len(book_models)} books by {author}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get books by author {author}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve books by author")

@router.get("/{book_id}/chapters", response_model=dict)
async def get_book_chapters(
    book_id: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get chapters for a specific book"""
    try:
        book = await db_manager.get_book_by_id(book_id)
        
        if not book:
            raise HTTPException(status_code=404, detail=f"Book with ID '{book_id}' not found")
        
        chapters = book.get('chapters', [])
        
        return {
            "success": True,
            "book_id": book_id,
            "book_title": book.get('metadata', {}).get('title', 'Unknown'),
            "chapters": chapters,
            "chapter_count": len(chapters),
            "message": f"Retrieved {len(chapters)} chapters for book"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chapters for book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve book chapters")
