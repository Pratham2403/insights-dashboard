"""
LangGraph Workflow Implementation for Sprinklr Insights Dashboard.

This module defines the stateful graph that orchestrates the agents:
1. HITL Verification Agent: Collects and validates user requirements.
2. Query Generation Agent: Generates Elasticsearch queries from validated requirements.
3. Data Processing Agent: Processes data retrieved from Elasticsearch to extract themes.

The workflow uses conditional edges based on the state validation and persists
memory using an in-memory `MemorySaver` (can be replaced with persistent storage).
"""
from typing import Dict, Any, TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver # Using in-memory for this example
from langgraph.graph.state import CompiledStateGraph # For type hinting config
from langchain_core.runnables import RunnableConfig

from server.models.project_state import ProjectState
from server.agents.hitl.verification_agent import HITLVerificationAgent
from server.agents.query_generation.query_builder_agent import QueryGenerationAgent
from server.agents.data_processing.data_processor_agent import DataProcessingAgent
from server.config.settings import settings
from server.services.llm_providers.custom_llm_router import CustomChatLLM # Import CustomChatLLM

# Initialize LLMs with CustomChatLLM
llm_default = CustomChatLLM(
    model_name=settings.DEFAULT_LLM_MODEL,
    temperature=0 # Temperature can be set here or managed by router if preferred
    # base_url and client_identifier are taken from settings by default in CustomChatLLM
)
llm_query_gen = CustomChatLLM(
    model_name=settings.QUERY_GENERATION_LLM_MODEL,
    temperature=0
)
llm_data_proc = CustomChatLLM(
    model_name=settings.DATA_PROCESSING_LLM_MODEL,
    temperature=0.1
)

# Initialize Agents
hitl_agent = HITLVerificationAgent(llm=llm_default)
query_gen_agent = QueryGenerationAgent(llm=llm_query_gen)
data_proc_agent = DataProcessingAgent(llm=llm_data_proc, top_n_themes=7)

# Define the State for the graph
# Using Pydantic model directly with LangGraph is now supported and preferred for complex states.
# For TypedDict approach, ensure all fields are correctly annotated.
class GraphState(ProjectState):
    pass # Inherits all fields from ProjectState

# Agent Nodes - functions that will be called by LangGraph
async def run_hitl_verification(state: GraphState) -> GraphState:
    """Node to run the HITL Verification Agent."""
    # print("--- Running HITL Verification ---")
    updated_state_dict = await hitl_agent.invoke(state)
    return GraphState(**updated_state_dict.model_dump())

async def run_query_generation(state: GraphState) -> GraphState:
    """Node to run the Query Generation Agent."""
    # print("--- Running Query Generation ---")
    updated_state_dict = await query_gen_agent.invoke(state)
    return GraphState(**updated_state_dict.model_dump())

async def run_data_processing(state: GraphState) -> GraphState:
    """
    Node to run the Data Processing Agent.
    This node simulates fetching data from Elasticsearch before processing.
    In a real scenario, this node or a preceding one would handle ES calls.
    """
    # print("--- Running Data Processing ---")
    # Simulate Elasticsearch data retrieval if queries exist and no data yet
    if state.elasticsearch_queries and not state.retrieved_data:
        # print(f"Simulating Elasticsearch call for {len(state.elasticsearch_queries)} queries.")
        # Placeholder: Replace with actual Elasticsearch client call
        # For now, create some dummy data based on queries
        dummy_data = []
        for i, query in enumerate(state.elasticsearch_queries):
            keywords = query.get("keywords", ["generic"])
            dummy_data.append({"id": f"doc_{i+1}", "text": f"Simulated document about {', '.join(keywords)}.", "query_source": query})
            if i > 5: # Limit dummy data
                break
        state.retrieved_data = dummy_data
        state.messages.append({"role": "system", "content": f"Simulated retrieval of {len(dummy_data)} documents from Elasticsearch."})
    
    updated_state_dict = await data_proc_agent.invoke(state)
    return GraphState(**updated_state_dict.model_dump())

