You are an expert Python developer specializing in multi-agent systems, LangGraph, and RAG implementations. Generate a complete codebase for the first phase of a Sprinklr Insights dashboard project.

## PROJECT CONTEXT

Build the backend of agentic system that collects user requirements through conversational AI, generates Boolean keyword queries, and processes data for dashboard creation. The system uses LangGraph for agent orchestration, implements Human-in-the-Loop verification, and maintains persistent state across conversations.

## TECHNICAL SPECIFICATIONS

### Core Technologies:

- **LangGraph**: Multi-agent workflow orchestration
- **FastAPI**: Backend API framework
- **Elasticsearch**: Data source (queries Data from some API, whose payload is the Boolean keyword query)
- **MemorySaver**: State persistence and memory management
- **TypedDict**: Type annotations for state management
- **Pydantic**: Data validation and state management
- **OpenAI**: LLM integration using the LLM Router.

  ```py
  LLM_ROUTER_BASE_URL: HttpUrl = Field(default=HttpUrl('http://qa6-intuitionx-llm-router-v2.sprinklr.com/chat-completion'))

  LLM_ROUTER_CLIENT_IDENTIFIER: str = Field(default='spr-backend-interns-25')
  ```

  ```
  Example LLM Router Usage:
  payload = {
      "messages": [
          {"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": "What is the weather like today?"}
      ],
      "model": "gpt-3.5-turbo",
      "client_identifier": LLM_ROUTER_CLIENT_IDENTIFIER
  }
  ```

### Required Components:

## 1. STATE MANAGEMENT SYSTEM

Create a comprehensive state management system that tracks:

```py
class ProjectState(TypedDict):
    # User Requirements
    ## Can be different for different users, so we can use Optional for some fields and there can be more fields as well because there may be different use-cases, so HITL should handle that
    user_persona: Optional[str]
    products: List[str]
    location: Optional[str]
    channels: List[str]
    goals: List[str]
    time_period: Optional[str]
    additional_notes: Optional[str]

    # System State
    conversation_id: str
    current_stage: str  # "collecting", "validating", "querying", "processing"
    missing_fields: List[str]
    is_complete: bool
    requires_human_input: bool

    # Data Processing
    retrieved_data: List[Dict[str, Any]]
    processed_themes: List[Dict[str, Any]]

    # Conversation Flow
    messages: List[Dict[str, str]]
```

## 2. LANGGRAPH MULTI-AGENT SYSTEM

Implement three specialized agents (Or Collection of Agents + Tools):

### A. HITL Verification Agent

- Validates collected user data against required fields
- Generates contextual prompts for missing information
- Maintains conversation flow with intelligent follow-up questions
- Must handle edge cases and ambiguous responses

### B. Query Generation Agent

- Converts user requirements into optimized and targeted Boolean keyword queries
- Uses LLM Router for query generation
- Generates multiple targeted queries batches rather than single broad queries
- Creates product-channel-goal combinations for comprehensive coverage
- Implements query optimization strategies

### C. Data Processing Agent

- Hit the API with the generated Boolean keyword queries to retrieve data.
- Processes retrieved data to extract meaningful themes
- Uses TF-IDF or semantic similarity for theme extraction
- Implements theme extraction with relevance scoring 
- Ranks and selects top 5-10 themes using weighted scoring algorithm
- Themes are basically a collection of keywords queries that are relevant to the user requirements
- Structures data for dashboard JSON generation
- Handles data deduplication and quality filtering

    ```json
    {
        "themes": [
            {
                "theme_name": "Samsung Brand Awareness",
                "keywords": ["Samsung", "S25 Ultra", "S25 Plus"],
                "relevance_score": 0.85
            },
            {
                "theme_name": "Customer Satisfaction",
                "keywords": ["feedback", "sentiment", "reviews"],
                "relevance_score": 0.90
            }
        ]
    }
    ```

## 3. LANGGRAPH WORKFLOW IMPLEMENTATION

Create a stateful workflow with:

- Conditional edges based on state validation
- Memory persistence using MemorySaver
- Error handling and recovery mechanisms
- Conversation context preservation
- State transitions: START → HITL → Query Generation → Data Processing → END . There should be a loop in the workflow where if the HITL agent finds missing fields, it should go back to the user to collect the missing fields and then continue with the Query Generation and Data Processing agents.

## 4. FRONTEND CHAT INTERFACE (Already Implemented)

Build a React-based interface featuring:

- Real-time chat conversation display
- Right-side state panel showing accumulated data
- Live updates as conversation progresses
- Confirmation dialog for final data review
- Session persistence and conversation history

## 5. BACKEND API SERVICES

Implement FastAPI endpoints for:

- `/chat` - Main conversation endpoint
- `/state/{conversation_id}` - State retrieval and updates
- `<SOME_RANDOM_EXTERNAL_API>` - Query Execution to Retrieve Data
- `/themes/extract` - Data processing and theme extraction

## IMPLEMENTATION REQUIREMENTS

### Specific Implementation Details:

1. **State Persistence**: Use In-Memory or MongoDB or Some txt file for state persistence across conversations
2. **Query Generator Integration**: Create robust query builder with error handling (complying with the Contexts Provided)
3. **Theme Extraction**: Implement TF-IDF or semantic similarity for theme scoring and Use some sort of Scoring Algorithm to rank themes and select top 5-10 themes based on threshold determined by relevance and frequency
4. **Conversation Flow**: Smart question progression based on collected data gaps

### Example Conversation Flow to Implement:

```
User: "I am the owner of Samsung and want customer insights"
AI: "What specific products are you looking for?"
User: "Samsung S25 Ultra, S25 Plus"
AI: "What channels do you want to analyze? (Twitter, Facebook, etc.)"
User: "Twitter and Facebook"
AI: "What are your goals? (Brand Awareness, Customer Satisfaction, etc.)"
User: "Increase Brand Awareness and Customer Satisfaction"
AI: "What time period should we analyze?"
User: "Last 6 months"
AI: "Any additional focus areas?"
User: "Customer feedback and sentiment analysis"
AI: [Shows compiled data for confirmation]
User: "Yes, proceed"
AI: [Triggers backend processing workflow]
```

## DELIVERABLES

Generate complete, executable code for:

1. **agents/** - All agent needed for this phase are implemented
2. **langgraph_workflow.py** - Complete LangGraph setup (or atleast for this phase)
3. **api/** - FastAPI backend services
4. **models/** - Pydantic state models
5. **config/** - Environment and settings management
6. **main.py** - Application entry point

## SUCCESS CRITERIA

The generated code must:

- Handle complete conversation flow from initial query to data confirmation
- Maintain state persistence across conversation sessions
- Extract and rank meaningful themes from retrieved data
- Include comprehensive error handling and logging (using some inbuilt logging library)
- Support easy extension for additional agents and data sources

Generate production-ready, well-documented code that can be immediately deployed and tested. Include example usage scenarios.
