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
    author: str  # Primary field - all collections join by author
    philosopher: Optional[str] = None  # Alternative name field
    
    # Date fields - handle both string and date formats
    dob: Optional[str] = Field(None, alias="date_of_birth")  # Date of birth
    dod: Optional[str] = Field(None, alias="date_of_death")  # Date of death
    date_of_birth: Optional[str] = None
    date_of_death: Optional[str] = None
    
    summary: Optional[str] = None
    content: Optional[str] = None
    school_id: Optional[Union[int, str]] = None  # Handle both int and string
    tag_id: Optional[Union[int, str]] = None     # Handle both int and string
    is_active_chat: Optional[int] = None  # Flag for active chat availability (0 or 1)
    lifespan_years: Optional[int] = None
    
    model_config = {"populate_by_name": True}

class PhilosopherResponse(BaseResponse):
    """Response model for philosopher data"""
    data: Union[PhilosopherSummary, List[PhilosopherSummary]]
    total_count: Optional[int] = None

# Philosophy School models
class PhilosophySchool(BaseModel):
    """Philosophy school model"""
    id: str = Field(..., alias="_id")
    school_id: Optional[Union[int, str]] = None  # Handle both int and string
    schoolID: Optional[Union[int, str]] = None   # From JSON structure
    
    name: Optional[str] = None
    school: Optional[str] = None  # From JSON structure
    category: Optional[str] = None
    summary: Optional[str] = None
    core_principles: Optional[str] = None
    corePrinciples: Optional[str] = None  # From JSON structure
    
    # Normalized fields
    name_normalized: Optional[str] = None
    category_normalized: Optional[str] = None
    keywords: Optional[List[str]] = None
    
    model_config = {"populate_by_name": True}

class PhilosophySchoolResponse(BaseResponse):
    """Response model for philosophy school data"""
    data: Union[PhilosophySchool, List[PhilosophySchool]]
    total_count: Optional[int] = None

class PhilosopherWithSchool(BaseModel):
    """Philosopher with associated school information"""
    philosopher: PhilosopherSummary
    school: Optional[PhilosophySchool] = None

class PhilosopherWithSchoolResponse(BaseResponse):
    """Response model for philosopher with school data"""
    data: Union[PhilosopherWithSchool, List[PhilosopherWithSchool]]
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

class BookSummaryResponse(BaseResponse):
    """Response model for book summary data"""
    data: Union[BookSummary, List[BookSummary]]
    total_count: Optional[int] = None

# Aphorism models
class Aphorism(BaseModel):
    """Aphorism model"""
    id: str = Field(..., alias="_id")
    author: str  # Primary field for author name
    category: Optional[str] = None  # Category of aphorisms (e.g., "Aphorisms")
    
    # Handle both single aphorism and nested structure
    text: Optional[str] = None  # For individual aphorism text
    aphorisms: Optional[Dict[str, List[str]]] = None  # For nested structure
    
    # Additional fields
    source: Optional[str] = None
    context: Optional[str] = None
    themes: Optional[List[str]] = None
    interpretation: Optional[str] = None
    
    # For backward compatibility
    @property
    def philosopher(self) -> str:
        return self.author
    
    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

class AphorismResponse(BaseResponse):
    """Response model for aphorism data"""
    data: Union[Aphorism, List[Aphorism]]
    total_count: Optional[int] = None

# Ideas models
class TopTenIdea(BaseModel):
    """Top ten philosophical idea model"""
    id: str = Field(..., alias="_id")
    filename: Optional[str] = None
    author: str  # Primary field for author name
    category: Optional[str] = None  # Category field (e.g., "Top 10 Ideas")
    
    # Main structure - array of ideas with rank, idea, description, key_books
    top_ideas: Optional[List[Dict[str, Any]]] = None  # Array of idea objects
    
    # Metadata from upload
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = {"populate_by_name": True}

class IdeaSummary(BaseModel):
    """Idea summary model"""
    id: str = Field(..., alias="_id")
    author: str  # Primary field for author name
    category: Optional[str] = None  # Category field (e.g., "Idea Summary")
    
    # Core fields matching JSON structure
    title: Optional[str] = None  # Title of the idea
    quote: Optional[str] = None  # Quote associated with the idea
    summary: Optional[List[Dict[str, Any]]] = None  # List of sections with "section" and "content" fields
    key_books: Optional[List[str]] = None  # List of 5 key books related to the idea
    
    model_config = {"populate_by_name": True}

