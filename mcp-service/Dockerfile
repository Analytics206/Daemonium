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

# Default environment
ENV MCP_PORT=8080 \
    PYTHONUNBUFFERED=1

# Expose MCP (placeholder) port
EXPOSE 8080

# Placeholder command to keep container running until MCP server code is added
CMD ["sh", "-lc", "echo 'MCP container ready. Add your MCP server code and override CMD.' && sleep infinity"]
