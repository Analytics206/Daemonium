# Backend API Routers - MongoDB Collections Reference

This document provides a comprehensive mapping of which MongoDB collections each API endpoint uses in the Daemonium philosopher chatbot project.

## Overview

The FastAPI backend consists of 8 router modules that provide REST API endpoints for accessing philosophical content stored in MongoDB. Each router is responsible for specific types of content and uses one or more MongoDB collections.

## Router-to-Collection Mapping

### 1. Aphorisms Router (`aphorisms.py`)
**Primary Collection:** `aphorisms`

| Endpoint | HTTP Method | Collections Used | Description |
|----------|-------------|------------------|-------------|
| `/api/v1/aphorisms/` | GET | `aphorisms` | Get all aphorisms with pagination and optional philosopher filter |
| `/api/v1/aphorisms/random` | GET | `aphorisms` | Get random selection of aphorisms |
| `/api/v1/aphorisms/by-philosopher/{philosopher}` | GET | `aphorisms` | Get aphorisms by specific philosopher |
| `/api/v1/aphorisms/by-theme/{theme}` | GET | `aphorisms` | Search aphorisms by theme in text/context |
| `/api/v1/aphorisms/{aphorism_id}` | GET | `aphorisms` | Get specific aphorism by ID |

### 2. Books Router (`books.py`)
**Primary Collections:** `books`, `book_summary`

| Endpoint | HTTP Method | Collections Used | Description |
|----------|-------------|------------------|-------------|
| `/api/v1/books/` | GET | `books` | Get all books with pagination |
| `/api/v1/books/summaries` | GET | `book_summary` | Get all book summaries |
| `/api/v1/books/by-author/{author}` | GET | `books` | Get books by specific author |
| `/api/v1/books/{book_id}` | GET | `books` | Get specific book by ID |
| `/api/v1/books/{book_id}/chapters` | GET | `books` | Get chapters from specific book |
| `/api/v1/books/summaries/{summary_id}` | GET | `book_summary` | Get specific book summary by ID |

### 3. Chat Router (`chat.py`)
**Primary Collections:** `chat_blueprint`, `conversation_logic`, `philosopher_bot`, `persona_core`

| Endpoint | HTTP Method | Collections Used | Description |
|----------|-------------|------------------|-------------|
| `/api/v1/chat/blueprints` | GET | `chat_blueprint` | Get chat blueprints for philosophers |
| `/api/v1/chat/conversation-logic` | GET | `conversation_logic` | Get conversation logic patterns |
| `/api/v1/chat/philosopher-bots` | GET | `philosopher_bot` | Get philosopher bot configurations |
| `/api/v1/chat/available-philosophers` | GET | `chat_blueprint`, `philosopher_bot`, `conversation_logic` | Get list of available philosophers for chat |
| `/api/v1/chat/personality/{philosopher}` | GET | `chat_blueprint`, `conversation_logic`, `persona_core` | Get personality profile for specific philosopher |
| `/api/v1/chat/conversation-starters/{philosopher}` | GET | `chat_blueprint` | Get conversation starters for specific philosopher |

### 4. Ideas Router (`ideas.py`)
**Primary Collections:** `top_10_ideas`, `idea_summary`

| Endpoint | HTTP Method | Collections Used | Description |
|----------|-------------|------------------|-------------|
| `/api/v1/ideas/top-ten` | GET | `top_10_ideas` | Get top 10 philosophical ideas |
| `/api/v1/ideas/summaries` | GET | `idea_summary` | Get all idea summaries |
| `/api/v1/ideas/top-ten/{rank}` | GET | `top_10_ideas` | Get top idea by rank (1-10) |
| `/api/v1/ideas/by-philosopher/{philosopher}` | GET | `top_10_ideas`, `idea_summary` | Get ideas by specific philosopher |
| `/api/v1/ideas/{idea_id}` | GET | `top_10_ideas`, `idea_summary` | Get specific idea by ID |

### 5. Philosophers Router (`philosophers.py`)
**Primary Collections:** `philosophers`, `philosophy_schools`, `aphorisms`, `book_summary`, `top_10_ideas`, `idea_summary`, `philosophy_themes`, `philosopher_summary`

| Endpoint | HTTP Method | Collections Used | Description |
|----------|-------------|------------------|-------------|
| `/api/v1/philosophers/` | GET | `philosophers` | Get all philosophers with pagination |
| `/api/v1/philosophers/{philosopher_id}` | GET | `philosophers` | Get specific philosopher by ID |
| `/api/v1/philosophers/{philosopher_name}/with-school` | GET | `philosophers`, `philosophy_schools` | Get philosopher with associated school information |
| `/api/v1/philosophers/search/` | GET | `philosophers` | Search philosophers by name/content |
| `/api/v1/philosophers/{philosopher_id}/related` | GET | `philosophers`, `philosophy_schools` | Get related philosophers by school and name similarity |
| `/api/v1/philosophers/by-author/{author}` | GET | `philosophers`, `aphorisms`, `book_summary`, `top_10_ideas`, `idea_summary`, `philosophy_themes`, `philosopher_summary` | Get comprehensive author profile with all related content |

### 6. Philosophy Schools Router (`philosophy_schools.py`)
**Primary Collections:** `philosophy_schools`, `philosophers`

