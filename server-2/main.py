# filepath: /Users/pratham.aggarwal/Documents/insights-dashboard/server/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from server.config.settings import settings
from server.models.project_state import ProjectState
from server.core.orchestration.langgraph_workflow import get_workflow_app, get_workflow_config
from server.api.schemas.agent_schemas import ChatMessageInput, ChatMessageOutput, ProjectStateOutput
from langchain_core.runnables import RunnableConfig # Import RunnableConfig


# In-memory storage for conversation states (replace with persistent storage in production)
conversation_states: Dict[str, Dict[str, Any]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic (e.g., initialize database connections, load models)
    print("Application startup...")
    yield
    # Shutdown logic (e.g., close database connections)
    print("Application shutdown.")

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

workflow = get_workflow_app() # This should be the compiled app

def get_current_state_summary(state_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts a summary of the project state for API responses."""
    return {
        "user_persona": state_data.get("user_persona"),
        "products": state_data.get("products"),
        "channels": state_data.get("channels"),
        "goals": state_data.get("goals"),
        "time_period": state_data.get("time_period"),
        "location": state_data.get("location"),
        "additional_notes": state_data.get("additional_notes"),
        "current_stage": state_data.get("current_stage"),
        "missing_fields": state_data.get("missing_fields"),
        "is_complete": state_data.get("is_complete"),
        "requires_human_input": state_data.get("requires_human_input"),
        "elasticsearch_queries_count": len(state_data.get("elasticsearch_queries", [])),
        "retrieved_data_count": len(state_data.get("retrieved_data", [])),
        "processed_themes_count": len(state_data.get("processed_themes", [])),
    }

@app.post(f"{settings.API_V1_STR}/chat", response_model=ChatMessageOutput)
async def chat_endpoint(payload: ChatMessageInput):
    conversation_id = payload.conversation_id
    
    if conversation_id and conversation_id in conversation_states:
        current_state_data = conversation_states[conversation_id]
    else:
        new_state = ProjectState()
        conversation_id = new_state.conversation_id
        current_state_data = new_state.model_dump() # Use model_dump for Pydantic v2+
        current_state_data["messages"] = []

    if payload.message:
        current_state_data["messages"].append({"role": "user", "content": payload.message})

    # Get the RunnableConfig for this conversation
    langgraph_config: RunnableConfig = get_workflow_config(conversation_id)

    updated_state_data = None
    try:
        # Use astream to get events, and look for the final state
        # The final state is usually the output of the last node before an END
        # or the state when the graph is waiting for human input.
        
        # Invoke the graph. The input should be a dictionary matching the GraphState.
        # LangGraph's `invoke` or `ainvoke` returns the final state of the graph run.
        final_graph_output = await workflow.ainvoke(current_state_data, config=langgraph_config)

        if isinstance(final_graph_output, dict):
            updated_state_data = final_graph_output
        elif hasattr(final_graph_output, 'model_dump'): # If it's a Pydantic model (like our GraphState)
            updated_state_data = final_graph_output.model_dump()
        else:
            # This case should ideally not happen if the graph is set up correctly
            # to output its state as a dictionary or Pydantic model.
            print(f"Warning: Unexpected output type from workflow: {type(final_graph_output)}")
            # Attempt to recover if possible, or fallback
            # For now, we'll assume it might be the state directly if not a dict
            # This part might need refinement based on exact graph output structure
            if final_graph_output: # if it's not None
                 updated_state_data = dict(final_graph_output) if not isinstance(final_graph_output, dict) else final_graph_output
            else:
                 updated_state_data = current_state_data # Fallback to current state if no output

    except Exception as e:
        print(f"Error invoking workflow for conversation {conversation_id}: {e}")
        error_message = f"An error occurred: {str(e)}"
        current_state_data["messages"].append({"role": "system", "content": error_message})
        current_state_data["requires_human_input"] = True 
        updated_state_data = current_state_data

    if not updated_state_data:
        # This should ideally be caught by the error handling above or indicate a more severe issue.
        raise HTTPException(status_code=500, detail="Workflow did not return a valid state.")

    conversation_states[conversation_id] = updated_state_data

    last_ai_message = "No AI response generated."
    if updated_state_data.get("messages"):
        ai_messages = [m['content'] for m in updated_state_data["messages"] if m['role'] == 'ai']
        if ai_messages:
            last_ai_message = ai_messages[-1]
    
    return ChatMessageOutput(
        conversation_id=conversation_id,
        response=last_ai_message,
        full_conversation=updated_state_data.get("messages", []),
        current_state_summary=get_current_state_summary(updated_state_data),
        requires_human_input=updated_state_data.get("requires_human_input", True)
    )

@app.get(f"{settings.API_V1_STR}/state/{{conversation_id}}", response_model=ProjectStateOutput)
async def get_conversation_state(conversation_id: str):
    if conversation_id not in conversation_states:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    state_data = conversation_states[conversation_id]
    try:
        # Validate and serialize with ProjectStateOutput
        # Pydantic models will ensure that the structure is correct.
        # If state_data is already a ProjectState model instance's dict, this will work.
        # If it's a raw dict, Pydantic will try to parse it.
        return ProjectStateOutput(**state_data)
    except Exception as e: 
        print(f"Error creating ProjectStateOutput from stored data for {conversation_id}: {e}")
        # This indicates a mismatch between stored state and output schema.
        raise HTTPException(status_code=500, detail=f"Error parsing state for conversation {conversation_id}")


@app.get(f"{settings.API_V1_STR}/active_conversations", response_model=List[str])
async def list_active_conversations():
    return list(conversation_states.keys())

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
