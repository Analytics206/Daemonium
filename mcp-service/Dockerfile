FROM python:3.11-slim

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set workdir and create common folders
WORKDIR /app
RUN mkdir -p /app/data /app/config

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy MCP service source code into the image
COPY . /app/
# Ensure entrypoint has LF endings and is executable (avoid sh parse errors on CRLF)
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Default environment
ENV MCP_PORT=8080 \
    PYTHONUNBUFFERED=1 \
    MCP_SERVER=ollama \
    MCP_AUTORUN=0

# Expose MCP (placeholder) port
EXPOSE 8080

# Use dynamic entrypoint to select MCP server (Ollama/OpenAI)
ENTRYPOINT ["/app/entrypoint.sh"]