| Endpoint | HTTP Method | Collections Used | Description |
|----------|-------------|------------------|-------------|
| `/api/v1/philosophy-schools/` | GET | `philosophy_schools` | Get all philosophy schools with pagination |
| `/api/v1/philosophy-schools/{school_id}` | GET | `philosophy_schools` | Get specific philosophy school by ID |
| `/api/v1/philosophy-schools/search/` | GET | `philosophy_schools` | Search philosophy schools by name/category/content |
| `/api/v1/philosophy-schools/{school_id}/philosophers` | GET | `philosophy_schools`, `philosophers` | Get philosophers belonging to specific school |

### 7. Search Router (`search.py`)
**Primary Collections:** All collections (global search)

| Endpoint | HTTP Method | Collections Used | Description |
|----------|-------------|------------------|-------------|
| `/api/v1/search/global` | GET | All collections | Global search across all content types |
| `/api/v1/search/suggestions` | GET | `philosophers`, `books`, `top_10_ideas` | Get search suggestions for autocomplete |
| `/api/v1/search/philosophers` | GET | `philosophers` | Search specifically in philosophers collection |
| `/api/v1/search/books` | GET | `books` | Search specifically in books collection |
| `/api/v1/search/ideas` | GET | `top_10_ideas` | Search specifically in ideas collection |

**Note:** Global search can target specific collections using the `collections` query parameter.

### 8. Summaries Router (`summaries.py`)
**Primary Collections:** `philosophy_themes`, `modern_adaptation`, `discussion_hook`, `philosopher_bio`, `persona_core`

| Endpoint | HTTP Method | Collections Used | Description |
|----------|-------------|------------------|-------------|
| `/api/v1/summaries/philosophy-themes` | GET | `philosophy_themes` | Get philosophy themes |
| `/api/v1/summaries/modern-adaptations` | GET | `modern_adaptation` | Get modern adaptations of philosophical concepts |
| `/api/v1/summaries/discussion-hooks` | GET | `discussion_hook` | Get discussion hooks for philosophical topics |
| `/api/v1/summaries/philosopher-bios` | GET | `philosopher_bio` | Get philosopher biographies |
| `/api/v1/summaries/by-collection/{collection_name}` | GET | Dynamic (based on parameter) | Get summaries from specified collection |
| `/api/v1/summaries/persona-cores` | GET | `persona_core` | Get persona core data for philosophers |
| `/api/v1/summaries/by-collection/{collection_name}/search` | GET | Dynamic (based on parameter) | Search within specified collection |

## MongoDB Collections Overview

The following collections are available in the MongoDB database:

| Collection Name | Purpose | Primary Use Cases |
|-----------------|---------|-------------------|
| `aphorisms` | Philosophical aphorisms and quotes | Aphorisms router, cross-collection queries |
| `book_summary` | Summaries of philosophical books | Books router, philosopher content aggregation |
| `books` | Full philosophical texts and chapters | Books router, search functionality |
| `chat_blueprint` | Chat conversation templates | Chat router, personality profiles |
| `conversation_logic` | Conversation flow logic | Chat router, bot behavior |
| `discussion_hook` | Discussion starters and hooks | Summaries router |
| `idea_summary` | Individual philosophical idea summaries | Ideas router, content aggregation |
| `modern_adaptation` | Modern applications of philosophy | Summaries router |
| `persona_core` | Core personality data for philosophers | Chat router, summaries router |
| `philosopher_bio` | Biographical information | Summaries router |
| `philosopher_bot` | Bot configuration data | Chat router |
| `philosopher_summary` | Comprehensive philosopher summaries | Cross-collection queries |
| `philosophers` | Main philosopher data | Philosophers router, relationships |
| `philosophy_schools` | Philosophical schools and movements | Philosophy schools router, relationships |
| `philosophy_themes` | Thematic philosophical content | Summaries router, content aggregation |
| `top_10_ideas` | Top 10 philosophical ideas by philosopher | Ideas router, search functionality |

## Key Design Patterns

### 1. Cross-Collection Queries
Some endpoints aggregate data from multiple collections:
- **Philosopher by Author**: Combines data from 7 collections for comprehensive profiles
- **Available Philosophers**: Aggregates from 3 chat-related collections
- **Global Search**: Searches across all collections simultaneously

### 2. Relationship Handling
- **Philosophers ↔ Philosophy Schools**: Joined via `school_id` field
- **Author-based Relationships**: Multiple collections linked by `author` field
- **Content Hierarchies**: Books contain chapters, ideas have summaries

### 3. Search Strategies
- **Direct Collection Access**: Most endpoints query single collections
- **Multi-field Search**: Search across multiple fields within collections
- **Aggregation Pipelines**: Complex queries combining multiple collections

## Usage Notes

1. **Field Mapping**: Most collections use `author` as the primary joining field
2. **ObjectId Handling**: All endpoints properly convert MongoDB ObjectIds to strings
3. **Pagination**: Most list endpoints support `skip` and `limit` parameters
4. **Filtering**: Many endpoints support additional filters (e.g., `is_active_chat`)
5. **Error Handling**: All endpoints include comprehensive error handling and logging

## Development Guidelines

When adding new endpoints:
1. Follow the existing pattern of database method calls
2. Ensure proper ObjectId to string conversion
3. Add appropriate error handling and logging
4. Update this documentation with new collection mappings
5. Consider cross-collection relationships for comprehensive data retrieval
