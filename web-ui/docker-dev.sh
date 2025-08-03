#!/bin/bash

# Daemonium Web UI - Docker Development Script
# This script helps with Docker development workflow

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Daemonium Web UI - Docker Development${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    print_error "package.json not found. Please run this script from the web-ui directory."
    exit 1
fi

# Parse command line arguments
COMMAND=${1:-"help"}

case $COMMAND in
    "build")
        print_status "Building Docker image for web-ui..."
        docker build -t daemonium-web-ui:latest .
        print_status "✅ Docker image built successfully!"
        ;;
    
    "dev")
        print_status "Starting development environment..."
        # Go to parent directory to run docker-compose
        cd ..
        docker-compose up web-ui --build
        ;;
    
    "start")
        print_status "Starting web-ui service..."
        cd ..
        docker-compose up web-ui -d
        print_status "✅ Web UI started at http://localhost:3000"
        ;;
    
    "stop")
        print_status "Stopping web-ui service..."
        cd ..
        docker-compose stop web-ui
        print_status "✅ Web UI stopped"
        ;;
    
    "logs")
        print_status "Showing web-ui logs..."
        cd ..
        docker-compose logs -f web-ui
        ;;
    
    "shell")
        print_status "Opening shell in web-ui container..."
        cd ..
        docker-compose exec web-ui /bin/sh
        ;;
    
    "clean")
        print_status "Cleaning up Docker resources..."
        docker system prune -f
        print_status "✅ Docker cleanup completed"
        ;;
    
    "full")
        print_status "Starting full Daemonium stack..."
        cd ..
        docker-compose up --build
        ;;
    
    "help"|*)
        echo -e "${GREEN}Daemonium Web UI - Docker Development Commands${NC}"
        echo ""
        echo "Usage: ./docker-dev.sh [command]"
        echo ""
        echo "Commands:"
        echo "  build    - Build the Docker image"
        echo "  dev      - Start development with live reload"
        echo "  start    - Start web-ui service in background"
        echo "  stop     - Stop web-ui service"
        echo "  logs     - Show web-ui logs"
        echo "  shell    - Open shell in web-ui container"
        echo "  clean    - Clean up Docker resources"
        echo "  full     - Start full Daemonium stack"
        echo "  help     - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./docker-dev.sh build"
        echo "  ./docker-dev.sh dev"
        echo "  ./docker-dev.sh logs"
        ;;
esac
