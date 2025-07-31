"""
Pydantic models for Daemonium API
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Base models
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaginationParams(BaseModel):
    """Pagination parameters"""
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of items to return")

class SearchParams(BaseModel):
    """Search parameters"""
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")

# Philosopher models
class PhilosopherSummary(BaseModel):
    """Philosopher summary model"""
    id: str = Field(..., alias="_id")
    name: str
    summary: Optional[str] = None
    key_concepts: Optional[List[str]] = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    nationality: Optional[str] = None
    major_works: Optional[List[str]] = None
    philosophical_school: Optional[str] = None
    influences: Optional[List[str]] = None
    influenced: Optional[List[str]] = None
    
    model_config = {"populate_by_name": True}

class PhilosopherResponse(BaseResponse):
    """Response model for philosopher data"""
    data: Union[PhilosopherSummary, List[PhilosopherSummary]]
    total_count: Optional[int] = None

# Book models
class BookMetadata(BaseModel):
    """Book metadata model"""
    title: str
    author: str
    language: Optional[str] = None
    publication_year: Optional[int] = None
    genre: Optional[str] = None
    isbn: Optional[str] = None

class Book(BaseModel):
    """Book model"""
    id: str = Field(..., alias="_id")
    metadata: BookMetadata
    content: Optional[str] = None
    chapters: Optional[List[Dict[str, Any]]] = None
    word_count: Optional[int] = None
    
    model_config = {"populate_by_name": True}

class BookSummary(BaseModel):
    """Book summary model"""
    id: str = Field(..., alias="_id")
    title: str
    author: str
    summary: str
    key_themes: Optional[List[str]] = None
    main_arguments: Optional[List[str]] = None
    significance: Optional[str] = None
    
    model_config = {"populate_by_name": True}

class BookResponse(BaseResponse):
    """Response model for book data"""
    data: Union[Book, BookSummary, List[Union[Book, BookSummary]]]
    total_count: Optional[int] = None

# Aphorism models
class Aphorism(BaseModel):
    """Aphorism model"""
    id: str = Field(..., alias="_id")
    text: str
    philosopher: str
    source: Optional[str] = None
    context: Optional[str] = None
    themes: Optional[List[str]] = None
    interpretation: Optional[str] = None
    
    model_config = {"populate_by_name": True}

class AphorismResponse(BaseResponse):
    """Response model for aphorism data"""
    data: Union[Aphorism, List[Aphorism]]
    total_count: Optional[int] = None

# Ideas models
class TopTenIdea(BaseModel):
    """Top ten philosophical idea model"""
    id: str = Field(..., alias="_id")
    rank: int
    title: str
    description: str
    philosopher: str
    significance: Optional[str] = None
    modern_relevance: Optional[str] = None
    related_concepts: Optional[List[str]] = None
    
    model_config = {"populate_by_name": True}

class IdeaSummary(BaseModel):
    """Idea summary model"""
    id: str = Field(..., alias="_id")
    title: str
    description: str
    philosopher: Optional[str] = None
    category: Optional[str] = None
    key_points: Optional[List[str]] = None
    examples: Optional[List[str]] = None
    
    model_config = {"populate_by_name": True}

class IdeasResponse(BaseResponse):
    """Response model for ideas data"""
    data: Union[TopTenIdea, IdeaSummary, List[Union[TopTenIdea, IdeaSummary]]]
    total_count: Optional[int] = None

# Chat models
class ChatBlueprint(BaseModel):
    """Chat blueprint model"""
    id: str = Field(..., alias="_id")
    philosopher: str
    personality_traits: Optional[List[str]] = None
    speaking_style: Optional[str] = None
    core_beliefs: Optional[List[str]] = None
    typical_responses: Optional[Dict[str, str]] = None
    conversation_starters: Optional[List[str]] = None
    
    model_config = {"populate_by_name": True}

class ConversationLogic(BaseModel):
    """Conversation logic model"""
    id: str = Field(..., alias="_id")
    philosopher: str
    response_patterns: Optional[Dict[str, Any]] = None
    topic_preferences: Optional[List[str]] = None
    argumentation_style: Optional[str] = None
    question_handling: Optional[Dict[str, str]] = None
    
    model_config = {"populate_by_name": True}

class PhilosopherBot(BaseModel):
    """Philosopher bot configuration model"""
    id: str = Field(..., alias="_id")
    philosopher: str
    bot_config: Optional[Dict[str, Any]] = None
    prompt_template: Optional[str] = None
    system_message: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    
    model_config = {"populate_by_name": True}

class ChatMessage(BaseModel):
    """Chat message model"""
    message: str = Field(..., min_length=1, description="User message")
    philosopher: Optional[str] = Field(None, description="Target philosopher for response")
    context: Optional[str] = Field(None, description="Additional context")

class ChatResponse(BaseResponse):
    """Chat response model"""
    response: str
    philosopher: str
    confidence: Optional[float] = None
    sources: Optional[List[str]] = None

class ChatBlueprintResponse(BaseResponse):
    """Response model for chat blueprint data"""
    data: Union[ChatBlueprint, ConversationLogic, PhilosopherBot, List[Union[ChatBlueprint, ConversationLogic, PhilosopherBot]]]
    total_count: Optional[int] = None

# Search models
class SearchResult(BaseModel):
    """Search result model"""
    collection: str
    document_id: str
    title: Optional[str] = None
    content_snippet: Optional[str] = None
    relevance_score: Optional[float] = None

class SearchResponse(BaseResponse):
    """Search response model"""
    query: str
    results: Dict[str, List[Dict[str, Any]]]
    total_results: int
    search_time_ms: Optional[float] = None

# Statistics models
class CollectionStats(BaseModel):
    """Collection statistics model"""
    collection_name: str
    document_count: int
    
class StatsResponse(BaseResponse):
    """Statistics response model"""
    api_version: str
    collections: Dict[str, int]
    total_documents: int

# Error models
class ErrorDetail(BaseModel):
    """Error detail model"""
    code: str
    message: str
    field: Optional[str] = None

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Health check models
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    database: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