class IdeasResponse(BaseResponse):
    """Response model for ideas data"""
    data: Union[TopTenIdea, IdeaSummary, List[Union[TopTenIdea, IdeaSummary]]]
    total_count: Optional[int] = None

class IdeaSummaryResponse(BaseResponse):
    """Response model for idea summary data"""
    data: Union[IdeaSummary, List[IdeaSummary]]
    total_count: Optional[int] = None

class TopTenIdeasResponse(BaseResponse):
    """Response model for top ten ideas data"""
    data: Union[TopTenIdea, List[TopTenIdea]]
    total_count: Optional[int] = None

# Modern Adaptation models
class ContextAwareness(BaseModel):
    """Context awareness model for modern adaptations"""
    historical_self_reference: Optional[List[str]] = None
    era_contrast_rules: Optional[List[str]] = None

class ModernTopic(BaseModel):
    """Modern topic model for modern adaptations"""
    name: str
    analysis: Optional[str] = None
    view: Optional[List[str]] = None
    sample_responses: Optional[List[str]] = None
    discussion_hooks: Optional[List[str]] = None

class AdaptiveTemplate(BaseModel):
    """Adaptive template model for modern adaptations"""
    pattern: str

class ModernAdaptationData(BaseModel):
    """Modern adaptation data model"""
    purpose: Optional[str] = None
    context_awareness: Optional[ContextAwareness] = None
    modern_topics: Optional[List[ModernTopic]] = None
    adaptive_templates: Optional[List[AdaptiveTemplate]] = None
    tone_instructions: Optional[Dict[str, str]] = None  # Dynamic section with varying keys

class ModernAdaptation(BaseModel):
    """Modern adaptation model"""
    id: str = Field(..., alias="_id")
    filename: Optional[str] = None
    author: str
    category: Optional[str] = None
    modern_adaptation: Optional[ModernAdaptationData] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # For backward compatibility
    @property
    def philosopher(self) -> str:
        return self.author
    
    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

class ModernAdaptationResponse(BaseResponse):
    """Response model for modern adaptation data"""
    data: Union[ModernAdaptation, List[ModernAdaptation]]
    total_count: Optional[int] = None

# Chat models
class ChatBlueprint(BaseModel):
    """Chat blueprint model"""
    id: str = Field(..., alias="_id")
    author: str  # Changed from philosopher to author
    personality_traits: Optional[List[str]] = None
    speaking_style: Optional[str] = None
    core_beliefs: Optional[List[str]] = None
    typical_responses: Optional[Dict[str, str]] = None
    conversation_starters: Optional[List[str]] = None
    
    model_config = {"populate_by_name": True}

class ResponseStrategy(BaseModel):
    """Response strategy nested model"""
    core_principles: Optional[List[str]] = []
    response_structure: Optional[List[str]] = []
    
    model_config = {"extra": "allow"}

class ToneSelection(BaseModel):
    """Tone selection nested model"""
    modes: Optional[List[Dict[str, Any]]] = []  # Changed from List[str] to List[Dict]
    
    model_config = {"extra": "allow"}

class ProvocationMethods(BaseModel):
    """Provocation methods nested model"""
    techniques: Optional[List[str]] = []
    examples: Optional[List[str]] = []
    
    model_config = {"extra": "allow"}

class ConversationFlow(BaseModel):
    """Conversation flow nested model"""
    opening_moves: Optional[List[str]] = []
    closing_moves: Optional[List[str]] = []
    
    model_config = {"extra": "allow"}

class Fallbacks(BaseModel):
    """Fallbacks nested model"""
    when_unknown: Optional[List[str]] = []
    
    model_config = {"extra": "allow"}

class ConversationLogicData(BaseModel):
    """Nested conversation logic data structure"""
    primary_goal: Optional[str] = ""
    response_strategy: Optional[ResponseStrategy] = None
    tone_selection: Optional[ToneSelection] = None
    provocation_methods: Optional[ProvocationMethods] = None
    dynamic_response_templates: Optional[List[Dict[str, Any]]] = []  # Changed from List[str] to List[Dict]
    prohibited_patterns: Optional[List[str]] = []
    conversation_flow: Optional[ConversationFlow] = None
    fallbacks: Optional[Fallbacks] = None
    
    model_config = {"extra": "allow"}

