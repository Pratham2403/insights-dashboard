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
        echo -e "${YELLOW}⚠️  Some packages may have failed to install.${NC}"
    fi
fi

# Show available options
echo -e "\n${BLUE}🚀 Choose an option:${NC}"
echo "1. 💬 Interactive Mode (Default)"
echo "2. 🎭 Demo Mode (Sample queries)"
echo "3. 🧪 System Tests"
echo "4. 🌐 Web Server"
echo "5. ⚙️  System Status"
echo "6. 🔍 Custom Query"
echo "7. ❓ Help"

read -p "Enter your choice (1-7, or press Enter for Interactive): " choice

case $choice in
    1|"")
        echo -e "${GREEN}🚀 Starting Interactive Mode...${NC}"
        python3 run.py
        ;;
    2)
        echo -e "${GREEN}🎭 Starting Demo Mode...${NC}"
        python3 run.py --demo
        ;;
    3)
        echo -e "${GREEN}🧪 Running System Tests...${NC}"
        python3 run.py --test
        ;;
    4)
        echo -e "${GREEN}🌐 Starting Web Server...${NC}"
        python3 run.py --web
        ;;
    5)
        echo -e "${GREEN}⚙️  Checking System Status...${NC}"
        python3 run.py --status
        ;;
    6)
        read -p "Enter your query: " query
        echo -e "${GREEN}🔍 Processing query: '$query'${NC}"
        python3 run.py --query "$query"
        ;;
    7)
        echo -e "${GREEN}❓ Showing Help...${NC}"
        python3 run.py --help
        ;;
    *)
        echo -e "${RED}❌ Invalid choice. Starting Interactive Mode...${NC}"
        python3 run.py
        ;;
esac

echo -e "\n${BLUE}👋 Thanks for using Sprinklr Dashboard!${NC}"
