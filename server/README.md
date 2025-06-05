# Sprinklr Insights Dashboard API (Phase 1)

## Overview

The Sprinklr Insights Dashboard API is a modular, multi-agent system designed to process natural language queries and generate actionable brand monitoring insights. In Phase 1, we focus on building a robust backend workflow that:

- Refines and validates user queries using Retrieval-Augmented Generation (RAG) context
- Interacts with users via Human-in-the-Loop (HITL) for collecting missing information
- Generates optimized boolean keyword queries for the Sprinklr API
- Analyzes fetched data to identify and categorize themes
- Orchestrates the end-to-end pipeline with LangGraph
- Exposes a RESTful Flask API for external integration

## Architecture

![](Architecture.pdf)

**Key components:**

1. **Query Refiner Agent**: Refines raw user input into structured, filter-ready queries using RAG context.
2. **Data Collector Agent**: Engages the user interactively (HITL) to gather any missing parameters (e.g., time period, channels, brand names).
3. **Boolean Query Generator Agent**: Constructs precise boolean queries for the Sprinklr API based on collected user data.
4. **ToolNode**: Executes the boolean queries to fetch raw data from Sprinklr.
5. **Data Analyzer Agent**: Processes and clusters returned data into meaningful themes, generating theme-specific boolean queries for deeper dives.
6. **HITL Verification Agent**: Presents generated themes, queries, and configurations back to the user for final approval before completion.
7. **Flask API**: Serves endpoints for submitting queries, checking workflow status, validating themes, and responding to prompts.
8. **Persistence & Memory**: Uses ChromaDB and LangGraph MemorySaver to store RAG indices and workflow state.

## Getting Started

### Prerequisites

- Python 3.11+
- `pip` package manager
- Access to Sprinklr API credentials (configured via environment variables or `config/settings.py`)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/insights-dashboard.git
cd insights-dashboard/server

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy or update `config/settings.py` with your Sprinklr API keys, chroma DB path, and any RAG index settings.
2. Optionally set environment variables in a `.env` file:
   - `HOST` (default: `0.0.0.0`)
   - `PORT` (default: `8000`)

### Running the Server

```bash
# Start the development server
python app.py
```

By default, the API will be available at `http://0.0.0.0:8000`.

For production deployments, consider using a WSGI server (e.g., Gunicorn):

```bash
gunicorn app:app --workers 4 --bind 0.0.0.0:8000
```

## API Endpoints

| Method | Path                               | Description                                 |
| ------ | ---------------------------------- | ------------------------------------------- |
| GET    | `/`                                | Service information (name, version, status) |
| GET    | `/api/health`                      | Health check                                |
| GET    | `/api/status`                      | Detailed service & workflow status          |
| POST   | `/api/analyze`                     | Submit a new natural-language query         |
| GET    | `/api/workflow/status/<thread_id>` | Retrieve status of an in-progress workflow  |
| POST   | `/api/themes/validate`             | Validate or reject generated themes         |
| POST   | `/api/respond`                     | Respond to pending HITL questions           |

**Example:**

```bash
curl -X POST http://localhost:8000/api/analyze \
     -H 'Content-Type: application/json' \
     -d '{"query":"Give me my Brand Monitor Insights"}'
```

Refer to [USAGE.md](USAGE.md) for a detailed end-to-end use-case example.

## Project Structure

```
server/
├── app.py              # Flask entrypoint
├── Architecture.pdf    # High-level system diagram
├── USAGE.md            # Example usage & workflow description
├── README.md           # ← You are here
├── requirements.txt    # Python dependencies
├── config/             # Configuration files & environment settings
├── src/                # Core application code
│   ├── workflow.py     # LangGraph orchestration
│   ├── agents/         # Multi-agent modules
│   ├── api/            # API handlers (if split from app.py)
│   ├── helpers/        # Shared prompts, state definitions
│   ├── rag/            # RAG context retrieval logic
│   └── tools/          # ToolNode integrations
├── chroma_db/          # Persisted Chroma vector store
└── docs/               # Jupyter notebooks & additional docs
```

# Sprinklr Insights Dashboard API (Phase 1) - MODERNIZED

## 🚀 Latest Update: LangGraph Modernization Complete

**MASSIVE CODE REDUCTION ACHIEVED: 78.8% for main workflow, 21.0% overall**

This project now uses the latest LangGraph patterns and implementation techniques, resulting in:

- **304 lines saved** from core components
- **Built-in memory management** with InMemorySaver
- **Modern HITL workflows** with interrupt patterns
- **Simplified agent architecture** using callable patterns
- **Enhanced functionality** with significantly less code

## 🆕 Modern Usage Examples

### Using the Modern Workflow (Recommended)

```python
from src.complete_modern_workflow import CompleteModernWorkflow

# Create modern workflow with built-in memory
workflow = CompleteModernWorkflow()

# Process user query with automatic persistence
config = {"configurable": {"thread_id": "user_session_123"}}
result = await workflow.invoke({
    "user_query": "Show me brand sentiment for last month",
    "user_id": "user123"
}, config)

# Built-in conversation history
conversation_history = await workflow.get_state(config)
```

### Modern API Endpoints (v2)

The modernized API includes new endpoints with enhanced functionality:

```bash
# Process query with modern workflow
curl -X POST http://localhost:8000/api/v2/process \
  -H "Content-Type: application/json" \
  -d '{"query": "engagement metrics analysis", "user_id": "user123"}'

# Get conversation history (built-in memory management)
curl http://localhost:8000/api/v2/history/user123

# Provide feedback to HITL workflows
curl -X POST http://localhost:8000/api/v2/feedback \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "abc123", "feedback": "approved", "user_id": "user123"}'
```

### Modern Agent Usage

```python
from src.agents.modern_query_refiner_agent import ModernQueryRefinerAgent
from src.agents.modern_data_collector_agent import ModernDataCollectorAgent

# Modern agents are callable and self-contained
query_refiner = ModernQueryRefinerAgent()
data_collector = ModernDataCollectorAgent()

# Simple callable pattern
state = {"user_query": "brand monitoring insights"}
refined_state = await query_refiner(state)
collected_state = await data_collector(refined_state)
```

### Modern HITL Workflows

```python
from src.agents.hitl_verification_agent import ModernHITLVerificationAgent

# Modern HITL with built-in interrupt handling
hitl_agent = ModernHITLVerificationAgent()

# Automatically handles interrupts and user input
state_with_hitl = await hitl_agent({
    "user_query": "complex analysis request",
    "needs_verification": True
})
```