# Conditional Edges
def should_continue_to_query_generation(state: GraphState) -> str:
    """
    Determines the next step after HITL verification.
    - If requirements are complete and validated: move to Query Generation.
    - If requirements are not complete: loop back to HITL (implicitly, by requiring human input).
    - If HITL determines it needs more user input, it should set `requires_human_input = True`.
    """
    # print(f"--- डिबगिंग HITL स्थिति: पूर्ण? {state.is_complete}, मानव इनपुट की आवश्यकता है? {state.requires_human_input} ---")
    if state.current_stage == "validating" and state.is_complete and not state.requires_human_input:
        # print("--- Condition: HITL complete, proceeding to Query Generation ---")
        return "query_generation"
    elif state.requires_human_input:
        # print("--- Condition: HITL requires more input, ending current flow for user interaction ---")
        # This signifies the graph should wait for the next user message before reinvoking.
        # The 'END' here means the current invocation of the graph is done, awaiting external input.
        return END # Or a specific node indicating waiting for user
    else:
        # print("--- Condition: HITL not complete but not requiring input (should not happen often), ending. ---")
        # This case should ideally be handled within the HITL agent or represent an error/loop.
        return END 

def should_continue_to_data_processing(state: GraphState) -> str:
    """
    Determines the next step after Query Generation.
    - If queries are generated: move to Data Processing.
    - If no queries (e.g., error or no basis for queries): end or handle error.
    """
    if state.current_stage == "querying" and state.elasticsearch_queries:
        # print("--- Condition: Queries generated, proceeding to Data Processing ---")
        return "data_processing"
    else:
        # print("--- Condition: No queries generated or error, ending flow. ---")
        # Could also go to an error handling node.
        state.messages.append({"role": "system", "content": "Query generation did not produce queries. Ending workflow."})
        return END

# Define the Workflow Graph
workflow = StateGraph(GraphState)

# Add nodes to the graph
workflow.add_node("hitl_verification", run_hitl_verification)
workflow.add_node("query_generation", run_query_generation)
workflow.add_node("data_processing", run_data_processing)

# Set the entry point
workflow.set_entry_point("hitl_verification")

# Add conditional edges
workflow.add_conditional_edges(
    "hitl_verification",
    should_continue_to_query_generation,
    {
        "query_generation": "query_generation",
        END: END # If HITL needs more input or decides to end
    }
)

workflow.add_conditional_edges(
    "query_generation",
    should_continue_to_data_processing,
    {
        "data_processing": "data_processing",
        END: END # If query generation fails or no queries
    }
)

# Data processing is the last step in this phase, so it goes to END
workflow.add_edge("data_processing", END)

# Compile the graph with memory
# MemorySaver allows persisting the state of the graph across calls for a given conversation_id.
# For production, replace MemorySaver with a persistent checkpoint like Redis, Postgres, etc.
memory = MemorySaver()
compiled_app = workflow.compile(checkpointer=memory) # Renamed to avoid conflict

def get_workflow_app() -> CompiledStateGraph: # More specific type hint
    """Returns the compiled LangGraph application."""
    return compiled_app

def get_workflow_config(conversation_id: str) -> RunnableConfig:
    """Returns the config dictionary for invoking the LangGraph app, specific to a conversation."""
    return RunnableConfig(configurable={"thread_id": conversation_id})

