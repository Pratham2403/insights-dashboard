# Sprinklr Dashboard - Terminal Scripts

This directory contains terminal scripts to easily run and test the Sprinklr Listening Dashboard.

## Quick Start

### Option 1: Use the interactive start script (Recommended)

```bash
./start.sh
```

This script will:

- Check dependencies
- Set up virtual environment if needed
- Install requirements
- Show a menu of options

### Option 2: Use the Python runner directly

```bash
python3 run.py
```

## Available Commands

### Interactive Mode (Default)

```bash
python3 run.py
# or
./start.sh
```

Starts an interactive CLI where you can enter queries and get real-time analysis.

### Single Query Mode

```bash
python3 run.py --query "Show me Samsung mentions on Twitter"
# or
python3 run.py -q "Analyze Apple brand sentiment"
```

### Demo Mode

```bash
python3 run.py --demo
# or
python3 run.py -d
```

Runs predefined sample queries to demonstrate functionality.

### System Tests

```bash
python3 run.py --test
# or
python3 run.py -t
```

Runs basic system validation tests.

### Web Server

```bash
python3 run.py --web
# or
python3 run.py -w
```

Starts the Flask web server for API access.

### System Status

```bash
python3 run.py --status
# or
python3 run.py -s
```

Shows current system status and configuration.

### Help

```bash
python3 run.py --help
```

## Web Server Options

Start web server on custom host/port:

```bash
python3 run.py --web --host 0.0.0.0 --port 8080
```

## Verbose Logging

Enable detailed logging for debugging:

```bash
python3 run.py --verbose
```

## Example Queries

Here are some example queries you can try:

### Brand Monitoring

- "Show me Samsung smartphone mentions in the last 30 days"
- "Analyze Apple brand sentiment on social media"
- "Tesla customer feedback and complaints"

### Channel-Specific Analysis

- "Twitter mentions of Nike this week"
- "Facebook posts about iPhone reviews"
- "Instagram content about luxury brands"

### Sentiment Analysis

- "Negative feedback about Microsoft products"
- "Positive reviews of Google services"
- "Customer satisfaction with Amazon delivery"

### Product Analysis

- "Customer complaints about delivery issues"
- "Product launch reactions for new iPhone"
- "Feature requests for software products"

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running from the server directory:

```bash
cd /path/to/insights-dashboard/server
python3 run.py
```

### Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

### Virtual Environment

Create and activate virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Logs

Check the log file for detailed error information:

```bash
tail -f sprinklr_dashboard.log
```

## Architecture

The terminal scripts interface with:

- **CLI Interface** (`src/main.py`) - Interactive terminal interface
- **Web API** (`app.py`) - Flask REST API
- **Workflow Engine** (`src/workflow.py`) - Core processing logic
- **Multi-Agent System** (`src/agents/`) - Specialized processing agents
- **RAG System** (`src/rag/`) - Vector database and retrieval
- **Tools** (`src/tools/`) - Data collection and processing tools

## Files

- `run.py` - Main Python runner script with all functionality
- `start.sh` - Interactive shell script for easy startup
- `src/main.py` - CLI application entry point
- `app.py` - Flask web server entry point

## Development

For development and debugging, use verbose mode:

```bash
python3 run.py --verbose --test
```

This will show detailed logs and help identify any configuration issues.
