
You are an expert Python developer specializing in multi-agent systems, LangGraph, and RAG implementations. Generate a complete, production-ready codebase for the first phase of a Sprinklr Insights dashboard project.

## PROJECT CONTEXT
Build the backend of agentic system that collects user requirements through conversational AI, generates Boolean keyword queries, and processes data for dashboard creation. The system uses LangGraph for agent orchestration, implements Human-in-the-Loop verification, and maintains persistent state across conversations.

## TECHNICAL SPECIFICATIONS

### Core Technologies:
- **LangGraph**: Multi-agent workflow orchestration
- **FastAPI**: Backend API framework
- **Elasticsearch**: Data source (queries in format: {"page":0,"size":100}) // here Just create a placeholder for the API
- **Pydantic**: Data validation and state management
- **OpenAI**: LLM integration

### Required Components:

## 1. STATE MANAGEMENT SYSTEM
Create a comprehensive state management system that tracks:
```py
class ProjectState(TypedDict):
    # User Requirements
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
    elasticsearch_queries: List[Dict[str, Any]]
    retrieved_data: List[Dict[str, Any]]
    processed_themes: List[Dict[str, Any]]
    
    # Conversation Flow
    messages: List[Dict[str, str]]
```

## 2. LANGGRAPH MULTI-AGENT SYSTEM
Implement three specialized agents:

### A. HITL Verification Agent
- Validates collected user data against required fields
- Generates contextual prompts for missing information
- Maintains conversation flow with intelligent follow-up questions
- Required fields: user_persona, products, channels, goals, time_period
- Must handle edge cases and ambiguous responses

### B. Query Generation Agent
- Converts user requirements into optimized Elasticsearch queries
- Generates multiple targeted queries rather than single broad queries
- Format: `{"page": 0, "size": 100, "keywords": [...], "filters": {...}}`
- Creates product-channel-goal combinations for comprehensive coverage
- Implements query optimization strategies

### C. Data Processing Agent
- Processes retrieved Elasticsearch results
- Implements theme extraction with relevance scoring
- Ranks and selects top 5-10 themes using weighted scoring algorithm
- Structures data for dashboard JSON generation
- Handles data deduplication and quality filtering

## 3. LANGGRAPH WORKFLOW IMPLEMENTATION
Create a stateful workflow with:
- Conditional edges based on state validation
- Memory persistence using MemorySaver
- Error handling and recovery mechanisms
- Conversation context preservation
- State transitions: START → HITL → Query Generation → Data Processing → END

## 4. FRONTEND CHAT INTERFACE (Alreay Implemented)
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
- `/elasticsearch/search` - Query execution
- `/themes/extract` - Data processing and theme extraction

## IMPLEMENTATION REQUIREMENTS

### Specific Implementation Details:

1. **State Persistence**: Use In-Memory or MongoDB or Some txt file for state persistence across conversations
3. **Query Generator Integration**: Create robust query builder with error handling (complying with the Contexts Provided)
4. **Theme Extraction**: Implement TF-IDF or semantic similarity for theme scoring and Use some sort of Scoring Algorithm to rank themes and select top 5-10 themes based on threshold determined by relevance and frequency
5. **Conversation Flow**: Smart question progression based on collected data gaps



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
5. **models/** - Pydantic state models
8. **config/** - Environment and settings management
9. **main.py** - Application entry point

## SUCCESS CRITERIA
The generated code must:
- Handle complete conversation flow from initial query to data confirmation
- Maintain state persistence across conversation sessions
- Do not create new Files as the structure is already defined
- Extract and rank meaningful themes from retrieved data
- Include comprehensive error handling and logging
- Support easy extension for additional agents and data sources

Generate production-ready, well-documented code that can be immediately deployed and tested.Include example usage scenarios.
