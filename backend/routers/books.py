"""
Books API router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from ..database import DatabaseManager
from ..models import BookResponse, Book, BookSummary, BibliographyResponse, Bibliography

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

@router.get("/bibliography", response_model=BibliographyResponse)
async def get_bibliographies(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    author: Optional[str] = Query(None, description="Filter by author"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get all bibliographies with pagination and optional author filter"""
    try:
        bibliographies = await db_manager.get_bibliographies(skip=skip, limit=limit, author=author)
        
        # Convert to Pydantic models
        bibliography_models = []
        for bibliography in bibliographies:
            try:
                bibliography_models.append(Bibliography(**bibliography))
            except Exception as e:
                logger.warning(f"Failed to parse bibliography {bibliography.get('_id', 'unknown')}: {e}")
                continue
        
        filter_msg = f" by author '{author}'" if author else ""
        return BibliographyResponse(
            data=bibliography_models,
            total_count=len(bibliography_models),
            message=f"Retrieved {len(bibliography_models)} bibliographies{filter_msg}"
        )
    
    except Exception as e:
        logger.error(f"Failed to get bibliographies: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bibliographies")

@router.get("/bibliography/search/", response_model=BibliographyResponse)
async def search_bibliographies(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Search bibliographies by author, description, or content"""
    try:
        bibliographies = await db_manager.search_bibliographies(query=query, limit=limit)
        
        if not bibliographies:
            return BibliographyResponse(
                data=[],
                total_count=0,
                message=f"No bibliographies found for query: '{query}'"
            )
        
        # Convert to Pydantic models
        bibliography_models = []
        for bibliography in bibliographies:
            try:
                bibliography_models.append(Bibliography(**bibliography))
            except Exception as e:
                logger.warning(f"Failed to parse bibliography {bibliography.get('_id', 'unknown')}: {e}")
                continue
        
        return BibliographyResponse(
            data=bibliography_models,
            total_count=len(bibliography_models),
            message=f"Found {len(bibliography_models)} bibliographies for query: '{query}'"
        )
    
    except Exception as e:
        logger.error(f"Failed to search bibliographies: {e}")
        raise HTTPException(status_code=500, detail="Failed to search bibliographies")

@router.get("/bibliography/by-author/{author}", response_model=BibliographyResponse)
async def get_bibliography_by_author(
    author: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get bibliography by author name"""
    try:
        bibliography = await db_manager.get_bibliography_by_author(author)
        
        if not bibliography:
            raise HTTPException(status_code=404, detail=f"No bibliography found for author '{author}'")
        
        bibliography_model = Bibliography(**bibliography)
        
        return BibliographyResponse(
            data=bibliography_model,
            message=f"Retrieved bibliography for: {bibliography_model.author}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bibliography for author {author}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bibliography by author")

@router.get("/bibliography/{bibliography_id}", response_model=BibliographyResponse)
async def get_bibliography_by_id(
    bibliography_id: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get a specific bibliography by ID"""
    try:
        bibliography = await db_manager.get_bibliography_by_id(bibliography_id)
        
        if not bibliography:
            raise HTTPException(status_code=404, detail=f"Bibliography with ID '{bibliography_id}' not found")
        
        bibliography_model = Bibliography(**bibliography)
        
        return BibliographyResponse(
            data=bibliography_model,
            message=f"Retrieved bibliography for: {bibliography_model.author}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bibliography {bibliography_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bibliography")

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
