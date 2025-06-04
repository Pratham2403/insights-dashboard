"""
This module sets up the LangGraph workflow for the application.

Functionality:
- Defines the workflow for handling user queries, data analysis, and classification.
- Uses LangGraph to construct the graph, set up nodes, and define edges.
"""

import logging
import importlib.util
import os
import re
import json
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from src.utils.files_helper import import_module_from_file 

# Import required modules
agents_path = os.path.join(os.path.dirname(__file__), 'agents')
helpers_path = os.path.join(os.path.dirname(__file__), 'helpers')
setup_path = os.path.join(os.path.dirname(__file__), 'setup')
rag_path = os.path.join(os.path.dirname(__file__), 'rag')
tools_path = os.path.join(os.path.dirname(__file__), 'tools')

# Import setup classes
llm_setup_module = import_module_from_file(os.path.join(setup_path, 'llm_setup.py'), 'llm_setup')
filters_rag_module = import_module_from_file(os.path.join(rag_path, 'filters_rag.py'), 'filters_rag')

LLMSetup = llm_setup_module.LLMSetup
FiltersRAG = filters_rag_module.FiltersRAG

# Import agents
query_refiner_module = import_module_from_file(
    os.path.join(agents_path, 'query_refiner_agent.py'), 
    'query_refiner'
)
query_generator_module = import_module_from_file(
    os.path.join(agents_path, 'query_generator_agent.py'), 
    'query_generator'
)
data_collector_module = import_module_from_file(
    os.path.join(agents_path, 'data_collector_agent.py'), 
    'data_collector'
)
data_analyzer_module = import_module_from_file(
    os.path.join(agents_path, 'data_analyzer_agent.py'), 
    'data_analyzer'
)
hitl_verification_module = import_module_from_file(
    os.path.join(agents_path, 'hitl_verification_agent.py'), 
    'hitl_verification'
)

# Import states
states_module = import_module_from_file(
    os.path.join(helpers_path, 'states.py'), 
    'states'
)

# Import tools
get_tool_module = import_module_from_file(
    os.path.join(tools_path, 'get_tool.py'), 
    'get_tool'
)

# Import agent factory functions
create_query_refiner_agent = query_refiner_module.create_query_refiner_agent
create_query_generator_agent = query_generator_module.create_query_generator_agent
create_data_collector_agent = data_collector_module.create_data_collector_agent
create_data_analyzer_agent = data_analyzer_module.create_data_analyzer_agent
create_hitl_verification_agent = hitl_verification_module.create_hitl_verification_agent
DashboardState = states_module.DashboardState
QueryRefinementData = states_module.QueryRefinementData
UserCollectedData = states_module.UserCollectedData

logger = logging.getLogger(__name__)

