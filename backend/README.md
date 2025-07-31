# Daemonium FastAPI Backend

A comprehensive REST API for the Daemonium philosopher chatbot project, providing access to philosophical content stored in MongoDB.

## Features

- **RESTful API** with FastAPI framework
- **Async MongoDB integration** using Motor
- **Comprehensive endpoints** for all philosophical content
- **Automatic API documentation** with Swagger UI
- **CORS support** for frontend integration
- **Pydantic models** for data validation
- **Health checks** and monitoring endpoints
- **Search functionality** across all collections

## API Endpoints

### Core Endpoints
- `GET /` - API welcome message
- `GET /health` - Health check endpoint
- `GET /api/v1/stats` - Database and API statistics

### Philosophers
- `GET /api/v1/philosophers/` - Get all philosophers (paginated)
- `GET /api/v1/philosophers/{id}` - Get specific philosopher
- `GET /api/v1/philosophers/search/` - Search philosophers
- `GET /api/v1/philosophers/{id}/related` - Get related philosophers

### Books
- `GET /api/v1/books/` - Get all books (paginated, filterable by author)
- `GET /api/v1/books/{id}` - Get specific book
- `GET /api/v1/books/summaries/` - Get book summaries
- `GET /api/v1/books/by-author/{author}` - Get books by author
- `GET /api/v1/books/{id}/chapters` - Get book chapters

### Aphorisms
- `GET /api/v1/aphorisms/` - Get all aphorisms (paginated, filterable)
- `GET /api/v1/aphorisms/random` - Get random aphorisms
- `GET /api/v1/aphorisms/by-philosopher/{philosopher}` - Get aphorisms by philosopher
- `GET /api/v1/aphorisms/by-theme/{theme}` - Get aphorisms by theme
- `GET /api/v1/aphorisms/{id}` - Get specific aphorism

### Ideas
- `GET /api/v1/ideas/top-ten` - Get top ten philosophical ideas
- `GET /api/v1/ideas/summaries` - Get idea summaries
- `GET /api/v1/ideas/top-ten/{rank}` - Get idea by rank (1-10)
- `GET /api/v1/ideas/by-philosopher/{philosopher}` - Get ideas by philosopher
- `GET /api/v1/ideas/{id}` - Get specific idea

### Summaries
- `GET /api/v1/summaries/philosophy-themes` - Get philosophy themes
- `GET /api/v1/summaries/modern-adaptations` - Get modern adaptations
- `GET /api/v1/summaries/discussion-hooks` - Get discussion hooks
- `GET /api/v1/summaries/philosopher-bios` - Get philosopher biographies
- `GET /api/v1/summaries/persona-cores` - Get persona cores
- `GET /api/v1/summaries/by-collection/{collection}` - Get summaries by collection
- `GET /api/v1/summaries/search/{collection}` - Search within collection

### Chat
- `GET /api/v1/chat/blueprints` - Get chat blueprints
- `GET /api/v1/chat/conversation-logic` - Get conversation logic
- `GET /api/v1/chat/philosopher-bots` - Get bot configurations
- `GET /api/v1/chat/available-philosophers` - Get available philosophers
- `POST /api/v1/chat/message` - Send chat message (mock implementation)
- `GET /api/v1/chat/conversation-starters/{philosopher}` - Get conversation starters
- `GET /api/v1/chat/personality/{philosopher}` - Get philosopher personality

### Search
- `GET /api/v1/search/` - Global search across all collections
- `GET /api/v1/search/philosophers` - Search philosopher-related content
- `GET /api/v1/search/content` - Search content collections
- `GET /api/v1/search/suggestions` - Get search suggestions

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start MongoDB
Ensure your MongoDB Docker container is running:
```bash
docker-compose up mongodb -d
```

### 3. Run the API Server
```bash
# Option 1: Using the run script
python backend/run.py

# Option 2: Using uvicorn directly
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Option 3: Using Python module
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the API
- **API Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Configuration

The API automatically loads configuration from `config/default.yaml`:

```yaml
mongodb:
  host: localhost
  port: 27018
  database: daemonium
  username: admin
  password: ch@ng3m300

