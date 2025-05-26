#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting UIBench installation...${NC}"

# Check Python version
python_version=$(python3 -c 'import sys; print("".join(map(str, sys.version_info[:2])))')
if [ "$python_version" -lt "38" ]; then
    echo -e "${RED}Error: Python 3.8 or higher is required${NC}"
    exit 1
fi

# Ensure the virtual environment is activated
if [ -d "venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
fi

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}Installing dependencies from requirements.txt...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo -e "${RED}Error: requirements.txt not found!${NC}"
    exit 1
fi

# Install Playwright browsers
if command -v playwright &> /dev/null; then
    echo -e "${YELLOW}Installing Playwright browsers...${NC}"
    playwright install
else
    echo -e "${RED}Error: Playwright is not installed!${NC}"
    exit 1
fi

# Ensure uvicorn is installed
if ! pip show uvicorn &> /dev/null; then
    echo -e "${YELLOW}Installing uvicorn...${NC}"
    pip install uvicorn
fi

# Download spaCy models
if ! python -m spacy validate | grep -q "en_core_web_lg"; then
    echo -e "${YELLOW}Downloading spaCy model en_core_web_lg...${NC}"
    python -m spacy download en_core_web_lg
fi

if ! python -m spacy validate | grep -q "en_core_web_sm"; then
    echo -e "${YELLOW}Downloading spaCy model en_core_web_sm...${NC}"
    python -m spacy download en_core_web_sm
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please update the .env file with your configuration${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p cache

# Ensure the virtual environment is activated before running uvicorn
if [ -d "venv" ]; then
    echo -e "${YELLOW}Activating virtual environment for running uvicorn...${NC}"
    source venv/bin/activate
else
    echo -e "${RED}Error: Virtual environment not found! Please run the installation script first.${NC}"
    exit 1
fi

# Final message
echo -e "${GREEN}Installation completed successfully!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update the .env file with your configuration"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Start the backend: uvicorn backend.main:app --reload"

source venv/bin/activate