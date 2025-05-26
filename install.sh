#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting UIBench installation...${NC}"

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo ${python_version}
if (( $(echo "$python_version < 3.6" | bc -l) )); then
    echo -e "${RED}Error: Python 3.8 or higher is required${NC}"
    exit 1
fi

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -e .

# Install Playwright browsers
echo -e "${YELLOW}Installing Playwright browsers...${NC}"
playwright install

# Download spaCy model
echo -e "${YELLOW}Downloading spaCy model...${NC}"
python -m spacy download en_core_web_lg

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

echo -e "${GREEN}Installation completed successfully!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update the .env file with your configuration"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Start the backend: uvicorn backend.main:app --reload" 