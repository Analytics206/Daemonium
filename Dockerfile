# Use the official Python 3.11 image as the base
FROM python:3.11-slim

# Update packages and apply security fixes
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv (fast dependency manager)
RUN pip install --no-cache-dir uv

# Copy only dependency files first for better caching
COPY pyproject.toml .
COPY setup.py .

# Install Python dependencies (cached unless these files change)
RUN uv pip install --system -e .

# Copy project files
COPY . .

# Set environment variables for Python (optional, but recommended)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Command to run the application
CMD ["python", "main.py"]