class SprinklrWorkflow:
    """
    LangGraph workflow orchestrator for the Sprinklr Listening Dashboard.
    
    This class manages the multi-agent workflow for processing user queries,
    refining them, generating boolean queries, collecting data, and analyzing
    it into meaningful themes.
    """
    
    def __init__(self):
        """Initialize the workflow with lazy loading for better performance"""
        
        # Lazy initialization to improve startup performance
        self._llm_setup = None
        self._rag_system = None
        self._query_refiner = None
        self._query_generator = None
        self._data_collector = None
        self._data_analyzer = None
        self._hitl_verification = None
        self._get_tools = None
        self._workflow = None
        
        # Create persistent memory for state management across all methods
        from langgraph.checkpoint.memory import MemorySaver
        self._memory = MemorySaver()
        
        logger.info("SprinklrWorkflow initialized with lazy loading and persistent memory")
    
    @property
    def llm_setup(self):
        """Lazy initialize LLM setup"""
        if self._llm_setup is None:
            self._llm_setup = LLMSetup()
        return self._llm_setup
    
    @property
    def rag_system(self):
        """Lazy initialize RAG system"""
        if self._rag_system is None:
            self._rag_system = filters_rag_module.get_filters_rag()
        return self._rag_system
    
    @property
    def query_refiner(self):
        """Lazy initialize query refiner agent"""
        if self._query_refiner is None:
            llm = self.llm_setup.get_agent_llm("workflow")
            self._query_refiner = create_query_refiner_agent(llm=llm, rag_system=self.rag_system)
        return self._query_refiner
    
    @property
    def query_generator(self):
        """Lazy initialize query generator agent"""
        if self._query_generator is None:
            self._query_generator = create_query_generator_agent()
        return self._query_generator
    
    @property
    def data_collector(self):
        """Lazy initialize data collector agent"""
        if self._data_collector is None:
            llm = self.llm_setup.get_agent_llm("workflow")
            self._data_collector = create_data_collector_agent(llm=llm)
        return self._data_collector
    
    @property
    def data_analyzer(self):
        """Lazy initialize data analyzer agent"""
        if self._data_analyzer is None:
            self._data_analyzer = create_data_analyzer_agent()
        return self._data_analyzer
    
    @property
    def hitl_verification(self):
        """Lazy initialize HITL verification agent"""
        if self._hitl_verification is None:
            llm = self.llm_setup.get_agent_llm("workflow")
            self._hitl_verification = create_hitl_verification_agent(llm=llm)
        return self._hitl_verification
    
    @property
    def get_tools(self):
        """Lazy initialize tools"""
        if self._get_tools is None:
            self._get_tools = get_tool_module.GetTools()
        return self._get_tools
    
    @property 
    def workflow(self):
        """Lazy initialize workflow graph"""
        if self._workflow is None:
            self._workflow = self._create_workflow()
        return self._workflow
    
    def _create_workflow(self) -> StateGraph:
        """Create and configure the LangGraph workflow"""
        try:
            # Initialize workflow with state
            workflow = StateGraph(DashboardState)
            
            # Add nodes for each agent
            workflow.add_node("query_refiner", self._query_refiner_node)
            workflow.add_node("hitl_verification", self._hitl_verification_node) 
            workflow.add_node("query_generator", self._query_generator_node)
            workflow.add_node("data_collector", self._data_collector_node)
            workflow.add_node("data_analyzer", self._data_analyzer_node)
            workflow.add_node("final_review", self._final_review_node)
            
            # Add tool node for API calls
            workflow.add_node("tools", ToolNode([self.get_tools.get_sprinklr_data]))
            
            # Set entry point
            workflow.set_entry_point("query_refiner")
            
            # Define the workflow edges
            workflow.add_edge("query_refiner", "hitl_verification")
            
            # Conditional edge from HITL verification
            workflow.add_conditional_edges(
                "hitl_verification",
                self._should_proceed_from_hitl,
                {
                    "proceed": "query_generator",
                    "refine": "query_refiner",
                    "end": END
                }
            )
            
            workflow.add_edge("query_generator", "data_collector")
            workflow.add_edge("data_collector", "data_analyzer")
            workflow.add_edge("data_analyzer", "final_review")
            workflow.add_edge("final_review", END)
            
            logger.info("Workflow graph created successfully")
            return workflow
            
        except Exception as e:
            logger.error(f"Error creating workflow: {str(e)}")
            raise
    
    async def _query_refiner_node(self, state: DashboardState) -> DashboardState:
        """Process query refinement"""
        try:
            logger.info("Processing query refinement node")
            updated_state = await self.query_refiner.process_state(state)
            updated_state.current_step = "query_refined"
            
            # Convert Pydantic models to dictionaries to avoid validation issues
            if hasattr(updated_state, 'query_refinement') and isinstance(updated_state.query_refinement, QueryRefinementData):
                # Use model_dump() instead of directly assigning None
                updated_state.query_refinement = updated_state.query_refinement.model_dump()
            
            if hasattr(updated_state, 'query_refinement_data') and isinstance(updated_state.query_refinement_data, QueryRefinementData):
                # Use model_dump() instead of directly assigning None
                updated_state.query_refinement_data = updated_state.query_refinement_data.model_dump()
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in query refiner node: {str(e)}")
            state.errors.append(f"Query refinement failed: {str(e)}")
            state.workflow_status = "failed"
            return state
    
    async def _hitl_verification_node(self, state: DashboardState) -> DashboardState:
        """Process HITL verification"""
        from langgraph.types import Interrupt
        
        try:
            logger.info("Processing HITL verification node")
            
            # Ensure necessary fields exist on state
            if not hasattr(state, "hitl_outcome"):
                # Initialize the field if missing
                state.hitl_outcome = None
                logger.info("Added missing hitl_outcome field to state")
                
            # Prepare the HITL input payload with the refined query data
            state.hitl_input_payload = {
                "conversation_id": state.conversation_id,
                "original_query": state.original_query,
                "refined_query": getattr(state.query_refinement_data, "refined_query", state.original_query) if hasattr(state, "query_refinement_data") else state.original_query,
                "user_data": state.user_data.model_dump() if hasattr(state.user_data, "model_dump") else state.user_data,
                "awaiting_confirmation": True,
                "verification_type": "data_confirmation",
                "questions": ["Is this refined query accurate?", "Is all the necessary information collected?"],
                "current_stage": state.current_stage,
                "next_steps": ["Proceed to generate query", "Collect more information", "Refine query further"]
            }
            
            # Call invoke instead of process_state
            result = await self.hitl_verification.invoke(state)
            
            # Check if the result is an Interrupt
            if isinstance(result, Interrupt):
                logger.info("HITL verification returned interrupt - returning to LangGraph")
                return result
            
            # Otherwise, merge the updates into the state
            # The invoke method of HITLVerificationAgent returns a dictionary of updates
            for key, value in result.items():
                setattr(state, key, value)
            
            state.current_step = "hitl_verified" 
            
            # Check if hitl_outcome indicates an error from the agent itself (e.g. bad input)
            if hasattr(state, "hitl_outcome") and isinstance(state.hitl_outcome, dict) and state.hitl_outcome.get("error"):
                error_message = state.hitl_outcome.get("error")
                logger.error(f"HITL agent returned an error: {error_message}")
                state.errors.append(f"HITL verification failed: {error_message}")
                state.workflow_status = "failed"

            # Debug: Log the state after HITL processing
            logger.info(f"DEBUG: After HITL processing - workflow_status = {state.workflow_status}")
            logger.info(f"DEBUG: After HITL processing - current_step = {state.current_step}")
            logger.info(f"DEBUG: After HITL processing - hitl_outcome = {getattr(state, 'hitl_outcome', None)}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in HITL verification node: {str(e)}")
            traceback.print_exc()
            state.errors.append(f"HITL verification failed: {str(e)}")
            state.workflow_status = "failed"
            return state
    
    async def _query_generator_node(self, state: DashboardState) -> DashboardState:
        """Process query generation"""
        try:
            logger.info("Processing query generator node")
            updated_state = await self.query_generator.process_state(state)
            updated_state.current_step = "query_generated"
            
            # Convert Pydantic models to dictionaries to avoid validation issues
            if hasattr(updated_state, 'boolean_query_data') and hasattr(updated_state.boolean_query_data, 'model_dump'):
                updated_state.boolean_query_data = updated_state.boolean_query_data.model_dump()
            
            if hasattr(updated_state, 'query_generation_data') and hasattr(updated_state.query_generation_data, 'model_dump'):
                updated_state.query_generation_data = updated_state.query_generation_data.model_dump()
                
            if hasattr(updated_state, 'boolean_query') and hasattr(updated_state.boolean_query, 'model_dump'):
                updated_state.boolean_query = updated_state.boolean_query.model_dump()
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in query generator node: {str(e)}")
            state.errors.append(f"Query generation failed: {str(e)}")
            state.workflow_status = "failed"
            return state
    
    async def _data_collector_node(self, state: DashboardState) -> DashboardState:
        """Process data collection setup"""
        try:
            logger.info("Processing data collector node")
            updated_state = await self.data_collector.process_state(state)
            updated_state.current_step = "data_collection_ready"
            
            # Extract boolean query from state
            boolean_query = ""
            if hasattr(updated_state, 'boolean_query_data') and updated_state.boolean_query_data:
                if isinstance(updated_state.boolean_query_data, dict):
                    boolean_query = updated_state.boolean_query_data.get('boolean_query', '')
                else:
                    boolean_query = getattr(updated_state.boolean_query_data, 'boolean_query', '')
            
            # Clean up the boolean query if it's wrapped in JSON
            if boolean_query and boolean_query.strip().startswith('```json'):
                # Extract the actual query from JSON response
                try:
                    # Remove markdown formatting
                    json_str = re.sub(r'```json\n(.*?)\n```', r'\1', boolean_query, flags=re.DOTALL)
                    parsed = json.loads(json_str)
                    boolean_query = parsed.get('boolean_query', '')
                except Exception as e:
                    logger.warning(f"Failed to parse JSON boolean query: {e}")
                    # Fallback to simple query
                    boolean_query = 'brand monitoring'
            
            # Call the tool directly and populate fetched_data
            if boolean_query:
                logger.info(f"Fetching data with query: {boolean_query}")
                try:
                    # Use the tool directly with proper invoke method
                    fetched_data = await self.get_tools.get_sprinklr_data.ainvoke({
                        "query": boolean_query,
                        "filters": None,
                        "limit": 0
                    })
                    updated_state.fetched_data = fetched_data if fetched_data else []
                    logger.info(f"Fetched {len(updated_state.fetched_data)} data points")
                    
                except Exception as tool_error:
                    logger.error(f"Error fetching data with tool: {tool_error}")
                    updated_state.fetched_data = []
                    updated_state.errors.append(f"Data fetching failed: {str(tool_error)}")
            else:
                logger.error("No boolean query available for data fetching")
                updated_state.fetched_data = []
                updated_state.errors.append("No boolean query available for data fetching")
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in data collector node: {str(e)}")
            state.errors.append(f"Data collection setup failed: {str(e)}")
            state.workflow_status = "failed"
            return state
    
    async def _data_analyzer_node(self, state: DashboardState) -> DashboardState:
        """Process data analysis"""
        try:
            logger.info("Processing data analyzer node")
            updated_state = await self.data_analyzer.process_state(state)
            updated_state.current_step = "data_analyzed"
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in data analyzer node: {str(e)}")
            state.errors.append(f"Data analysis failed: {str(e)}")
            state.workflow_status = "failed"
            return state
    
    async def _final_review_node(self, state: DashboardState) -> DashboardState:
        """Final review and completion"""
        try:
            logger.info("Processing final review")
            
            # Check if we have successful results
            themes_count = 0
            if state.theme_data:
                if isinstance(state.theme_data, dict):
                    themes = state.theme_data.get('themes', [])
                    themes_count = len(themes) if themes else 0
                else:
                    themes = getattr(state.theme_data, 'themes', [])
                    themes_count = len(themes) if themes else 0
            
            if themes_count > 0:
                state.workflow_status = "completed"
                state.current_step = "completed"
                logger.info(f"Workflow completed successfully with {themes_count} themes")
            else:
                state.workflow_status = "completed_with_warnings"
                state.current_step = "completed"
                state.errors.append("No themes were generated")
                logger.warning("Workflow completed but no themes were generated")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in final review node: {str(e)}")
            state.errors.append(f"Final review failed: {str(e)}")
            state.workflow_status = "failed"
            return state
    
    def _should_proceed_from_hitl(self, state: DashboardState) -> str:
        """Determine next step after HITL verification"""
        try:
            # Debug: Log the incoming state
            logger.info(f"DEBUG: _should_proceed_from_hitl called with workflow_status = {getattr(state, 'workflow_status', 'unknown')}")
            logger.info(f"DEBUG: _should_proceed_from_hitl called with current_step = {getattr(state, 'current_step', 'unknown')}")
            logger.info(f"DEBUG: _should_proceed_from_hitl has hitl_verification_data = {hasattr(state, 'hitl_verification_data')}")
            
            # Check if we have HITL verification data
            if hasattr(state, 'hitl_verification_data') and state.hitl_verification_data:
                # Access verification_status safely from dict
                if isinstance(state.hitl_verification_data, dict):
                    verification_status = state.hitl_verification_data.get("status", "pending")
                    requires_user_input = state.hitl_verification_data.get("requires_user_input", False)
                else:
                    verification_status = getattr(state.hitl_verification_data, "status", "pending")
                    requires_user_input = getattr(state.hitl_verification_data, "requires_user_input", False)
                
                # If the verification specifically requires user input, end the workflow
                # to allow the API to return and prompt the user
                if requires_user_input or verification_status == "needs_refinement":
                    logger.info("HITL verification requires user input, stopping workflow for user interaction")
                    return "end"
                
                # If the verification was approved by a previous user response, continue
                if verification_status == "approved":
                    logger.info("HITL verification approved, proceeding to query generation")
                    return "proceed"
                
                # For any other status, end the workflow
                logger.info(f"HITL verification status: {verification_status}, stopping workflow")
                return "end"
            
            # Default behavior: for incomplete user queries, always require HITL verification
            user_query = getattr(state, 'user_query', '').strip().lower()
            
            # Use Query Refiner Agent to determine if query is meaningful enough
            try:
                # Get dynamic assessment from Query Refiner Agent
                refinement_analysis = self.query_refiner.refine_query(user_query)
                
                # Check if the refinement indicates the query needs more information
                if hasattr(refinement_analysis, 'get'):
                    confidence_score = refinement_analysis.get('confidence_score', 0)
                    missing_info = refinement_analysis.get('missing_information', [])
                    
                    # If confidence is low or there's significant missing information, require user input
                    if confidence_score < 0.5 or len(missing_info) > 3:
                        logger.info(f"Query '{user_query}' needs user input based on dynamic analysis (confidence: {confidence_score})")
                        return "end"
                else:
                    # Fallback: if we can't analyze dynamically, check basic criteria
                    query_words = user_query.split()
                    is_too_short = len(query_words) <= 3;
                    
                    if is_too_short:
                        logger.info(f"Query '{user_query}' is too short and needs user input")
                        return "end"
                        
            except Exception as e:
                logger.warning(f"Could not dynamically analyze query meaningfulness: {e}")
                # Fallback to simple length check
                query_words = user_query.split()
                is_too_short = len(query_words) <= 3
                
                if is_too_short:
                    logger.info(f"Query '{user_query}' needs user input (fallback analysis)")
                    return "end"
            
            # If no verification data but query seems complete, also end for user confirmation
            logger.info("No HITL verification data available, requiring user confirmation")
            return "end"
            
        except Exception as e:
            logger.error(f"Error determining HITL next step: {str(e)}")
            return "end"
        
        
    async def process_user_query(
        self, 
        user_query: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the complete workflow.
        
        Args:
            user_query: The user's natural language query
            user_context: Additional context about the user's preferences
            
        Returns:
            Dictionary containing the complete workflow results
        """
        try:
            logger.info(f"Starting workflow for query: {user_query[:100]}...")
            
            # Initialize state
            initial_state = DashboardState(
                user_query=user_query,
                original_query=user_query,  # Set both fields for compatibility
                user_context=user_context or {},
                workflow_status="started",
                current_step="initializing",
                errors=[],
                messages=[HumanMessage(content=user_query)],  # Add initial message for LangGraph
                query_refinement=None,
                query_refinement_data=None  # Explicitly set to None to avoid validation errors
            )
            
            # Compile and run workflow
            app = self.workflow.compile(checkpointer=self._memory)
            logger.info(f"Starting workflow with state: {initial_state.model_dump()}")
            
            # Execute workflow
            thread_id = f"workflow_{hash(user_query)}"
            config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
            
            # Initialize variables to track workflow state
            final_state = None
            is_interrupted = False
            interrupt_data = None
            
            try:
                # Stream the execution to capture intermediate states
                async for state_dict in app.astream(initial_state, config=config):
                    final_state = state_dict
                    # Process the state for meaningful data
                    if isinstance(final_state, dict) and final_state:
                        state_val = list(final_state.values())[0]
                        
                        # Create a safe copy of the state data that we can modify
                        if isinstance(state_val, dict):
                            state_data = state_val.copy()
                            actual_state = DashboardState(**state_data)
                        else:
                            # Already a DashboardState object
                            actual_state = state_val
                            
                        # Only access workflow_status if actual_state is properly set
                        if actual_state is not None:
                            logger.info(f"Current workflow state: {actual_state.workflow_status}")
                            current_step = getattr(actual_state, 'current_step', 'unknown')
                        else:
                            current_step = 'unknown'
                    else:
                        current_step = 'unknown'

                    logger.info(f"Workflow step completed: {current_step}")
                
                # No interruption occurred, process normally
                logger.info("Workflow completed without interruption")
                
            except Exception as e:
                # Check if this is an Interrupt exception (LangGraph will raise the Interrupt)
                if "Interrupt" in str(e):
                    logger.info(f"Workflow interrupted for user input: {str(e)}")
                    is_interrupted = True
                    
                    # Get the interrupts from the app
                    interrupts = app.get_interrupts(config)
                    if interrupts:
                        latest_interrupt = interrupts[-1]
                        interrupt_id = latest_interrupt["interrupt_id"]
                        interrupt_data = latest_interrupt["payload"]
                        logger.info(f"Interrupt ID: {interrupt_id}, Payload: {interrupt_data}")
                    else:
                        logger.error("Expected interrupts but none found")
                else:
                    # This is a real error, not an interrupt
                    logger.error(f"Error in workflow execution: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    return {
                        "status": "error",
                        "message": f"Error processing query: {str(e)}",
                        "conversation_id": thread_id,
                        "errors": [str(e)],
                        "workflow_status": "failed"
                    }
            
            # Get the complete final state from the checkpointer
            complete_state = app.get_state(config)
            result_state = complete_state.values if complete_state else None
            
            if is_interrupted and interrupt_data:
                # Workflow was interrupted for human input
                return {
                    "status": "awaiting_user_input",
                    "message": "Human input required to continue",
                    "conversation_id": thread_id,
                    "interrupt_data": interrupt_data,
                    "workflow_status": "awaiting_user_input",
                    "current_step": "human_verification",
                    "refined_query": result_state.get("query_refinement_data", {}).get("refined_query", "") if result_state else ""
                }
            
            if result_state:
                # Get themes from theme_data if it exists
                themes = []
                if 'theme_data' in result_state and result_state['theme_data']:
                    if isinstance(result_state['theme_data'], dict):
                        themes = result_state['theme_data'].get('themes', [])
                    else:
                        themes = getattr(result_state['theme_data'], 'themes', [])
                
                # Get refined query
                refined_query = ""
                if 'query_refinement_data' in result_state and result_state['query_refinement_data']:
                    if isinstance(result_state['query_refinement_data'], dict):
                        refined_query = result_state['query_refinement_data'].get('refined_query', '')
                    else:
                        refined_query = getattr(result_state['query_refinement_data'], 'refined_query', '')
                
                # Check workflow status
                workflow_status = result_state.get('workflow_status', 'failed')
                current_step = result_state.get('current_step', 'unknown')
                errors = result_state.get('errors', [])
                
                # Return formatted response
                return {
                    "status": "success" if workflow_status != "failed" else "failed",
                    "message": "Dashboard insights generated" if workflow_status != "failed" else "Failed to generate insights",
                    "conversation_id": thread_id,
                    "refined_query": refined_query,
                    "themes": themes,
                    "workflow_status": workflow_status,
                    "current_step": current_step,
                    "errors": errors,
                    "timestamp": datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
                }
            else:
                return {
                    "status": "error",
                    "message": "Could not retrieve final workflow state",
                    "conversation_id": thread_id,
                    "workflow_status": "failed"
                }
                
        except Exception as e:
            logger.error(f"Error processing user query: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "status": "error",
                "message": f"Error processing query: {str(e)}",
                "conversation_id": f"workflow_{hash(user_query)}",
                "errors": [str(e)],
                "workflow_status": "failed"
            }
    
    def get_workflow_status(self, thread_id: str) -> Dict[str, Any]:
        """Get the current status of a workflow execution"""
        try:
            # This would typically query the checkpointer for status
            # For now, return a basic status
            return {
                "thread_id": thread_id,
                "status": "running",
                "current_step": "unknown"
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return {
                "thread_id": thread_id,
                "status": "error",
                "error": str(e)
            }
    
    async def process_user_response(self, thread_id: str, user_response: str) -> Dict[str, Any]:
        """
        Process a user response to a pending question and resume the workflow.
        
        Args:
            thread_id: The thread ID for the conversation
            user_response: The user's response to the pending question
            
        Returns:
            Dictionary containing updated workflow results
        """
        try:
            logger.info(f"Processing user response for thread {thread_id}: {user_response[:100]}...")
            
            # Get the compiled workflow app with checkpointer
            app = self.workflow.compile(checkpointer=self._memory)
            config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
            
            # Check if there are any interrupts for this thread
            thread_state = app.get_state(config)
            
            if not thread_state:
                logger.error(f"No state found for thread {thread_id}")
                return {
                    "status": "error",
                    "message": f"No conversation found with ID {thread_id}",
                    "thread_id": thread_id
                }
            
            # Check for active interrupts
            try:
                thread_interrupts = app.get_interrupts(config)
            except AttributeError:
                logger.warning("CompiledStateGraph has no get_interrupts; assuming no pending interrupts")
                thread_interrupts = []
            if not thread_interrupts:
                logger.warning(f"No active interrupts found for thread {thread_id}, processing as regular response")
                # No interrupts to resume, handle as regular response
                # Create a human message from the user response
                new_message = HumanMessage(content=user_response)
                
                # Use standard workflow processing here
                # [Additional processing logic as needed]
                
                return {
                    "status": "success",
                    "message": "Your response has been processed",
                    "thread_id": thread_id,
                    "workflow_status": "in_progress"
                }
            
            # Process the most recent interrupt
            latest_interrupt = thread_interrupts[-1]
            interrupt_id = latest_interrupt["interrupt_id"]
            logger.info(f"Resuming workflow with interrupt_id: {interrupt_id}")
            
            # Prepare the human response payload
            human_response_payload = {
                "approved": True,  # Default to approved
                "feedback": user_response,
                "next_action": "continue"
            }
            
            # Check for rejection keywords
            rejection_keywords = ['no', 'incorrect', 'wrong', 'reject', 'refine', 'change', 'modify']
            if any(keyword in user_response.lower() for keyword in rejection_keywords):
                human_response_payload["approved"] = False
                human_response_payload["next_action"] = "refine"
                logger.info(f"Detected rejection in response: {user_response}")
            
            # Resume the workflow with the user's response
            result = None
            async for state_update in app.astream_interrupt(interrupt_id, human_response_payload, config=config):
                result = state_update  # Get the final state
            
            if not result:
                logger.error("No result returned from workflow resumption")
                return {
                    "status": "error",
                    "message": "Failed to resume workflow after user input",
                    "thread_id": thread_id
                }
            
            # Process the result to extract relevant information
            # The result contains the updated state dictionary
            final_state = None
            
            # Extract the state from the result
            if isinstance(result, dict) and len(result) > 0:
                # The result is typically {node_name: state}
                final_state = list(result.values())[0]
            
            if not final_state:
                logger.error(f"Could not extract state from result: {result}")
                return {
                    "status": "error",
                    "message": "Could not determine workflow state after resumption",
                    "thread_id": thread_id
                }
            
            # Extract information from the final state
            if hasattr(final_state, "values"):
                state_values = final_state.values
            elif isinstance(final_state, dict) and "values" in final_state:
                state_values = final_state["values"]
            else:
                state_values = final_state
            
            # Create a response with the relevant information
            themes = state_values.get("theme_data", {}).get("themes", [])
            refined_query = state_values.get("query_refinement_data", {}).get("refined_query", "")
            workflow_status = state_values.get("workflow_status", "in_progress")
            current_step = state_values.get("current_step", "")
            
            return {
                "status": "success",
                "message": "Your response has been processed successfully",
                "thread_id": thread_id,
                "themes": themes,
                "refined_query": refined_query,
                "workflow_status": workflow_status,
                "current_step": current_step
            }
            
        except Exception as e:
            logger.error(f"Error processing user response: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "message": "An error occurred while processing your response",
                "thread_id": thread_id,
                "error": str(e)
            }
    
    def analyze(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for process_user_query to maintain compatibility with app.py
        
        Args:
            user_query: User's query string
            context: Additional context dictionary
            
        Returns:
            Analysis results dictionary
        """
        import asyncio
        
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, we need to run in a new thread
            import concurrent.futures
            
            def run_async():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(self.process_user_query(user_query, context))
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async)
                return future.result()
                
        except RuntimeError:
            # No event loop running, we can create our own
            return asyncio.run(self.process_user_query(user_query, context))
    
    def validate_themes(self, themes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate generated themes for quality and relevance
        
        Args:
            themes: List of theme dictionaries to validate
            
        Returns:
            Validation results with feedback
        """
        try:
            validation_results = {
                "valid_themes": [],
                "invalid_themes": [],
                "suggestions": [],
                "overall_quality": "good"
            }
            
            for theme in themes:
                if self._validate_single_theme(theme):
                    validation_results["valid_themes"].append(theme)
                else:
                    validation_results["invalid_themes"].append(theme)
            
            # Calculate overall quality
            valid_count = len(validation_results["valid_themes"])
            total_count = len(themes)
            
            if total_count == 0:
                validation_results["overall_quality"] = "no_themes"
            elif valid_count / total_count >= 0.8:
                validation_results["overall_quality"] = "excellent"
            elif valid_count / total_count >= 0.6:
                validation_results["overall_quality"] = "good"
            else:
                validation_results["overall_quality"] = "needs_improvement"
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating themes: {e}")
            return {
                "valid_themes": [],
                "invalid_themes": themes,
                "suggestions": ["Unable to validate themes due to system error"],
                "overall_quality": "error"
            }
    
    def _validate_single_theme(self, theme: Dict[str, Any]) -> bool:
        """Validate a single theme for required fields and quality"""
        required_fields = ["name", "description", "boolean_keyword_query"]
        
        # Check required fields
        if not all(field in theme for field in required_fields):
            return False
        
        # Check field content quality
        if len(theme.get("name", "").strip()) < 3:
            return False
            
        if len(theme.get("description", "").strip()) < 10:
            return False
            
        if len(theme.get("boolean_keyword_query", "").strip()) < 5:
            return False
        
        return True


# Global workflow instance
_workflow_instance = None

def get_workflow() -> SprinklrWorkflow:
    """
    Get or create the global workflow instance
    
    Returns:
        SprinklrWorkflow instance
    """
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = SprinklrWorkflow()
    return _workflow_instance