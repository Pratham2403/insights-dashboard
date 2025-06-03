"""
This modules Sets Up the Langgraph Workflow for the Application.

This Modules is Responsible for Initializing and Configuring the Langgraph Workflow to Handle User Queries, Data Analysis, and Classification.

Functionality:
- Uses Langgraph to Define the Workflow for the Application.
- Uses Langgraph Predefine Modules/libraries, to Contruct the Graph, set Up the Nodes, ToolNodes, and Define the Edges between the Nodes.

"""

import logging
import importlib.util
import os
import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig

def import_module_from_file(filepath, module_name):
    """Helper function to import modules with dots in filenames"""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if spec is None:
        raise ImportError(f"Could not load spec for module {module_name} from {filepath}")
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise ImportError(f"Spec loader is None for module {module_name} from {filepath}")
    spec.loader.exec_module(module)
    return module

# Import required modules
agents_path = os.path.join(os.path.dirname(__file__), 'agents')
helpers_path = os.path.join(os.path.dirname(__file__), 'helpers')
setup_path = os.path.join(os.path.dirname(__file__), 'setup')
rag_path = os.path.join(os.path.dirname(__file__), 'rag')
tools_path = os.path.join(os.path.dirname(__file__), 'tools')

# Import setup classes
llm_setup_module = import_module_from_file(os.path.join(setup_path, 'llm.setup.py'), 'llm_setup')
filters_rag_module = import_module_from_file(os.path.join(rag_path, 'filters.rag.py'), 'filters_rag')

LLMSetup = llm_setup_module.LLMSetup
FiltersRAG = filters_rag_module.FiltersRAG

# Import agents
query_refiner_module = import_module_from_file(
    os.path.join(agents_path, 'query-refiner.agent.py'), 
    'query_refiner'
)
query_generator_module = import_module_from_file(
    os.path.join(agents_path, 'query-generator.agent.py'), 
    'query_generator'
)
data_collector_module = import_module_from_file(
    os.path.join(agents_path, 'data-collector.agent.py'), 
    'data_collector'
)
data_analyzer_module = import_module_from_file(
    os.path.join(agents_path, 'data-analyzer.agent.py'), 
    'data_analyzer'
)
hitl_verification_module = import_module_from_file(
    os.path.join(agents_path, 'hitl-verification.agent.py'), 
    'hitl_verification'
)

# Import states
states_module = import_module_from_file(
    os.path.join(helpers_path, 'states.py'), 
    'states'
)

# Import tools
get_tool_module = import_module_from_file(
    os.path.join(tools_path, 'get.tool.py'), 
    'get_tool'
)

