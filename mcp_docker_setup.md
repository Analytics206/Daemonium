--add docker container for mcp service for models calls
--docker will support different models services: openai, anthropic, ollama local, cloud models
--do not change any existing model use in any code, we are just setting up docker for mcp service
--do not work on anything else, stay focused on mcp docker setup
--add persistant store for mcp service container
--use naming convenstion already used in docker-compose.yml
--do not write any other code besides creating docker container for mcp service and update docker-compose.yml

# example of add dockerfile to docker-compose.yml
FROM python:3.11-slim

## Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

## Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP service code
COPY src/ /app/src/
COPY config/ /app/config/

WORKDIR /app

# Expose MCP service port
EXPOSE 8080

CMD ["python", "-m", "src.mcp_server"]

# add to requirements.txt if needed
## MCP Protocol
mcp>=1.0.0

## Model APIs
openai>=1.0.0
anthropic>=0.25.0
requests>=2.31.0

## Local Ollama
ollama>=0.1.0

## Context retrieval (connect to your existing services)
redis>=5.0.0
qdrant-client>=1.7.0

## Web framework for MCP service
fastapi>=0.104.0
uvicorn>=0.24.0

## Async support
aiohttp>=3.9.0
asyncio-mqtt>=0.13.0
