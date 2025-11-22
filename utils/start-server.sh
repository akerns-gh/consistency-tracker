#!/bin/bash

# Start Local Server for True Lacrosse Consistency Tracker Prototype
# This script starts a simple HTTP server to run the prototype locally

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
PROTOTYPE_DIR="$PROJECT_ROOT/prototype"

# Default port
PORT=8000

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${BLUE}Port $PORT is already in use. Trying port 8001...${NC}"
    PORT=8001
fi

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}Starting local server with Python 3...${NC}"
    echo -e "${BLUE}Server running at: http://localhost:$PORT${NC}"
    echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
    echo ""
    cd "$PROTOTYPE_DIR" && python3 -m http.server $PORT
# Check if Python 2 is available
elif command -v python &> /dev/null; then
    echo -e "${GREEN}Starting local server with Python 2...${NC}"
    echo -e "${BLUE}Server running at: http://localhost:$PORT${NC}"
    echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
    echo ""
    cd "$PROTOTYPE_DIR" && python -m SimpleHTTPServer $PORT
# Check if Node.js http-server is available
elif command -v npx &> /dev/null; then
    echo -e "${GREEN}Starting local server with Node.js http-server...${NC}"
    echo -e "${BLUE}Server running at: http://localhost:$PORT${NC}"
    echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
    echo ""
    cd "$PROTOTYPE_DIR" && npx --yes http-server -p $PORT
# Check if PHP is available
elif command -v php &> /dev/null; then
    echo -e "${GREEN}Starting local server with PHP...${NC}"
    echo -e "${BLUE}Server running at: http://localhost:$PORT${NC}"
    echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
    echo ""
    cd "$PROTOTYPE_DIR" && php -S localhost:$PORT
else
    echo "Error: No suitable server found."
    echo "Please install one of the following:"
    echo "  - Python 3 (python3)"
    echo "  - Python 2 (python)"
    echo "  - Node.js (npx)"
    echo "  - PHP (php)"
    exit 1
fi