class ConversationLogicMetadata(BaseModel):
    """Conversation logic metadata"""
    upload_timestamp: Optional[Any] = None  # Can be string or datetime
    last_updated: Optional[Any] = None      # Can be string or datetime
    source_file: Optional[str] = None
    tone_modes_count: Optional[int] = 0
    core_principles_count: Optional[int] = 0
    response_structure_steps: Optional[int] = 0
    provocation_techniques_count: Optional[int] = 0
    dynamic_templates_count: Optional[int] = 0
    prohibited_patterns_count: Optional[int] = 0
    
    model_config = {"extra": "allow"}

class ConversationLogic(BaseModel):
    """Conversation logic model matching standardized structure"""
    id: str = Field(..., alias="_id")
    filename: Optional[str] = None
    author: str
    category: Optional[str] = None
    conversation_logic: Optional[ConversationLogicData] = None
    metadata: Optional[ConversationLogicMetadata] = None
    
    # Legacy fields for backward compatibility
    response_patterns: Optional[Dict[str, Any]] = None
    topic_preferences: Optional[List[str]] = None
    argumentation_style: Optional[str] = None
    question_handling: Optional[Dict[str, str]] = None
    
    # For backward compatibility
    @property
    def philosopher(self) -> str:
        return self.author
    
    model_config = {
        "populate_by_name": True, 
        "arbitrary_types_allowed": True,
        "extra": "allow"
    }

class PhilosopherBot(BaseModel):
    """Philosopher bot configuration model"""
    id: str = Field(..., alias="_id")
    author: str  # Changed from philosopher to author
    bot_config: Optional[Dict[str, Any]] = None
    prompt_template: Optional[str] = None
    system_message: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    
    # For backward compatibility
    @property
    def philosopher(self) -> str:
        return self.author
    
    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

class ChatMessage(BaseModel):
    """Chat message model"""
    message: str = Field(..., min_length=1, description="User message")
    author: Optional[str] = Field(None, description="Target author for response")
    context: Optional[str] = Field(None, description="Additional context")
    
    # For backward compatibility
    @property
    def philosopher(self) -> Optional[str]:
        return self.author
    
    @philosopher.setter
    def philosopher(self, value: Optional[str]) -> None:
        self.author = value

class ChatResponse(BaseResponse): # should be BaseResponse?
    """Chat response model"""
    response: str
    author: str  # Changed from philosopher to author
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

# Persona Core models
class PersonaIdentity(BaseModel):
    """Persona identity model"""
    full_name: Optional[str] = None
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    nationality: Optional[str] = None
    roles: Optional[List[str]] = None

class PersonaBiography(BaseModel):
    """Persona biography model"""
    overview: Optional[str] = None
    historical_context: Optional[str] = None
    key_events: Optional[List[str]] = None
    personality_traits: Optional[List[str]] = None

class PersonaStyle(BaseModel):
    """Persona style model"""
    tone: Optional[str] = None
    speaking_style: Optional[str] = None
    pacing: Optional[str] = None
    thought_process: Optional[str] = None
    devices: Optional[List[str]] = None
    prohibited: Optional[List[str]] = None

class ModeOfResponse(BaseModel):
    """Mode of response model"""
    name: Optional[str] = None
    description: Optional[str] = None
    triggers: Optional[List[str]] = None
    example: Optional[str] = None

class ResponseLength(BaseModel):
    """Response length configuration model"""
    typical: Optional[str] = None
    maximum: Optional[str] = None

class PersonaInteractionRules(BaseModel):
    """Persona interaction rules model"""
    primary_goal: Optional[str] = None
    behavior: Optional[List[str]] = None
    response_length: Optional[ResponseLength] = None

class PersonaData(BaseModel):
    """Persona data model"""
    author: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    identity: Optional[PersonaIdentity] = None
    biography: Optional[PersonaBiography] = None
    core_principles: Optional[List[str]] = None
    style: Optional[PersonaStyle] = None
    modes_of_response: Optional[List[ModeOfResponse]] = None
    interaction_rules: Optional[PersonaInteractionRules] = None

