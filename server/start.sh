#!/bin/bash
# Sprinklr Dashboard Quick Start Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 Sprinklr Listening Dashboard${NC}"
echo -e "${BLUE}================================${NC}"

# Check if we're in the right directory
if [ ! -f "run.py" ]; then
    echo -e "${RED}❌ Error: run.py not found. Please run this script from the server directory.${NC}"
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 is required but not installed.${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created.${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install requirements if needed
if [ -f "requirements.txt" ]; then
    echo -e "${BLUE}📦 Installing requirements...${NC}"
    pip install -r requirements.txt > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Requirements installed.${NC}"
    else
        echo -e "${YELLOW}⚠️  Some packages may have failed to install. Check pip output above.${NC}" # Clarified message
    fi
fi

# Show available options - Simplified to only web server
echo -e "\n${BLUE}🚀 Choose an option:${NC}"
echo "1. 🌐 Web Server (Default)"
echo "2. ❓ Help"

read -p "Enter your choice (1-2, or press Enter for Web Server): " choice

case $choice in
    1|"")
        echo -e "${GREEN}🌐 Starting Web Server...${NC}"
        python3 run.py --web
        ;;
    2)
        echo -e "${GREEN}❓ Showing Help...${NC}"
        python3 run.py --help # run.py --help will show minimal help now
        ;;
    # Removed cases for Interactive, Demo, System Tests, System Status, Custom Query
    *)
        echo -e "${YELLOW}⚠️  Invalid choice. Please select 1 or 2.${NC}"
        ;;
esac

echo -e "\n${BLUE}👋 Thanks for using Sprinklr Dashboard!${NC}"