# --- Example Usage (for testing the workflow directly) ---
async def run_example_conversation():
    print("--- Starting Example Conversation Flow ---")
    
    config: RunnableConfig = get_workflow_config("example_convo_123") # Use the helper, ensure type

    # Initial state for a new conversation
    # Pass messages directly, other fields will use Pydantic defaults
    initial_graph_state = GraphState(
        messages=[{"role": "user", "content": "I am the owner of Samsung and want customer insights"}]
    )

    print(f"\\n--- Invocation 1: User\'s first message ---")
    current_graph_run = await compiled_app.ainvoke(initial_graph_state.model_dump(), config=config) 
    
    current_state = GraphState(**current_graph_run) 
    print(f"AI Response: {current_state.messages[-1]['content']}")
    print(f"Current Stage: {current_state.current_stage}, Requires Input: {current_state.requires_human_input}")

    # Simulate user providing more information based on AI's question
    if current_state.requires_human_input and current_state.messages[-1]["role"] == "ai":
        user_response_2 = "Samsung S25 Ultra, S25 Plus"
        print(f"\\n--- Invocation 2: User responds with products: \'{user_response_2}\' ---")
        
        current_messages = current_state.messages.copy()
        current_messages.append({"role": "user", "content": user_response_2})
        
        next_invoke_input = current_state.model_dump()
        next_invoke_input["messages"] = current_messages
        
        current_graph_run = await compiled_app.ainvoke(next_invoke_input, config=config) 
        current_state = GraphState(**current_graph_run)
        print(f"AI Response: {current_state.messages[-1]['content']}")
        print(f"Current Stage: {current_state.current_stage}, Missing Fields: {current_state.missing_fields}")

    print("\\n--- Simulating filling all required fields to trigger full flow ---")
    final_input_state_dict = {
        "user_persona": "Samsung Owner",
        "products": ["Samsung S25 Ultra", "S25 Plus"],
        "channels": ["Twitter", "Facebook"],
        "goals": ["Increase Brand Awareness", "Customer Satisfaction"],
        "time_period": "Last 6 months",
        "additional_notes": "Focus on customer feedback and sentiment analysis.",
        "messages": [
            {"role": "user", "content": "I am the owner of Samsung and want customer insights"},
            {"role": "ai", "content": "What specific products are you looking for?"}, 
            {"role": "user", "content": "Samsung S25 Ultra, S25 Plus"},
            {"role": "ai", "content": "What channels do you want to analyze? (Twitter, Facebook, etc.)"}, 
            {"role": "user", "content": "Twitter and Facebook"},
            {"role": "ai", "content": "What are your goals? (Brand Awareness, Customer Satisfaction, etc.)"}, 
            {"role": "user", "content": "Increase Brand Awareness and Customer Satisfaction"},
            {"role": "ai", "content": "What time period should we analyze?"}, 
            {"role": "user", "content": "Last 6 months"},
            {"role": "ai", "content": "Any additional focus areas?"}, 
            {"role": "user", "content": "Customer feedback and sentiment analysis"}
        ],
        "conversation_id": "example_convo_123", 
        "is_complete": False, 
        "requires_human_input": True 
    }
        
    print(f"\\n--- Invocation with all data ---")
    full_flow_run = await compiled_app.ainvoke(final_input_state_dict, config=config)
    final_state = GraphState(**full_flow_run)

    print(f"\\n--- Final Workflow State (after full run) ---")
    print(f"Conversation ID: {final_state.conversation_id}")
    print(f"Current Stage: {final_state.current_stage}")
    print(f"Is Complete: {final_state.is_complete}")
    print(f"Requires Human Input: {final_state.requires_human_input}")
    print(f"Messages: ")
    for msg in final_state.messages:
        print(f"  {msg['role']}: {msg['content']}")
    print(f"Elasticsearch Queries ({len(final_state.elasticsearch_queries)}): ")
    for q_idx, q_val in enumerate(final_state.elasticsearch_queries):
        print(f"  Query {q_idx+1}: {q_val}")
    # print(f"Retrieved Data: {final_state.retrieved_data}") # Can be verbose
    print(f"Processed Themes ({len(final_state.processed_themes)}): ")
    for theme_idx, theme_val in enumerate(final_state.processed_themes):
        print(f"  Theme {theme_idx+1}: {theme_val}")

    # To inspect a persisted state (if using MemorySaver and same thread_id):
    # persisted_state_data = memory.get(config)
    # if persisted_state_data:
    #     persisted_state = GraphState(**persisted_state_data)
    #     print("\n--- State from MemorySaver ---")
    #     print(persisted_state.model_dump_json(indent=2))

if __name__ == "__main__":
    import asyncio
    # import os
    # from dotenv import load_dotenv
    # load_dotenv() # Ensure OPENAI_API_KEY is available
    # if not os.getenv("OPENAI_API_KEY"):
    #     print("OPENAI_API_KEY not set. Exiting.")
    # else:
    #     asyncio.run(run_example_conversation())
    asyncio.run(run_example_conversation())
