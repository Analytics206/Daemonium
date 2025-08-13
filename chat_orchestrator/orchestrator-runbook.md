# Chat Orchestrator Runbook (Node.js)

The orchestrator aggregates data from the FastAPI backend, joins collections per author (and by `school_id` for schools), and publishes two Redis datasets for the chatbot.

- master_orchestrator: all philosophers (non-active often sparse by design)
- master_orchestrator_active: only `is_active_chat=1` philosophers (expected to be largely complete)

Optionally writes JSON snapshots for developer review.

## Prerequisites

- Docker + Docker Compose with the Daemonium stack running
- Healthy services: `backend`, `redis`, `mongodb`, `nodejs`
- Environment (provided via `docker-compose.yml` for the `nodejs` service):
  - FASTAPI_BASE_URL=http://backend:8000
  - FASTAPI_API_KEY (optional)
  - REDIS_URL=redis://:ch@ng3m300@redis:6379
  - MASTER_ORCHESTRATOR_TTL=0 (0 = no TTL)
  - ORCHESTRATOR_CONCURRENCY=6 (default)

## How to Run (Windows PowerShell)

Run inside the `nodejs` container. These commands do not require changing directories.

1) Run (writes datasets only to Redis):

```powershell
docker compose exec nodejs node /app/chat_orchestrator/master_combiner.js
```

2) Run and also write JSON snapshots:

```powershell
docker compose exec nodejs node /app/chat_orchestrator/master_combiner.js --write-json
```

3) Override concurrency just for this run (example: 8):

```powershell
docker compose exec nodejs sh -lc "ORCHESTRATOR_CONCURRENCY=8 node /app/chat_orchestrator/master_combiner.js --write-json"
```

## Outputs

- Redis keys:
  - master_orchestrator
  - master_orchestrator_active

- Optional JSON files (with `--write-json`):
  - /app/master_orchestrator.json
  - /app/master_orchestrator_active.json

## Quick Verification

Check JSON presence and sizes (if created):

```powershell
docker compose exec nodejs sh -lc "ls -lh /app/master_orchestrator*.json"
```

Summarize discussion_hook counts (active dataset):

```powershell
docker compose exec nodejs node -e "const fs=require('fs');const p='/app/master_orchestrator_active.json';if(!fs.existsSync(p)){console.log('missing');process.exit(0);}const d=JSON.parse(fs.readFileSync(p,'utf8'));const out=d.map(x=>({a:x.author||x.name||'UNKNOWN',h:Array.isArray(x.discussion_hook)?x.discussion_hook.length:0}));out.sort((a,b)=>b.h-a.h||a.a.localeCompare(b.a));console.log(out.slice(0,15));"
```

Check Redis keys and TTL values:

```powershell
docker compose exec redis redis-cli -a "ch@ng3m300" --no-auth-warning --scan --pattern "master_orchestrator*"
docker compose exec redis redis-cli -a "ch@ng3m300" --no-auth-warning TTL master_orchestrator
docker compose exec redis redis-cli -a "ch@ng3m300" --no-auth-warning TTL master_orchestrator_active
```

Delete keys to force a clean rebuild next run (optional):

```powershell
docker compose exec redis redis-cli -a "ch@ng3m300" --no-auth-warning DEL master_orchestrator master_orchestrator_active
```

## RedisInsight (Windows host)

- Host: localhost (or 127.0.0.1)
- Port: 6380 (host port mapped to container 6379)
- Username: leave blank (or "default" if UI requires)
- Password: ch@ng3m300 (or your REDIS_PASSWORD override)
- TLS: Off

URI example:

```
redis://:ch@ng3m300@localhost:6380
```

## Collections Joined

- Philosophers (base)
- Aphorisms
- Book Summary
- Bibliography (normalized to array)
- Conversation Logic
- Discussion Hook (strict author filtering; flattened; de-duplicated)
- Idea Summary
- Modern Adaptation
- Persona Core
- Philosopher Summary
- Philosophy Themes
- Top 10 Ideas (alias `top_ten_ideas` supported)
- Philosophy School (joined by `school_id`)
- Chat Blueprints (global dataset applied to each philosopher)

Note: Non-active philosophers may legitimately have empty arrays; verify completeness using the active dataset.

## Troubleshooting

- Empty arrays for non-active philosophers are expected by design.
- If Redis keys are missing, re-run with `--write-json` and inspect logs; ensure `backend` is healthy and reachable from `nodejs`.
- If FastAPI requires auth, set `FASTAPI_API_KEY` in `docker-compose.yml` or environment.
- RedisInsight errors on 6379 indicate you’re using the container port; use host port 6380.
