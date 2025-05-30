"""
LangGraph workflow for the Sprinklr Insights Dashboard application.
"""
from typing import Dict, List, Any, TypedDict, Annotated, Literal, Optional
import asyncio
from datetime import datetime
from uuid import uuid4
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from app.agents.hitl_verification_agent import HITLVerificationAgent
from app.agents.query_generation_agent import QueryGenerationAgent
from app.agents.data_processing_agent import DataProcessingAgent
from app.models.state import ProjectState, UserRequirements
from app.utils.state_manager import get_state_manager


logger = logging.getLogger(__name__)


# Initialize agents
hitl_agent = HITLVerificationAgent()
query_agent = QueryGenerationAgent()
data_agent = DataProcessingAgent()
state_manager = get_state_manager()


async def process_user_input(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process user input through the HITL verification agent.
    
    Args:
        state: The current state of the conversation, expected to contain 'user_input'.
        
    Returns:
        Updated state.
    """
    logger.info(f"process_user_input called with state keys: {list(state.keys())}")
    
    # Extract user input from the latest message if not already set
    user_input = state.get("user_input")
    if user_input is None and "messages" in state and state["messages"]:
        # Get the last human message
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'content') and hasattr(msg, '__class__') and 'HumanMessage' in str(msg.__class__):
                user_input = msg.content
                state["user_input"] = user_input
                break
    
    if user_input is None:
        logger.info("No user_input found in state. Returning current state without processing.")
        # Don't mark as completed, just return the current state
        return state

    logger.info(f"Processing user input: {user_input}")
    
    # Process user input through HITL agent
    result = await hitl_agent.process_input(state, user_input)
    
    # Clear user_input after processing to prevent reprocessing
    if "user_input" in result:
        del result["user_input"]
    
    return result


async def generate_queries(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Boolean keyword queries based on user requirements.
    
    Args:
        state: The current state of the conversation.
        
    Returns:
        Updated state with generated queries.
    """
    # Generate queries
    return await query_agent.generate_queries(state)


async def process_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process search results and extract themes.
    
    Args:
        state: The current state of the conversation.
        
    Returns:
        Updated state with extracted themes.
    """
    # Process data
    return await data_agent.process_data(state)


def should_collect_more_requirements(state: Dict[str, Any]) -> Literal["collect_requirements", "generate_queries", "__end__"]:
    """
    Determine if more requirements should be collected or if the workflow should proceed to query generation.
    
    Args:
        state: The current state of the conversation.
        
    Returns:
        Next step in the workflow.
    """
    # Check if workflow is completed
    if state.get("workflow_completed", False):
        return "__end__"
    
    # Check if all required fields are filled
    if state.get("all_requirements_collected", False):
        return "generate_queries"
    else:
        # If we just processed user input, we should end this workflow run
        # and wait for the next message to start a new run
        return "__end__"


def should_generate_dashboard(state: Dict[str, Any]) -> Literal["dashboard_confirmation", "__end__"]:
    """
    Determine if the workflow should proceed to dashboard confirmation.
    
    Args:
        state: The current state of the conversation.
        
    Returns:
        Next step in the workflow.
    """
    # Check if themes have been extracted
    if state.get("themes") and len(state.get("themes", [])) > 0:
        return "dashboard_confirmation"
    else:
        return "__end__"


async def confirm_dashboard(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Confirm the dashboard generation with the user.
    
    Args:
        state: The current state of the conversation.
        
    Returns:
        Updated state.
    """
    # Add confirmation message
    if "messages" not in state:
        state["messages"] = []
    
    # Extract key data for confirmation
    user_req = state.get("user_requirements", {})
    theme_count = len(state.get("themes", []))
    
    # Construct confirmation message
    confirmation_msg = f"""
I've analyzed data for the following requirements:

Products: {', '.join(user_req.get('products', []))}
Channels: {', '.join(user_req.get('channels', []))}
Goals: {', '.join(user_req.get('goals', []))}
Time Period: {user_req.get('time_period', 'Not specified')}

I've identified {theme_count} key themes from the data. Would you like to proceed with generating the dashboard?
    """
    
    state["messages"].append({
        "role": "assistant",
        "content": confirmation_msg
    })
    
    # Update current step
    state["current_step"] = "DASHBOARD_CONFIRMATION"
    
    return state


def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for the Sprinklr Insights Dashboard.
    
    Returns:
        StateGraph: The workflow graph.
    """
    # Define the workflow as a state graph
    workflow = StateGraph(ProjectState)
    
    # Add nodes to the graph
    workflow.add_node("collect_requirements", process_user_input)
    workflow.add_node("generate_queries", generate_queries)
    workflow.add_node("process_data", process_data)
    workflow.add_node("dashboard_confirmation", confirm_dashboard)
    
    # Define edges in the graph
    # From collect_requirements, either collect more or generate queries
    workflow.add_conditional_edges(
        "collect_requirements",
        should_collect_more_requirements,
        {
            "collect_requirements": "collect_requirements",
            "generate_queries": "generate_queries",
            "__end__": END
        }
    )
    
    # From generate_queries, always proceed to process_data
    workflow.add_edge("generate_queries", "process_data")
    
    # From process_data, either proceed to dashboard_confirmation or end
    workflow.add_conditional_edges(
        "process_data",
        should_generate_dashboard,
        {
            "dashboard_confirmation": "dashboard_confirmation",
            "__end__": END
        }
    )
    
    # From dashboard_confirmation, end the workflow
    workflow.add_edge("dashboard_confirmation", END)
    
    # Set the entry point
    workflow.set_entry_point("collect_requirements")
    
    return workflow


async def create_or_load_conversation(conversation_id: Optional[str] = None) -> tuple:
    """
    Create a new conversation or load an existing one.
    
    Args:
        conversation_id: The ID of the conversation to load. If None, a new conversation is created.
        
    Returns:
        Tuple of (conversation_id, app).
    """
    # Create memory saver
    memory = MemorySaver()
    
    # Create workflow
    workflow = create_workflow()
    
    # Create the compiled workflow
    app = workflow.compile(checkpointer=memory)
    
    # If no conversation_id provided, create a new one
    if not conversation_id:
        conversation_id = str(uuid4())
        
        # Initialize state
        initial_state = {
            "conversation_id": conversation_id,
            "messages": [],
            "user_requirements": UserRequirements().dict(),
            "current_step": "START",
            "last_updated": datetime.now().isoformat()
        }
        
        # Save initial state
        await state_manager.save_state(conversation_id, initial_state)
    else:
        # Load existing state
        existing_state = await state_manager.get_state(conversation_id)
        
        if not existing_state:
            # If no state found, create a new conversation
            conversation_id = str(uuid4())
            
            # Initialize state with proper LangGraph message structure
            initial_state = {
                "conversation_id": conversation_id,
                "messages": [],  # This will be handled by add_messages annotation
                "user_requirements": UserRequirements().dict(),
                "current_step": "START",
                "last_updated": datetime.now().isoformat(),
                "all_requirements_collected": False,
                "workflow_completed": False
            }
            
            # Save initial state
            await state_manager.save_state(conversation_id, initial_state)
    
    return conversation_id, app


async def process_message(conversation_id: str, message: str) -> Dict[str, Any]:
    """
    Process a user message in a conversation.
    
    Args:
        conversation_id: The ID of the conversation.
        message: The user message.
        
    Returns:
        Updated state.
    """
    logger.info(f"Processing message for conversation {conversation_id}: {message}")
    
    # Create or load conversation
    conv_id, app = await create_or_load_conversation(conversation_id)
    
    # Get current state
    current_state = await state_manager.get_state(conv_id)
    if not current_state:
        # If no state found, create a new conversation
        conv_id, app = await create_or_load_conversation()
        current_state = await state_manager.get_state(conv_id)
    
    logger.info(f"Current state keys: {list(current_state.keys())}")
    
    # Initialize messages if not present
    if "messages" not in current_state:
        current_state["messages"] = []
    
    # Convert old dict messages to LangGraph messages if needed
    langraph_messages = []
    for msg in current_state.get("messages", []):
        if isinstance(msg, BaseMessage):
            # Already a LangGraph message
            langraph_messages.append(msg)
        elif isinstance(msg, dict):
            # Convert dict to LangGraph message
            if msg.get("role") == "user" or msg.get("type") == "human":
                langraph_messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant" or msg.get("type") == "ai":
                langraph_messages.append(AIMessage(content=msg["content"]))
            elif msg.get("role") == "system" or msg.get("type") == "system":
                langraph_messages.append(SystemMessage(content=msg["content"]))
            else:
                # Fallback for unknown format
                langraph_messages.append(HumanMessage(content=str(msg.get("content", msg))))
        else:
            # Handle other formats gracefully
            langraph_messages.append(HumanMessage(content=str(msg)))

    # Add new user message
    langraph_messages.append(HumanMessage(content=message))
    
    # Create a new state dict for the workflow with LangGraph messages
    workflow_state = current_state.copy()
    workflow_state["messages"] = langraph_messages
    workflow_state["user_input"] = message
    
    logger.info(f"Workflow state keys before ainvoke: {list(workflow_state.keys())}")
    
    # Run the workflow with recursion limit
    config = {
        "configurable": {"thread_id": conv_id},
        "recursion_limit": 10  # Set a reasonable recursion limit
    }
    
    try:
        result = await app.ainvoke(workflow_state, config)
        logger.info(f"Workflow result keys: {list(result.keys())}")
    except Exception as e:
        logger.error(f"Error in workflow execution: {e}")
        # Add error message to state
        current_state["messages"].append({
            "role": "assistant",
            "content": "I encountered an error processing your request. Please try again.",
            "timestamp": datetime.now().isoformat()
        })
        result = current_state
    
    # Save updated state
    await state_manager.save_state(conv_id, result)
    
    return {"conversation_id": conv_id, "state": result}
