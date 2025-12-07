#!/bin/bash

# Deployment script for Consistency Tracker Infrastructure
# Sets up Python virtual environment and runs deploy.py

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AWS_DIR="$SCRIPT_DIR"
VENV_PATH="$AWS_DIR/.venv"

echo -e "${BLUE}🚀 Consistency Tracker Infrastructure Deployment${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}❌ Python 3 is required but not found.${NC}"
    echo "Please install Python 3.9 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${YELLOW}❌ Python 3.9+ required. Found: Python $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python version: $(python3 --version)${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${BLUE}🐍 Creating Python virtual environment...${NC}"
    cd "$AWS_DIR"
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔌 Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Check if requirements.txt exists
if [ ! -f "$AWS_DIR/requirements.txt" ]; then
    echo -e "${YELLOW}❌ requirements.txt not found in $AWS_DIR${NC}"
    exit 1
fi

# Install/upgrade dependencies
echo -e "${BLUE}📦 Installing/updating Python dependencies...${NC}"
pip install --quiet --upgrade pip
pip install --quiet -r "$AWS_DIR/requirements.txt"
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Change to aws directory
cd "$AWS_DIR"

# Run deploy.py
echo ""
echo -e "${BLUE}🚀 Starting deployment...${NC}"
echo ""
python3 deploy.py

# Capture exit code
EXIT_CODE=$?

# Deactivate virtual environment
deactivate

# Exit with the same code as deploy.py
exit $EXIT_CODE

