#!/bin/bash
# Production Deployment Script for Sprinklr Insights Dashboard

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Script header
echo "🚀 SPRINKLR INSIGHTS DASHBOARD - PRODUCTION DEPLOYMENT"
echo "===================================================="
echo

# Check if we're in the right directory
if [ ! -f "production_app.py" ]; then
    print_error "production_app.py not found. Please run this script from the server directory."
    exit 1
fi

# Check for virtual environment
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Check Python version
python_version=$(python --version 2>&1)
print_status "Using Python: $python_version"

# Install/upgrade requirements
if [ -f "requirements.txt" ]; then
    print_status "Installing/updating requirements..."
    pip install -r requirements.txt > /dev/null 2>&1
    print_success "Requirements installed"
else
    print_warning "requirements.txt not found. Installing basic dependencies..."
    pip install flask flask-cors langchain langgraph > /dev/null 2>&1
fi

# Run validation tests
print_status "Running production validation tests..."
if python -c "
import sys
sys.path.append('./src')
try:
    from complete_modern_workflow import get_available_workflows
    from production_config import ProductionConfig
    print('✅ Basic imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"; then
    print_success "Validation tests passed"
else
    print_error "Validation tests failed"
    exit 1
fi

# Check configuration
print_status "Checking configuration..."
export FLASK_HOST=${FLASK_HOST:-"0.0.0.0"}
export FLASK_PORT=${FLASK_PORT:-"8000"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

echo "  Host: $FLASK_HOST"
echo "  Port: $FLASK_PORT"
echo "  Log Level: $LOG_LEVEL"

# Check if port is available
if command -v netstat >/dev/null 2>&1; then
    if netstat -tuln | grep ":$FLASK_PORT " > /dev/null; then
        print_warning "Port $FLASK_PORT appears to be in use"
    fi
fi

# Create log directory if needed
mkdir -p logs

# Function to start the server
start_server() {
    print_status "Starting Sprinklr Insights Dashboard..."
    echo
    echo "🌐 Server will be available at: http://$FLASK_HOST:$FLASK_PORT"
    echo "📊 Health check: http://$FLASK_HOST:$FLASK_PORT/api/health"
    echo "📈 Status: http://$FLASK_HOST:$FLASK_PORT/api/v2/status"
    echo
    echo "Press Ctrl+C to stop the server"
    echo

    # Start the production app
    python production_app.py
}

# Function to run in background
start_background() {
    print_status "Starting server in background..."
    nohup python production_app.py > logs/server.log 2>&1 &
    server_pid=$!
    echo $server_pid > server.pid
    print_success "Server started in background (PID: $server_pid)"
    echo "  View logs: tail -f logs/server.log"
    echo "  Stop server: kill $server_pid"
}

# Function to stop background server
stop_server() {
    if [ -f "server.pid" ]; then
        server_pid=$(cat server.pid)
        if kill $server_pid 2>/dev/null; then
            print_success "Server stopped (PID: $server_pid)"
            rm server.pid
        else
            print_warning "Could not stop server with PID: $server_pid"
        fi
    else
        print_warning "No server.pid file found"
    fi
}

# Function to show status
show_status() {
    if [ -f "server.pid" ]; then
        server_pid=$(cat server.pid)
        if kill -0 $server_pid 2>/dev/null; then
            print_success "Server is running (PID: $server_pid)"
            echo "  Health check: curl http://$FLASK_HOST:$FLASK_PORT/api/health"
        else
            print_error "Server PID file exists but process is not running"
        fi
    else
        print_status "No server instance found"
    fi
}

# Parse command line arguments
case "${1:-start}" in
    "start")
        start_server
        ;;
    "background"|"bg")
        start_background
        ;;
    "stop")
        stop_server
        ;;
    "restart")
        stop_server
        sleep 2
        start_background
        ;;
    "status")
        show_status
        ;;
    "test")
        print_status "Running comprehensive tests..."
        python final_production_validation.py
        ;;
    "health")
        print_status "Checking health..."
        curl -s http://$FLASK_HOST:$FLASK_PORT/api/health | python -m json.tool || echo "Server not responding"
        ;;
    *)
        echo "Usage: $0 {start|background|stop|restart|status|test|health}"
        echo
        echo "Commands:"
        echo "  start      - Start server in foreground (default)"
        echo "  background - Start server in background"
        echo "  stop       - Stop background server"
        echo "  restart    - Restart background server"
        echo "  status     - Show server status"
        echo "  test       - Run validation tests"
        echo "  health     - Check server health"
        exit 1
        ;;
esac