app:
  debug: false
  log_level: INFO
```

## Database Collections

The API provides access to these MongoDB collections:

- **aphorisms** - Philosophical aphorisms and quotes
- **book_summaries** - Summaries of philosophical books
- **books** - Full text of philosophical books
- **chat_blueprints** - Chatbot personality configurations
- **conversation_logic** - Conversation flow logic
- **discussion_hooks** - Discussion starter prompts
- **idea_summaries** - Summaries of philosophical ideas
- **modern_adaptations** - Modern applications of philosophy
- **persona_cores** - Core personality attributes
- **philosopher_bios** - Biographical information
- **philosopher_bots** - Bot configuration data
- **philosopher_summaries** - Philosopher overviews
- **philosophy_themes** - Thematic categorizations
- **top_ten_ideas** - Top philosophical concepts

## API Features

### Pagination
Most endpoints support pagination with `skip` and `limit` parameters:
```
GET /api/v1/philosophers/?skip=0&limit=10
```

### Filtering
Many endpoints support filtering by relevant fields:
```
GET /api/v1/books/?author=Nietzsche
GET /api/v1/aphorisms/?philosopher=Nietzsche
```

### Search
Comprehensive search functionality:
```
GET /api/v1/search/?query=existentialism&limit=20
GET /api/v1/search/suggestions?query=niet
```

### Response Format
All responses follow a consistent format:
```json
{
  "success": true,
  "data": [...],
  "total_count": 42,
  "message": "Retrieved 42 philosophers",
  "timestamp": "2025-07-31T12:00:00Z"
}
```

## Error Handling

The API provides detailed error responses:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Philosopher with ID 'unknown' not found"
  },
  "timestamp": "2025-07-31T12:00:00Z"
}
```

## Development

### Project Structure
```
backend/
├── __init__.py
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── database.py          # MongoDB connection and queries
├── models.py            # Pydantic data models
├── run.py              # Standalone runner script
├── README.md           # This file
└── routers/            # API route modules
    ├── __init__.py
    ├── philosophers.py  # Philosopher endpoints
    ├── books.py        # Book endpoints
    ├── aphorisms.py    # Aphorism endpoints
    ├── ideas.py        # Ideas endpoints
    ├── summaries.py    # Summary endpoints
    ├── chat.py         # Chat endpoints
    └── search.py       # Search endpoints
```

### Adding New Endpoints
1. Create or modify router files in `routers/`
2. Add router to `main.py`
3. Update models in `models.py` if needed
4. Add database methods in `database.py` if needed

### Testing
```bash
# Run health check
curl http://localhost:8000/health

# Test philosopher endpoint
curl http://localhost:8000/api/v1/philosophers/

# Test search
curl "http://localhost:8000/api/v1/search/?query=Nietzsche&limit=5"
```

## Integration with Frontend

This API is designed to work with React frontends. Key features for frontend integration:

- **CORS enabled** for cross-origin requests
- **Consistent JSON responses** with success/error indicators
- **Pagination support** for large datasets
- **Search suggestions** for autocomplete functionality
- **Mock chat endpoints** ready for LLM integration

## Future Enhancements

- **Authentication and authorization**
- **Rate limiting**
- **Caching with Redis**
- **Real LLM integration** for chat endpoints
- **Vector search integration** with Qdrant
- **WebSocket support** for real-time chat
- **API versioning**
- **Request/response logging**
- **Performance monitoring**

## Troubleshooting

### MongoDB Connection Issues
- Ensure MongoDB container is running: `docker-compose ps`
- Check MongoDB logs: `docker-compose logs mongodb`
- Verify connection string in config/default.yaml

### Import Errors
- Ensure you're running from the project root directory
- Check that all dependencies are installed: `pip install -r requirements.txt`

### Port Conflicts
- Change the port in `run.py` or use `--port` flag with uvicorn
- Default port is 8000, ensure it's not in use

For more help, check the FastAPI documentation at https://fastapi.tiangolo.com/
