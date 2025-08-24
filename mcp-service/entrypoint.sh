#!/usr/bin/env sh
# Daemonium MCP service entrypoint
# Dynamically launches Ollama or OpenAI MCP servers based on env vars

set -e

log() {
  printf "[mcp-entrypoint] %s\n" "$1"
}

run_ollama() {
  log "Starting Ollama MCP server (python /app/mcp_server.py)"
  exec python /app/mcp_server.py
}

run_openai() {
  if [ -z "${OPENAI_API_KEY:-}" ]; then
    log "OPENAI_API_KEY is not set; falling back to Ollama MCP server"
    run_ollama
    return
  fi
  # Defaults if not provided
  export OPENAI_MODEL="${OPENAI_MODEL:-${OPENAI_MODEL_GENERAL_KG:-gpt-4o-mini}}"
  export OPENAI_TIMEOUT="${OPENAI_TIMEOUT:-60}"
  log "Starting OpenAI MCP server (model=$OPENAI_MODEL, timeout=$OPENAI_TIMEOUT)"
  exec python /app/mcp_server_openai.py
}

run_selected() {
  server="${MCP_SERVER:-ollama}"
  case "$server" in
    openai|OPENAI)
      run_openai
      ;;
    ollama|OLLAMA)
      run_ollama
      ;;
    *)
      log "Unknown MCP_SERVER='$server'; defaulting to Ollama"
      run_ollama
      ;;
  esac
}

# Optional auto-run guard for stdio servers. By default, keep the container idle so clients can docker exec.
if [ "${MCP_AUTORUN:-0}" = "1" ] || [ "${MCP_AUTORUN:-false}" = "true" ]; then
  log "MCP_AUTORUN enabled"
  run_selected
else
  log "MCP_AUTORUN disabled; container is idle. To start a server now:"
  log "  docker exec -i daemonium-mcp /app/entrypoint.sh    # uses MCP_SERVER (default: ollama)"
  log "  docker exec -i --env MCP_SERVER=openai daemonium-mcp /app/entrypoint.sh"
  exec sh -c 'sleep infinity'
fi
