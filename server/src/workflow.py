"""
This modules Sets Up the Langgraph Workflow for the Application.

This Modules is Responsible for Initializing and Configuring the Langgraph Workflow to Handle User Queries, Data Analysis, and Classification.

Functionality:
- Uses Langgraph to Define the Workflow for the Application.
- Uses Langgraph Predefine Modules/libraries, to Contruct the Graph, set Up the Nodes, ToolNodes, and Define the Edges between the Nodes.

"""

import logging
from typing import Dict, Any, List, Optional, Union
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig

# Import agents and helpers
import importlib.util
import os

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

logger = logging.getLogger(__name__)

class SprinklrWorkflow:
    """
    LangGraph workflow orchestrator for the Sprinklr Listening Dashboard.
    
    This class manages the multi-agent workflow for processing user queries,
    refining them, generating boolean queries, collecting data, and analyzing
    it into meaningful themes.
    """
    
    def __init__(self):
        """Initialize the workflow with all agents and tools"""
        
        # Initialize LLM setup
        llm_setup = LLMSetup()
        llm = llm_setup.get_agent_llm("workflow")
        
        # Initialize RAG system (lazy initialization)
        rag_system = filters_rag_module.get_filters_rag()
        
        # Initialize agents with required parameters
        self.query_refiner = QueryRefinerAgent(llm=llm, rag_system=rag_system)
        self.query_generator = QueryGeneratorAgent()
        self.data_collector = DataCollectorAgent(llm=llm)
        self.data_analyzer = DataAnalyzerAgent()
        self.hitl_verification = HITLVerificationAgent(llm=llm)
        
        # Initialize tools
        self.get_tools = get_tool_module.GetTools()
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
        
        logger.info("SprinklrWorkflow initialized successfully")
    
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
            import re
            if boolean_query and boolean_query.strip().startswith('```json'):
                # Extract the actual query from JSON response
                try:
                    import json
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
                    fetched_data = await self.get_tools.get_sprinklr_data.invoke({
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
            if state.hitl_verification_data:
                # Access verification_status safely from dict
                verification_status = state.hitl_verification_data.get("status", "pending")
                
                if verification_status == "approved":
                    return "proceed"
                elif verification_status == "needs_refinement":
                    return "refine"
                else:
                    return "end"
            
            # Default to proceed if no verification data
            return "proceed"
            
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
            from langchain_core.messages import HumanMessage
            
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
            
            # Extract final state
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
                
                # Check if workflow was successful
                workflow_status = getattr(result_state, 'workflow_status', 'failed')
                is_successful = workflow_status in ["completed", "completed_with_warnings", "data_analyzed"]
                
                # Return response in USAGE.md format
                return {
                    "status": "success" if is_successful else "failed",
                    "message": f"Brand monitor insights have been successfully generated." if is_successful else "Failed to generate insights",
                    "themes": themes,
                    "refined_query": refined_query,
                    "workflow_status": workflow_status,
                    "current_step": getattr(result_state, 'current_step', 'unknown'),
                    "errors": getattr(result_state, 'errors', []),
                    "conversation_id": getattr(result_state, 'conversation_id', 'unknown'),
                    "timestamp": getattr(result_state, 'timestamp', None)
                }
            else:
                return {
                    "status": "failed",
                    "message": "Workflow did not complete properly",
                    "themes": [],
                    "refined_query": "",
                    "errors": ["Workflow execution failed"]
                }
                
        except Exception as e:
            logger.error(f"Error processing user query: {str(e)}")
            return {
                "success": False,
                "status": "failed",
                "error": str(e),
                "themes": [],
                "errors": [str(e)]
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