class PersonaCoreMetadata(BaseModel):
    """Persona core metadata model"""
    upload_timestamp: Optional[str] = None
    last_updated: Optional[str] = None
    source_file: Optional[str] = None
    roles_count: Optional[int] = 0
    key_events_count: Optional[int] = 0
    personality_traits_count: Optional[int] = 0
    core_principles_count: Optional[int] = 0
    modes_of_response_count: Optional[int] = 0
    style_devices_count: Optional[int] = 0
    behavior_rules_count: Optional[int] = 0
    has_birth_date: Optional[bool] = False
    has_death_date: Optional[bool] = False
    has_primary_goal: Optional[bool] = False

class PersonaCore(BaseModel):
    """Persona core model matching MongoDB structure"""
    id: str = Field(..., alias="_id")
    filename: Optional[str] = None
    persona: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # For backward compatibility
    @property
    def author(self) -> str:
        if self.persona and "author" in self.persona:
            return self.persona["author"]
        return "Unknown"
    
    @property
    def philosopher(self) -> str:
        return self.author
    
    model_config = {
        "populate_by_name": True, 
        "arbitrary_types_allowed": True,
        "extra": "allow"
    }

class PersonaCoreResponse(BaseResponse):
    """Response model for persona core data"""
    data: Union[PersonaCore, List[PersonaCore]]
    total_count: Optional[int] = None

# Philosopher Bio models
class PhilosopherBio(BaseModel):
    """Philosopher biography model"""
    id: str = Field(..., alias="_id")
    author: str
    category: Optional[str] = None
    description: Optional[str] = None
    sections: Optional[Dict[str, Any]] = None
    
    model_config = {"populate_by_name": True}

class PhilosopherBioResponse(BaseResponse):
    """Response model for philosopher biography data"""
    data: Union[PhilosopherBio, List[PhilosopherBio]]
    total_count: Optional[int] = None

# Philosopher Summary models (for philosopher_summary collection)
class PhilosopherSummarySection(BaseModel):
    """Philosopher summary section model"""
    title: str
    content: str
    subsections: Optional[List[Dict[str, Any]]] = None

class PhilosopherSummaryDetailed(BaseModel):
    """Detailed philosopher summary model for philosopher_summary collection"""
    id: str = Field(..., alias="_id")
    filename: Optional[str] = None
    author: str
    category: Optional[str] = None
    title: Optional[str] = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    lifespan_years: Optional[int] = None
    nationality: Optional[str] = None
    description: Optional[str] = None
    sections: Optional[List[PhilosopherSummarySection]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = {"populate_by_name": True}

class PhilosopherSummaryDetailedResponse(BaseResponse):
    """Response model for detailed philosopher summary data"""
    data: Union[PhilosopherSummaryDetailed, List[PhilosopherSummaryDetailed]]
    total_count: Optional[int] = None

# Aliases for backward compatibility
TopTenIdeas = TopTenIdea  # Alias for import compatibility

# Philosophy Themes models
class PhilosophyThemeCoreIdea(BaseModel):
    """Core idea model for philosophy themes"""
    name: str
    summary: str
    discussion_hooks: List[str] = []

class PhilosophyThemePerspectivismFramework(BaseModel):
    """Perspectivism framework model for philosophy themes"""
    principle: str
    implications: List[str] = []
    example_prompts: List[str] = []

class PhilosophyThemeDiscussionTemplate(BaseModel):
    """Discussion template model for philosophy themes"""
    type: str
    pattern: str

class PhilosophyThemeData(BaseModel):
    """Philosophy theme data model"""
    core_ideas: List[PhilosophyThemeCoreIdea] = []
    perspectivism_framework: Optional[PhilosophyThemePerspectivismFramework] = None
    aphorisms: List[str] = []
    discussion_templates: List[PhilosophyThemeDiscussionTemplate] = []

class PhilosophyTheme(BaseModel):
    """Philosophy theme model"""
    id: str = Field(..., alias="_id")
    filename: Optional[str] = None
    author: str
    category: Optional[str] = None
    philosophy_and_themes: Optional[PhilosophyThemeData] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # For backward compatibility
    @property
    def philosopher(self) -> str:
        return self.author
    
    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

class PhilosophyThemeResponse(BaseResponse):
    """Response model for philosophy theme data"""
    data: Union[PhilosophyTheme, List[PhilosophyTheme]]
    total_count: Optional[int] = None

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
