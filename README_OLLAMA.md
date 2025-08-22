# Ollama Docker (GPU) — Daemonium

This guide shows how to run the Ollama container with GPU support, manage models, and test via CLI and HTTP. It matches the docker-compose service `ollama` and uses a persistent volume at `./docker_volumes/ollama_data`.

## Prerequisites
- Docker Desktop with WSL2 integration enabled
- NVIDIA GPU drivers on Windows
- NVIDIA Container Toolkit installed in WSL2 (user confirmed)
- Docker Compose that supports profiles (or use COMPOSE_PROFILES fallback)

## Start/Stop the Ollama service

- Create persistence folder (first time only):
```powershell
New-Item -ItemType Directory -Force -Path .\docker_volumes\ollama_data | Out-Null
```

- Start the Ollama service:
```powershell
docker compose --profile ollama up -d ollama
```

- Stop the Ollama service:
```powershell
docker compose --profile ollama down ollama
or
docker compose stop ollama
```

- Remove the Ollama service:
```powershell
docker compose --profile ollama rm ollama
```

- Start the Ollama service with COMPOSE_PROFILES:
```powershell
$env:COMPOSE_PROFILES = "ollama"; docker compose up -d ollama
```

- Test the Ollama service:
```powershell
Invoke-WebRequest http://localhost:11434/api/tags | Select-Object -ExpandProperty Content
```

- Restart the Ollama service:
```powershell
docker compose restart ollama
```

- Pull a model:
```powershell
docker exec -it daemonium-ollama ollama pull llama3.1:latest
docker exec -it daemonium-ollama ollama pull deepseek-r1:latest
docker exec -it daemonium-ollama ollama pull deepseek-r1:14b
docker exec -it daemonium-ollama ollama pull granite-embedding:278m
docker exec -it daemonium-ollama ollama pull llama3.2:latest
docker exec -it daemonium-ollama ollama pull mxbai-embed-large:latest
docker exec -it daemonium-ollama ollama pull snowflake-arctic-embed2:latest
docker exec -it daemonium-ollama ollama pull gpt-oss:20b
docker exec -it daemonium-ollama ollama pull gemma3:12b

docker exec -it daemonium-ollama ollama pull gte-large:latest
docker exec -it daemonium-ollama ollama pull all-minilm:latest
docker exec -it daemonium-ollama ollama pull all-minilm:l6-v2:latest
docker exec -it daemonium-ollama ollama pull gte-large:latest
docker exec -it daemonium-ollama ollama pull all-minilm:latest
docker exec -it daemonium-ollama ollama pull all-minilm:l6-v2:latest
docker exec -it daemonium-ollama ollama pull gte-large:latest
docker exec -it daemonium-ollama ollama pull all-minilm:latest
docker exec -it daemonium-ollama ollama pull all-minilm:l6-v2:latest
```

- List models:
```powershell
docker exec -it daemonium-ollama ollama list
```

- Run a model:
```powershell
docker exec -it daemonium-ollama ollama run llama3.1:latest "Hello, how are you?"
```

- Remove a model:
```powershell
docker exec -it daemonium-ollama ollama remove llama3.1:latest
```

- Remove all models:
```powershell
docker exec -it daemonium-ollama ollama remove --all
```

- Remove the Ollama service:
```powershell
docker compose --profile ollama rm ollama
```

- Remove the Ollama service with COMPOSE_PROFILES:
```powershell
$env:COMPOSE_PROFILES = "ollama"; docker compose rm ollama
```

- Run a model:
```powershell
docker exec daemonium-ollama ollama run llama3.1:latest "Say hello from Ollama in Docker."
docker exec daemonium-ollama ollama run gpt-oss:20b "Say hello from Ollama in Docker."
```

$body = @{
  model  = "llama3.1:latest"
  prompt = "Write one sentence about Stoicism."
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:11434/api/generate" -Body $body -ContentType "application/json"

Invoke-RestMethod -Method Post -Uri "http://localhost:11434/api/generate" -Body $body -ContentType "application/json" | Select-Object -ExpandProperty response


Invoke-RestMethod -Method Get -Uri "http://localhost:11434/api/tags" | Select-Object -ExpandProperty Content

Invoke-RestMethod -Method Get -Uri "http://localhost:11434/api/tags" | Select-Object -ExpandProperty Content | ConvertFrom-Json

# Check GPU usage
docker exec -it daemonium-ollama nvidia-smi

# Check logs
docker logs daemonium-ollama --since 5m | Select-String -Pattern "CUDA|cuBLAS|GPU|NVIDIA"

# Check health
docker inspect daemonium-ollama | Select-Object -ExpandProperty State | Select-Object -ExpandProperty Health

# Check stats
docker stats daemonium-ollama

# Check stats for all containers
docker stats

# Check stats for all containers with more details
docker stats --no-trunc

# Check stats for all containers with more details and more columns
docker stats --no-trunc --format "table {{.Name}}\t{{.ID}}\t{{.Image}}\t{{.CPUs}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}\t{{.PIDs}}\t{{.Status}}"

# Check stats for all containers with more details and more columns and more columns
docker stats --no-trunc --format "table {{.Name}}\t{{.ID}}\t{{.Image}}\t{{.CPUs}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}\t{{.PIDs}}\t{{.Status}}\t{{.Ports}}"

# Start the Ollama service with COMPOSE_PROFILES
$env:COMPOSE_PROFILES = "ollama"; docker compose up -d ollama

