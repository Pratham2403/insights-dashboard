# Sprinklr Insights Dashboard Server

This project implements a multi-agent system for generating insights dashboards based on user requirements through conversational AI. It's built using LangGraph for agent orchestration, LangChain for LLM integration, and FastAPI for the API layer.

## Project Overview

The Sprinklr Insights Dashboard helps users discover insights about products, brands, or services by analyzing social media and other online sources. It features:

- Conversational UI for collecting user requirements
- Multi-agent system for processing requirements and generating insights
- Boolean keyword query generation for data retrieval
- Theme extraction from search results
- Stateful conversation management

## Key Features

- **Human-in-the-Loop Verification**: Validates user data and generates contextual prompts for missing information
- **Intelligent Query Generation**: Converts user requirements into optimized Boolean keyword queries
- **Theme Extraction**: Processes search results to identify meaningful themes and insights
- **State Persistence**: Maintains conversation context across sessions
- **Modular Architecture**: Built with LangGraph for easy extensibility and maintenance

## System Architecture

The system is composed of three primary agents:

1. **HITL Verification Agent**: Verifies and collects user requirements through conversation
2. **Query Generation Agent**: Converts user requirements into Boolean keyword queries
3. **Data Processing Agent**: Processes search results and extracts meaningful themes

These agents are orchestrated using a LangGraph workflow that manages state transitions and ensures all required information is collected before proceeding.

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

### Prerequisites

- Python 3.9+
- OpenAI API Key (or compatible LLM provider)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/insights-dashboard.git
cd insights-dashboard/server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your API keys (see `.env.example` for a template).

### Running the Server

Start the server with:

```bash
./run_server.sh
```

The API will be available at `http://localhost:8000`.

## API Endpoints

- `POST /api/v1/chat`: Main conversation endpoint
- `GET /api/v1/conversations`: List all conversations
- `GET /api/v1/state/{conversation_id}`: Get the state of a specific conversation
- `DELETE /api/v1/state/{conversation_id}`: Delete a conversation state
- `POST /api/v1/mock-search`: Mock search endpoint for testing (when external API is unavailable)

## Example Conversation Flow

```
User: "I am the owner of Samsung and I want to know about the Customer Insights about my products."
Assistant: "What specific products are you looking for?"
User: "Generate for Samsung s25 ultra, s25plus"
Assistant: "What channels do you want to analyze? (Twitter, Facebook, etc.)"
User: "I want to know about the Twitter and Facebook channels."
Assistant: "What are your goals? (Brand Awareness, Customer Satisfaction, etc.)"
User: "I want to increase Brand Awareness and Customer Satisfaction."
Assistant: "What time period should we analyze?"
User: "I want to know about the last 6 months."
Assistant: "Any additional focus areas?"
User: "Yes, I want to focus on customer feedback and sentiment analysis."
Assistant: [Shows compiled data for confirmation]
User: "Yes, I am sure."
```

## Development

### Project Structure

```
insights-dashboard/
├── server/
│   ├── app/
│   │   ├── agents/             # Agent implementations
│   │   │   ├── hitl_verification_agent.py  # Human-in-the-Loop verification
│   │   │   ├── query_generation_agent.py   # Boolean query generation
│   │   │   └── data_processing_agent.py    # Theme extraction
│   │   ├── api/                # API endpoints
│   │   ├── config/             # Configuration settings
│   │   ├── models/             # Pydantic models
│   │   ├── tests/              # Test modules
│   │   ├── utils/              # Utility functions
│   │   ├── workflows/          # LangGraph workflows
│   │   └── main.py             # FastAPI application
│   ├── main.py                 # Entry point
│   └── requirements.txt        # Dependencies
```

### Testing

Run the test conversation script to verify the system works correctly:

```bash
python -m app.tests.test_conversation
```

For API tests:

```bash
python -m pytest app/tests/test_api.py -v
```

## Future Enhancements

- Integration with MongoDB for more robust state management
- Enhanced theme extraction with deep learning models
- Dashboard JSON generation for frontend visualization
- Authentication and user management
- Streaming responses for improved user experience

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project uses LangGraph for agent orchestration
- FastAPI for the web framework
- LangChain for LLM integration