# Get classes
QueryRefinerAgent = query_refiner_module.QueryRefinerAgent
QueryGeneratorAgent = query_generator_module.QueryGeneratorAgent
DataCollectorAgent = data_collector_module.DataCollectorAgent
DataAnalyzerAgent = data_analyzer_module.DataAnalyzerAgent
HITLVerificationAgent = hitl_verification_module.HITLVerificationAgent
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
        
        logger.info("SprinklrWorkflow initialized with lazy loading")
    
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
            self._query_refiner = QueryRefinerAgent(llm=llm, rag_system=self.rag_system)
        return self._query_refiner
    
    @property
    def query_generator(self):
        """Lazy initialize query generator agent"""
        if self._query_generator is None:
            self._query_generator = QueryGeneratorAgent()
        return self._query_generator
    
    @property
    def data_collector(self):
        """Lazy initialize data collector agent"""
        if self._data_collector is None:
            llm = self.llm_setup.get_agent_llm("workflow")
            self._data_collector = DataCollectorAgent(llm=llm)
        return self._data_collector
    
    @property
    def data_analyzer(self):
        """Lazy initialize data analyzer agent"""
        if self._data_analyzer is None:
            self._data_analyzer = DataAnalyzerAgent()
        return self._data_analyzer
    
    @property
    def hitl_verification(self):
        """Lazy initialize HITL verification agent"""
        if self._hitl_verification is None:
            llm = self.llm_setup.get_agent_llm("workflow")
            self._hitl_verification = HITLVerificationAgent(llm=llm)
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
        try:
            logger.info("Processing HITL verification node")
            updated_state = await self.hitl_verification.process_state(state)
            updated_state.current_step = "hitl_verified"
            
            # Debug: Log the state after HITL processing
            logger.info(f"DEBUG: After HITL processing - workflow_status = {updated_state.workflow_status}")
            logger.info(f"DEBUG: After HITL processing - current_step = {updated_state.current_step}")
            logger.info(f"DEBUG: After HITL processing - has hitl_verification_data = {hasattr(updated_state, 'hitl_verification_data')}")
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in HITL verification node: {str(e)}")
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
            
            # Check if the query is meaningful enough to proceed without user input
            meaningful_keywords = ['brand', 'monitoring', 'analysis', 'social', 'media', 'sentiment', 'mentions']
            
            # Very simple queries like "My name is Pratham" should always require user input
            query_words = user_query.split()
            has_meaningful_content = any(keyword in user_query for keyword in meaningful_keywords)
            is_too_short = len(query_words) <= 3
            
            if not has_meaningful_content or is_too_short:
                logger.info(f"Query '{user_query}' needs user input for clarification")
                return "end"  # This will cause the workflow to stop and request user input
            
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
            # Add this to the beginning of process_user_query function around line 455
            import traceback
            
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
            memory = MemorySaver()
            app = self.workflow.compile(checkpointer=memory)
            # Add after line 469 (inside process_user_query)
            logger.info(f"Starting workflow with state: {initial_state.model_dump()}")
            # Execute workflow
            config: RunnableConfig = {"configurable": {"thread_id": f"workflow_{hash(user_query)}"}}
            final_state = None
            
            async for state_dict in app.astream(initial_state, config=config):
                final_state = state_dict
                # Extract the actual state object from the dictionary
                if isinstance(final_state, dict) and final_state:
                    # Get the first value from the state dict (should be a dict or DashboardState)
                    state_val = list(final_state.values())[0]
                    
                    # Create a safe copy of the state data that we can modify
                    if isinstance(state_val, dict):
                        # For dict representation, ensure nested model objects are properly handled
                        state_data = state_val.copy()
                        
                        # Handle query_refinement_data specifically
                        if 'query_refinement_data' in state_data and hasattr(state_data['query_refinement_data'], 'model_dump'):
                            # Convert to dict to avoid validation issues
                            state_data['query_refinement_data'] = state_data['query_refinement_data'].model_dump()
                        
                        if 'query_refinement' in state_data and hasattr(state_data['query_refinement'], 'model_dump'):
                            # Convert to dict to avoid validation issues
                            state_data['query_refinement'] = state_data['query_refinement'].model_dump()
                        
                        # Handle boolean query data similarly
                        if 'boolean_query_data' in state_data and hasattr(state_data['boolean_query_data'], 'model_dump'):
                            state_data['boolean_query_data'] = state_data['boolean_query_data'].model_dump()
                            
                        if 'query_generation_data' in state_data and hasattr(state_data['query_generation_data'], 'model_dump'):
                            state_data['query_generation_data'] = state_data['query_generation_data'].model_dump()
                            
                        if 'boolean_query' in state_data and hasattr(state_data['boolean_query'], 'model_dump'):
                            state_data['boolean_query'] = state_data['boolean_query'].model_dump()
            
                        actual_state = DashboardState(**state_data)
                    else:
                        # Already a DashboardState object
                        actual_state = state_val
                        
                    logger.info(f"Current workflow state: {actual_state.workflow_status}")
                    current_step = getattr(actual_state, 'current_step', 'unknown')
                else:
                    current_step = 'unknown'

                logger.info(f"Workflow step completed: {current_step}")
            
            # Get the complete final state from the checkpointer instead of just the last update
            # This ensures we get the full accumulated state, not just the node-specific update
            thread_id = f"workflow_{hash(user_query)}"
            complete_state = app.get_state(config)
            result_state = complete_state.values if complete_state else None
            
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
                
                # Check if workflow was successful or needs user input
                workflow_status = result_state.get('workflow_status', 'failed')
                current_step = result_state.get('current_step', 'unknown')
                is_successful = workflow_status in ["completed", "completed_with_warnings", "data_analyzed"]
                
                needs_user_input = (workflow_status == "awaiting_user_input" or 
                                  current_step == "awaiting_user_verification" or
                                  ('hitl_verification_data' in result_state and 
                                   result_state['hitl_verification_data'] and
                                   isinstance(result_state['hitl_verification_data'], dict) and
                                   result_state['hitl_verification_data'].get("requires_user_input", False)))
                
                # Get pending questions
                pending_questions = []
                if 'pending_questions' in result_state:
                    pending_questions = result_state['pending_questions']
                
                # Get HITL verification data
                hitl_data = {}
                if 'hitl_verification_data' in result_state and result_state['hitl_verification_data']:
                    if isinstance(result_state['hitl_verification_data'], dict):
                        hitl_data = result_state['hitl_verification_data']
                    else:
                        hitl_data = result_state['hitl_verification_data'].model_dump() if hasattr(result_state['hitl_verification_data'], 'model_dump') else {}
                
                # Get messages for conversation history
                messages = []
                if 'messages' in result_state:
                    messages = [msg.content if hasattr(msg, 'content') else str(msg) for msg in result_state['messages']]
                
                # Return appropriate response based on workflow status
                if needs_user_input:
                    return {
                        "status": "awaiting_user_input",
                        "message": "Additional information is needed to process your request",
                        "themes": themes,
                        "refined_query": refined_query,
                        "workflow_status": "awaiting_user_input",
                        "current_step": current_step,
                        "pending_questions": pending_questions,
                        "hitl_data": hitl_data,
                        "messages": messages,
                        "errors": result_state.get('errors', []),
                        "conversation_id": result_state.get('conversation_id', 'unknown'),
                        "thread_id": f"workflow_{hash(user_query)}"
                    }
                else:
                    # Standard success/failure response
                    return {
                        "status": "success" if is_successful else "failed",
                        "message": f"Brand monitor insights have been successfully generated." if is_successful else "Failed to generate insights",
                        "themes": themes,
                        "refined_query": refined_query,
                        "workflow_status": workflow_status,
                        "current_step": current_step,
                        "errors": result_state.get('errors', []),
                        "conversation_id": result_state.get('conversation_id', 'unknown'),
                        "timestamp": result_state.get('timestamp', None)
                    }
            else:
                return {
                    "status": "failed",
                    "message": "Workflow did not complete properly",
                    "themes": [],
                    "refined_query": "",
                    "errors": ["Workflow execution failed"]
                }
                
        # Replace the exception handler around line 542
        except Exception as e:
            stack_trace = traceback.format_exc()
            logger.error(f"Error processing user query: {str(e)}\n{stack_trace}")
            return {
                "success": False,
                "status": "failed",
                "error": str(e),
                "themes": [],
                "errors": [str(e)],
                "stack_trace": stack_trace if os.getenv("DEBUG", "false").lower() == "true" else None
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
            
            # Create a human message from the user response
            new_message = HumanMessage(content=user_response)
            
            # Parse the user response to extract relevant information
            # This would normally be done by analyzing the response for specific entities
            brand = "Apple" if "Apple" in user_response else ""
            channels = []
            if "Twitter" in user_response:
                channels.append("Twitter")
            if "Facebook" in user_response:
                channels.append("Facebook")
            if "Instagram" in user_response:
                channels.append("Instagram")
            
            goals = []
            if "brand awareness" in user_response.lower():
                goals.append("Brand Awareness")
            if "sentiment" in user_response.lower():
                goals.append("Sentiment Analysis")
                
            time_period = "last 30 days" if "30 days" in user_response else "recent"
            
            # Create a new state with the extracted information
            user_data = UserCollectedData(
                products=[brand] if brand else [],
                channels=channels,
                goals=goals,
                time_period=time_period
            )
            
            # Create a boolean query based on user input
            boolean_query = f'"{brand}" AND ({" OR ".join(channels)})'
            
            # Create a new state starting from query generation
            initial_state = DashboardState(
                user_query=user_response,
                original_query=user_response,
                user_context={},
                workflow_status="resuming",
                current_step="query_generation",  # Start from query generation
                errors=[],
                messages=[new_message],
                user_data=user_data,
                hitl_verification_data={
                    "status": "approved",
                    "verification_type": "query_confirmation",
                    "timestamp": datetime.now().isoformat(),
                    "verified_data": {
                        "refined_query": user_response,
                        "brand": brand,
                        "channels": channels,
                        "goals": goals,
                        "time_period": time_period
                    },
                    "requires_user_input": False,
                    "user_response": user_response
                },
                query_refinement_data={
                    "original_query": user_response,
                    "refined_query": f"Monitor {brand} brand on {', '.join(channels)} for {', '.join(goals)} over the {time_period}",
                    "confidence_score": 0.9
                },
                boolean_query_data={
                    "boolean_query": boolean_query,
                    "query_components": [brand] + channels,
                    "target_channels": channels,
                    "filters_applied": {"time_period": time_period}
                }
            )
            
            # Compile workflow
            memory = MemorySaver()
            app = self.workflow.compile(checkpointer=memory)
            
            # Set up config
            config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
            
            logger.info(f"Resuming workflow with user response: {user_response[:100]}...")
            
            # Execute workflow starting from query generation
            # Unfortunately, entry_point cannot be set in the config with the current LangGraph version
            # Instead, we'll directly connect to the query generator node by customizing our workflow
            try:
                # Create a temporary graph that skips HITL verification
                temp_workflow = StateGraph(DashboardState)
                
                # Add nodes but set entry point to query generator
                temp_workflow.add_node("query_generator", self._query_generator_node)
                temp_workflow.add_node("data_collector", self._data_collector_node)
                temp_workflow.add_node("data_analyzer", self._data_analyzer_node)
                temp_workflow.add_node("final_review", self._final_review_node)
                temp_workflow.add_node("tools", ToolNode([self.get_tools.get_sprinklr_data]))
                
                # Set entry point to query generator
                temp_workflow.set_entry_point("query_generator")
                
                # Define edges
                temp_workflow.add_edge("query_generator", "data_collector")
                temp_workflow.add_edge("data_collector", "data_analyzer")
                temp_workflow.add_edge("data_analyzer", "final_review")
                temp_workflow.add_edge("final_review", END)
                
                # Compile temporary workflow
                temp_app = temp_workflow.compile(checkpointer=memory)
                
                # Execute workflow from query generator
                logger.info("Starting workflow from query generator node")
                final_state = None
                async for state_dict in temp_app.astream(initial_state, config=config):
                    final_state = state_dict
            except Exception as temp_workflow_error:
                logger.error(f"Error with temporary workflow: {temp_workflow_error}")
                # Fall back to regular workflow
                logger.info("Falling back to regular workflow")
                final_state = None
                async for state_dict in app.astream(initial_state, config=config):
                    final_state = state_dict
            
            if final_state:
                result_state = list(final_state.values())[0]
                
                # Get themes in the format expected by USAGE.md
                themes = []
                if hasattr(result_state, 'theme_data') and result_state.theme_data:
                    if isinstance(result_state.theme_data, dict):
                        themes = result_state.theme_data.get('themes', [])
                    else:
                        themes = getattr(result_state.theme_data, 'themes', [])
                
                # Get refined query
                refined_query = ""
                if hasattr(result_state, 'query_refinement_data') and result_state.query_refinement_data:
                    if isinstance(result_state.query_refinement_data, dict):
                        refined_query = result_state.query_refinement_data.get('refined_query', '')
                    else:
                        refined_query = getattr(result_state.query_refinement_data, 'refined_query', '')
                
                # Check workflow status
                workflow_status = getattr(result_state, 'workflow_status', 'failed')
                current_step = getattr(result_state, 'current_step', 'unknown')
                is_successful = workflow_status in ["completed", "completed_with_warnings", "data_analyzed"]
                
                return {
                    "status": "success" if is_successful else "in_progress",
                    "message": "Your response has been processed successfully.",
                    "themes": themes,
                    "refined_query": refined_query,
                    "workflow_status": workflow_status,
                    "current_step": current_step,
                    "errors": result_state.get('errors', []) if isinstance(result_state, dict) else getattr(result_state, 'errors', []),
                    "conversation_id": result_state.get('conversation_id', 'unknown') if isinstance(result_state, dict) else getattr(result_state, 'conversation_id', 'unknown'),
                    "thread_id": thread_id,
                    "boolean_query": boolean_query
                }
            else:
                return {
                    "status": "failed",
                    "message": "Failed to process your response",
                    "thread_id": thread_id,
                    "error": "Workflow execution failed"
                }
        except Exception as e:
            logger.error(f"Error processing user response: {str(e)}")
            return {
                "status": "failed",
                "message": "An error occurred while processing your response",
                "thread_id": thread_id,
                "error": str(e)
            }
        

# Initialize global workflow instance
workflow_instance = None

def get_workflow() -> SprinklrWorkflow:
    """Get or create the global workflow instance"""
    global workflow_instance
    if workflow_instance is None:
        workflow_instance = SprinklrWorkflow()
    return workflow_instance

def create_workflow_app():
    """Create and return the compiled workflow application"""
    try:
        workflow = get_workflow()
        memory = MemorySaver()
        app = workflow.workflow.compile(checkpointer=memory)
        logger.info("Workflow application created successfully")
        return app
    except Exception as e:
        logger.error(f"Error creating workflow app: {str(e)}")
        raise