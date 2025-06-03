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

| Method | Path                             | Description                                       |
| ------ | -------------------------------- | ------------------------------------------------- |
| GET    | `/`                              | Service information (name, version, status)       |
| GET    | `/api/health`                    | Health check                                     |
| GET    | `/api/status`                    | Detailed service & workflow status               |
| POST   | `/api/analyze`                   | Submit a new natural-language query              |
| GET    | `/api/workflow/status/<thread_id>` | Retrieve status of an in-progress workflow      |
| POST   | `/api/themes/validate`           | Validate or reject generated themes              |
| POST   | `/api/respond`                  | Respond to pending HITL questions                 |

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

