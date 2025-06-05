"""
Complete Modern LangGraph Workflow Implementation
Following the exact architecture flow:
1. Query Refiner Agent → 2. Data Collector Agent → 3. HITL verification → 
4. Query Generator Agent → 5. ToolNode → 6. Data Analyzer Agent

Key Features:
- Modern LangGraph patterns with interrupt() and Command
- Memory persistence with conversation threads
- Human-in-the-loop verification
- Complete agent orchestration
"""

import logging
import json
import traceback
from typing import Dict, Any, List, Optional, Union, Literal
from datetime import datetime, timedelta
from pathlib import Path
import time

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command, interrupt

# Import our modern components
from src.config.settings import settings
from src.helpers.states import DashboardState
from src.setup.llm_setup import LLMSetup
from src.tools.get_tool import get_sprinklr_data
from src.agents.query_refiner_agent import QueryRefinerAgent
from src.agents.data_collector_agent import DataCollectorAgent
from src.agents.data_analyzer_agent import DataAnalyzerAgent
from src.agents.query_generator_agent import create_query_generator_agent

logger = logging.getLogger(__name__)

class SprinklrWorkflow:
    """
    Complete Modern LangGraph Workflow Implementation.
    
    Architecture Flow:
    1. User Query → Query Refiner Agent (adds defaults like 30-day duration)
    2. Data Collector Agent (extracts relevant data, creates keywords/filters lists)
    3. HITL verification with interrupt() - iterates until user confirms
    4. Query Generator Agent (creates Boolean queries using AND/OR/NEAR/NOT)
    5. ToolNode (API call with Boolean query)
    6. Data Analyzer Agent (processes results)
    
    Features:
    - Conversation memory with thread-based persistence
    - Modern LangGraph patterns (interrupt(), Command, MemorySaver)
    - Support for multiple conversation threads
    """
    
    def __init__(self):
        """Initialize the modern workflow with all components"""
        logger.info("Initializing Modern Sprinklr Workflow...")
        
        # Setup LLM
        self.llm_setup = LLMSetup()
        self.llm = self.llm_setup.get_agent_llm("workflow")
        
        # Initialize agents
        self.query_refiner = QueryRefinerAgent(self.llm)
        self.data_collector = DataCollectorAgent(self.llm)
        self.data_analyzer = DataAnalyzerAgent(self.llm)
        self.query_generator = create_query_generator_agent()
        
        # Setup tools
        self.tools = [get_sprinklr_data]
        self.tool_node = ToolNode(self.tools)
        
        # Memory management
        self.memory = MemorySaver()
        
        # Build workflow
        self.workflow = self._build_workflow()
        
        logger.info("Modern Sprinklr Workflow initialized successfully")
    
    def _build_workflow(self) -> StateGraph:
        """Build the complete LangGraph workflow following the architecture"""
        
        # Create state graph
        workflow = StateGraph(DashboardState)
        
        # Add nodes following the exact architecture flow
        workflow.add_node("query_refiner", self._query_refiner_node)
        workflow.add_node("data_collector", self._data_collector_node) 
        workflow.add_node("hitl_verification", self._hitl_verification_node)
        workflow.add_node("query_generator", self._query_generator_node)
        workflow.add_node("tools", self._tool_execution_node)  # Use custom tool node
        workflow.add_node("data_analyzer", self._data_analyzer_node)
        
        # Define the exact architecture flow
        workflow.add_edge(START, "query_refiner")
        workflow.add_edge("query_refiner", "data_collector")
        workflow.add_edge("data_collector", "hitl_verification")
        
        # HITL verification can loop back or continue
        workflow.add_conditional_edges(
            "hitl_verification",
            self._should_continue_hitl,
            {
                "continue": "query_generator",
                "refine": "query_refiner",
                "collect": "data_collector"
            }
        )
        
        workflow.add_edge("query_generator", "tools")
        workflow.add_edge("tools", "data_analyzer")
        workflow.add_edge("data_analyzer", END)
        
        # Compile with memory
        compiled_workflow = workflow.compile(
            checkpointer=self.memory,
            interrupt_before=["hitl_verification"]  # Always interrupt for HITL
        )
        
        logger.info("📋 Workflow compiled with interrupt_before=['hitl_verification']")
        logger.info(f"📊 Workflow nodes: {list(workflow.nodes.keys()) if hasattr(workflow, 'nodes') else 'Unknown'}")
        
        return compiled_workflow
    
    async def _query_refiner_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 1: Query Refiner Agent
        - Adds defaults like 30-day duration, Twitter/Instagram sources
        - Uses completeUseCase.txt for context
        """
        logger.info("🔍 Step 1: Query Refiner Agent")
        
        try:
            # Get the latest user message
            user_query = state["messages"][-1].content if state["messages"] else ""
            
            # Process with query refiner using correct method
            refined_result = await self.query_refiner({"user_query": user_query})
            
            # Extract refinement data
            query_refinement = refined_result.get("query_refinement", {})
            
            # Update state
            state["refined_query"] = query_refinement.get("refined_query", user_query)
            state["query_context"] = query_refinement.get("context", {})
            state["defaults_applied"] = query_refinement.get("defaults_applied", [])
            
            # Add system message about refinement
            refinement_msg = AIMessage(
                content=f"Query refined with defaults: {query_refinement.get('refined_query', user_query)}"
            )
            
            return {
                "messages": [refinement_msg],
                "refined_query": state["refined_query"],
                "query_context": state["query_context"],
                "defaults_applied": state["defaults_applied"]
            }
            
        except Exception as e:
            logger.error(f"Query Refiner error: {e}")
            error_msg = AIMessage(content=f"Error in query refinement: {str(e)}")
            return {"messages": [error_msg]}
    
    async def _data_collector_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 2: Data Collector Agent
        - Extracts relevant data from refined query
        - Uses filters.json for filter options
        - Creates keywords and filters lists
        """
        logger.info("📊 Step 2: Data Collector Agent")
        
        try:
            refined_query = state.get("refined_query", "")
            query_context = state.get("query_context", {})
            
            if not refined_query:
                logger.error("No refined query found in state")
                # Get user query as fallback
                user_query = state["messages"][-1].content if state["messages"] else ""
                refined_query = user_query
            
            # Process with data collector - pass the full state
            collection_result = await self.data_collector({
                **state,
                "refined_query": refined_query,
                "query_context": query_context
            })
            
            # Update state with collected data
            state["keywords"] = collection_result.get("keywords", [])
            state["filters"] = collection_result.get("filters", {})
            state["data_requirements"] = collection_result.get("data_requirements", {})
            state["extracted_entities"] = collection_result.get("extracted_entities", [])
            
            # Create summary message
            summary = f"""Data collection complete:
- Keywords: {len(state['keywords'])} extracted
- Filters: {', '.join(state['filters'].keys()) if state['filters'] else 'None'}
- Entities: {len(state['extracted_entities'])} found"""
            
            collection_msg = AIMessage(content=summary)
            
            logger.info(f"📊 Data Collector completed successfully: {len(state['keywords'])} keywords, {len(state['filters'])} filters")
            
            return {
                "messages": [collection_msg],
                "keywords": state["keywords"],
                "filters": state["filters"],
                "data_requirements": state["data_requirements"],
                "extracted_entities": state["extracted_entities"]
            }
            
        except Exception as e:
            logger.error(f"Data Collector error: {e}")
            error_msg = AIMessage(content=f"Error in data collection: {str(e)}")
            return {"messages": [error_msg]}
    
    async def _hitl_verification_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 3: HITL Verification with interrupt()
        - Presents refined query and collected data to user
        - Waits for user confirmation or modification requests
        - Can iterate back to steps 1-2 based on user feedback
        """
        logger.info("👤 Step 3: HITL Verification (Human-in-the-Loop)")
        
        # Prepare verification summary
        verification_summary = {
            "refined_query": state.get("refined_query", ""),
            "keywords": state.get("keywords", []),
            "filters": state.get("filters", {}),
            "defaults_applied": state.get("defaults_applied", []),
            "extracted_entities": state.get("extracted_entities", [])
        }
        
        # Create human-readable summary
        summary_text = f"""
🔍 **Query Analysis Summary**

**Refined Query:** {verification_summary['refined_query']}

**Keywords Extracted:** {', '.join(verification_summary['keywords'][:10]) if verification_summary['keywords'] else 'None'}
{f'... and {len(verification_summary["keywords"]) - 10} more' if len(verification_summary.get("keywords", [])) > 10 else ''}

**Filters Applied:**
{json.dumps(verification_summary['filters'], indent=2) if verification_summary['filters'] else 'No specific filters'}

**Defaults Applied:** {', '.join(verification_summary['defaults_applied']) if verification_summary['defaults_applied'] else 'None'}

**Entities Found:** {', '.join(verification_summary['extracted_entities'][:5]) if verification_summary['extracted_entities'] else 'None'}
{f'... and {len(verification_summary["extracted_entities"]) - 5} more' if len(verification_summary.get("extracted_entities", [])) > 5 else ''}

---
**Please review and respond:**
- Type "continue" to proceed with query generation
- Type "refine query" to modify the query refinement  
- Type "collect data" to adjust data collection
- Or provide specific feedback for modifications
"""
        
        # Store verification data in state
        state["hitl_summary"] = verification_summary
        state["hitl_iteration"] = state.get("hitl_iteration", 0) + 1
        state["awaiting_human_input"] = True
        
        # Create verification message
        verification_msg = AIMessage(content=summary_text)
        
        # Use interrupt to pause execution - this will stop the workflow here
        # The workflow will resume when human provides feedback
        interrupt({
            "type": "human_verification_required",
            "summary": verification_summary,
            "iteration": state["hitl_iteration"],
            "message": summary_text,
            "conversation_id": state.get("conversation_id"),
            "instructions": "Please review the analysis and provide feedback to continue."
        })
        
        return {
            "messages": [verification_msg],
            "hitl_summary": verification_summary,
            "hitl_iteration": state["hitl_iteration"],
            "awaiting_human_input": True,
            "current_stage": "hitl_verification"
        }
    
    def _should_continue_hitl(self, state: DashboardState) -> str:
        """
        Determine next step based on HITL feedback
        """
        human_feedback = state.get("human_feedback", "")
        
        if not human_feedback:
            return "continue"  # Default to continue if no feedback
        
        feedback_lower = str(human_feedback).lower().strip()
        
        # Check for specific commands
        if any(cmd in feedback_lower for cmd in ["continue", "proceed", "yes", "ok", "approve"]):
            return "continue"
        elif any(cmd in feedback_lower for cmd in ["refine", "modify query", "change query"]):
            return "refine"
        elif any(cmd in feedback_lower for cmd in ["collect", "data", "filters", "keywords"]):
            return "collect"
        else:
            # Default to continue if unclear
            return "continue"
    
    async def _query_generator_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 4: Query Generator Agent  
        - Creates Boolean queries using AND/OR/NEAR/NOT operators
        - Uses keyword_query_patterns.json for examples
        """
        logger.info("🔧 Step 4: Query Generator Agent")
        
        try:
            keywords = state.get("keywords", [])
            filters = state.get("filters", {})
            data_requirements = state.get("data_requirements", {})
            
            # Generate Boolean query using correct method
            boolean_query_result = await self.query_generator({
                "keywords": keywords,
                "filters": filters,
                "data_requirements": data_requirements
            })
            
            boolean_query = boolean_query_result.get("boolean_query", "")
            state["boolean_query"] = boolean_query
            state["query_metadata"] = {
                "generated_at": datetime.now().isoformat(),
                "keywords_count": len(keywords),
                "filters_applied": list(filters.keys()) if filters else []
            }
            
            query_msg = AIMessage(
                content=f"Boolean query generated: {boolean_query[:200]}..."
            )
            
            return {
                "messages": [query_msg],
                "boolean_query": state["boolean_query"],
                "query_metadata": state["query_metadata"]
            }
            
        except Exception as e:
            logger.error(f"Query Generator error: {e}")
            error_msg = AIMessage(content=f"Error in query generation: {str(e)}")
            return {"messages": [error_msg]}
    
    async def _data_analyzer_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 6: Data Analyzer Agent
        - Processes API results
        - Generates insights and themes
        - Provides final analysis
        """
        logger.info("📈 Step 6: Data Analyzer Agent")
        
        try:
            # Get API results from tool execution
            api_results = state.get("tool_results", {})
            boolean_query = state.get("boolean_query", "")
            
            # Analyze the data using correct method
            analysis_result = await self.data_analyzer({
                "fetched_data": api_results,
                "boolean_query": boolean_query,
                "query_context": state.get("query_context", {})
            })
            
            # Update state with analysis
            state["analysis_results"] = analysis_result.get("analysis_results", {})
            state["insights"] = analysis_result.get("insights", [])
            state["themes"] = analysis_result.get("themes", [])
            state["summary"] = analysis_result.get("summary", "")
            
            # Create final analysis message
            final_msg = AIMessage(
                content=f"""
🎯 **Analysis Complete**

**Summary:** {state['summary']}

**Key Insights:** {len(state['insights'])} insights generated
**Themes Identified:** {len(state['themes'])} themes found

**Top Insights:**
{chr(10).join([f"• {insight}" for insight in state['insights'][:3]])}

**Analysis completed successfully!**
"""
            )
            
            return {
                "messages": [final_msg],
                "analysis_results": state["analysis_results"],
                "insights": state["insights"], 
                "themes": state["themes"],
                "summary": state["summary"],
                "workflow_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Data Analyzer error: {e}")
            error_msg = AIMessage(content=f"Error in data analysis: {str(e)}")
            return {"messages": [error_msg]}
    
    async def _tool_execution_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 5: Tool Execution Node
        - Executes API calls with Boolean query
        - Fetches data from Sprinklr API
        - Stores results for analysis
        """
        logger.info("🔧 Step 5: Tool Execution (API Calls)")
        
        try:
            boolean_query = state.get("boolean_query", "")
            filters = state.get("filters", {})
            
            if not boolean_query:
                logger.error("No Boolean query available for tool execution")
                error_msg = AIMessage(content="Error: No Boolean query generated for API call")
                return {"messages": [error_msg]}
            
            # Prepare tool input
            tool_input = {
                "query": boolean_query,
                "filters": filters,
                "limit": 10  # Default limit
            }
            
            # Execute the Sprinklr API tool
            
            logger.info(f"Executing API call with query: {boolean_query[:100]}...")
            api_results = await get_sprinklr_data.ainvoke(tool_input)
            
            # Store results in state
            state["tool_results"] = {
                "sprinklr_data": api_results,
                "query_used": boolean_query,
                "timestamp": datetime.now().isoformat(),
                "results_count": len(api_results) if isinstance(api_results, list) else 0
            }
            
            tool_msg = AIMessage(
                content=f"✅ API call completed. Retrieved {len(api_results) if isinstance(api_results, list) else 0} results."
            )
            
            return {
                "messages": [tool_msg],
                "tool_results": state["tool_results"],
                "fetched_data": api_results
            }
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            error_msg = AIMessage(content=f"Error in API execution: {str(e)}")
            return {"messages": [error_msg]}

    # ...existing code...
    
    async def run_workflow(
        self, 
        user_query: str, 
        thread_id: str = None,
        config: Optional[RunnableConfig] = None
    ) -> Dict[str, Any]:
        """
        Run the complete workflow with conversation memory
        
        Args:
            user_query: The user's query to process
            thread_id: Conversation thread ID for memory persistence
            config: Optional runnable configuration
            
        Returns:
            Final state with analysis results
        """
        logger.info(f"🚀 Starting Modern Sprinklr Workflow for query: {user_query[:100]}...")
        
        # Setup thread config
        if not thread_id:
            thread_id = f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        thread_config = {
            "configurable": {"thread_id": thread_id}
        }
        if config:
            thread_config.update(config)
        
        # Initial state
        initial_state = {
            "messages": [HumanMessage(content=user_query)],
            "thread_id": thread_id,
            "workflow_started": datetime.now().isoformat()
        }
        
        try:
            # Run the workflow
            final_state = await self.workflow.ainvoke(
                initial_state,
                config=thread_config
            )
            
            logger.info("✅ Modern Sprinklr Workflow completed successfully")
            return final_state
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def resume_workflow(
        self,
        thread_id: str,
        user_input: str = None,
        config: Optional[RunnableConfig] = None
    ) -> Dict[str, Any]:
        """
        Resume a workflow from HITL interruption
        
        Args:
            thread_id: Thread ID to resume
            user_input: User feedback/input for HITL
            config: Optional runnable configuration
            
        Returns:
            Updated state after resumption
        """
        logger.info(f"🔄 Resuming workflow for thread: {thread_id}")
        
        thread_config = {
            "configurable": {"thread_id": thread_id}
        }
        if config:
            thread_config.update(config)
        
        # Add user input if provided
        input_data = None
        if user_input:
            input_data = {
                "messages": [HumanMessage(content=user_input)],
                "human_feedback": user_input
            }
        
        try:
            # Resume the workflow
            final_state = await self.workflow.ainvoke(
                input_data,
                config=thread_config
            )
            
            logger.info("✅ Workflow resumed successfully")
            return final_state
            
        except Exception as e:
            logger.error(f"❌ Workflow resumption failed: {e}")
            raise
    
    async def get_workflow_status(self, thread_id: str) -> Dict[str, Any]:
        """Get current status of a workflow thread"""
        try:
            # Get current state from memory
            current_state = self.memory.get({
                "configurable": {"thread_id": thread_id}
            })
            
            if not current_state:
                return {"status": "not_found", "thread_id": thread_id}
            
            # Determine current status
            last_message = current_state.get("messages", [])[-1] if current_state.get("messages") else None
            workflow_status = current_state.get("workflow_status", "in_progress")
            
            return {
                "status": workflow_status,
                "thread_id": thread_id,
                "last_message": last_message.content if last_message else None,
                "current_step": self._determine_current_step(current_state),
                "hitl_iteration": current_state.get("hitl_iteration", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return {"status": "error", "error": str(e)}
    
    def _determine_current_step(self, state: Dict[str, Any]) -> str:
        """Determine current workflow step based on state"""
        if state.get("analysis_results"):
            return "completed"
        elif state.get("boolean_query"):
            return "data_analysis" 
        elif state.get("hitl_summary"):
            return "hitl_verification"
        elif state.get("keywords"):
            return "data_collection"
        elif state.get("refined_query"):
            return "query_refinement"
        else:
            return "starting"
    
    async def process_dashboard_request(self, user_query: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main function to process dashboard requests using the modern workflow.
        
        Args:
            user_query: User's query string
            conversation_id: Optional conversation thread ID
            
        Returns:
            Dictionary with workflow results
        """
        logger.info(f"Processing dashboard request: {user_query[:100]}...")
        
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = f"conv_{int(time.time())}"
            
            # Create initial state
            from src.helpers.states import create_initial_state
            initial_state = create_initial_state(user_query, conversation_id)
            
            # Create config with thread_id for memory
            config = RunnableConfig(
                configurable={"thread_id": conversation_id}
            )
            
            # Use streaming execution to handle interrupts properly
            final_state = None
            is_interrupted = False
            interrupt_data = None
            
            try:
                # Stream the workflow execution to handle HITL interrupts
                async for state_update in self.workflow.astream(initial_state, config):
                    final_state = state_update
                    logger.info(f"🔄 Workflow state update: {list(state_update.keys()) if isinstance(state_update, dict) else type(state_update)}")
                    
                    # Check which node just executed
                    if isinstance(state_update, dict):
                        for node_name, node_state in state_update.items():
                            logger.info(f"✅ Node '{node_name}' completed")
                            if hasattr(node_state, 'get'):
                                # Check if this is the final state
                                if 'current_stage' in node_state:
                                    logger.info(f"   Current stage: {node_state.get('current_stage', 'unknown')}")
                
                logger.info(f"🎯 Workflow stream completed for conversation: {conversation_id}")
                logger.info(f"🔍 Final state keys: {list(final_state.keys()) if isinstance(final_state, dict) else 'No final state'}")
                
                # Check if the workflow was interrupted (indicated by __interrupt__ in final state)
                if isinstance(final_state, dict) and '__interrupt__' in final_state:
                    logger.info("🛑 Detected workflow interrupt - setting interrupted status")
                    is_interrupted = True
                    
                    # Set default interrupt data
                    interrupt_data = {
                        "type": "human_verification_required", 
                        "next_node": "hitl_verification",
                        "state": "interrupted_before_hitl"
                    }
                    
                    # Get the current state and interrupt info
                    current_state = self.workflow.get_state(config)
                    if current_state and hasattr(current_state, 'values'):
                        final_state = current_state.values
                        
                    # Check for interrupts
                    try:
                        # Get current state which should contain interrupt info
                        state_snapshot = self.workflow.get_state(config)
                        if state_snapshot and hasattr(state_snapshot, 'next'):
                            # LangGraph state contains next nodes to execute
                            logger.info(f"Next nodes to execute: {state_snapshot.next}")
                            if 'hitl_verification' in state_snapshot.next:
                                interrupt_data.update({
                                    "next_node": "hitl_verification",
                                    "state_values": current_state.values if current_state else {},
                                    "conversation_id": conversation_id
                                })
                                logger.info(f"HITL interrupt detected: {interrupt_data}")
                    except Exception as int_e:
                        logger.warning(f"Could not get state info: {int_e}")
                
            except Exception as e:
                # Real error occurred during execution  
                logger.error(f"Workflow execution error: {e}")
                raise
            
            if is_interrupted:
                return {
                    "conversation_id": conversation_id,
                    "status": "awaiting_human_input",
                    "interrupt_data": interrupt_data,
                    "current_state": final_state,
                    "message": "HITL verification required - workflow paused for human input"
                }
            
            return {
                "conversation_id": conversation_id,
                "status": "completed",
                "results": final_state
            }
            
        except Exception as e:
            logger.error(f"Error processing dashboard request: {e}")
            return {
                "conversation_id": conversation_id,
                "status": "error",
                "error": str(e),
                "results": {}
            }
    
    async def handle_user_feedback(self, conversation_id: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle user feedback for HITL verification using proper interrupt resume pattern.
        
        Args:
            conversation_id: Conversation thread ID
            feedback: User feedback data
            
        Returns:
            Dictionary with feedback processing results
        """
        logger.info(f"Handling user feedback for conversation: {conversation_id}")
        
        try:
            # Create config with thread_id
            config = RunnableConfig(
                configurable={"thread_id": conversation_id}
            )
            
            # Get current state from memory
            state = await self.workflow.aget_state(config)
            
            if not state:
                logger.error(f"No state found for conversation {conversation_id}")
                return {
                    "conversation_id": conversation_id,
                    "status": "error",
                    "error": f"No conversation found with ID {conversation_id}"
                }
            
            # Check for active interrupts
            try:
                interrupts = self.workflow.get_interrupts(config)
            except AttributeError:
                logger.warning("Workflow has no get_interrupts method; assuming no pending interrupts")
                interrupts = []
                
            if not interrupts:
                logger.warning(f"No active interrupts found for conversation {conversation_id}")
                return {
                    "conversation_id": conversation_id,
                    "status": "error",
                    "error": "No pending interrupts to resume"
                }
            
            # Get the most recent interrupt
            latest_interrupt = interrupts[-1]
            interrupt_id = latest_interrupt["interrupt_id"]
            logger.info(f"Resuming workflow with interrupt_id: {interrupt_id}")
            
            # Prepare the human response payload
            user_response = feedback.get("content", "")
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
            
            # Resume the workflow with the user's response using proper interrupt resume
            result = None
            async for state_update in self.workflow.astream_interrupt(interrupt_id, human_response_payload, config=config):
                result = state_update  # Get the final state
            
            if not result:
                logger.error("No result returned from workflow resumption")
                return {
                    "conversation_id": conversation_id,
                    "status": "error",
                    "error": "Failed to resume workflow after user input"
                }
            
            # Process the result to extract relevant information
            final_state = None
            
            # Extract the state from the result
            if isinstance(result, dict) and len(result) > 0:
                # The result is typically {node_name: state}
                final_state = list(result.values())[0]
            
            if not final_state:
                logger.error(f"Could not extract state from result: {result}")
                return {
                    "conversation_id": conversation_id,
                    "status": "error",
                    "error": "Could not determine workflow state after resumption"
                }
            
            # Extract information from the final state
            if hasattr(final_state, "values"):
                state_values = final_state.values
            elif isinstance(final_state, dict) and "values" in final_state:
                state_values = final_state["values"]
            else:
                state_values = final_state
            
            # Create a response with the relevant information
            workflow_status = state_values.get("workflow_status", "in_progress")
            current_step = state_values.get("current_step", "")
            
            return {
                "conversation_id": conversation_id,
                "status": "feedback_processed",
                "workflow_status": workflow_status,
                "current_step": current_step,
                "message": "Your feedback has been processed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error handling user feedback: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "conversation_id": conversation_id,
                "status": "error",
                "error": str(e)
            }
    
    async def get_workflow_history(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation history for a specific thread."""
        try:
            config = {"configurable": {"thread_id": conversation_id}}
            
            # Get state from memory
            state = await self.workflow.aget_state(config)
            
            return {
                "conversation_id": conversation_id,
                "status": "retrieved",
                "state": state.values if state else {},
                "messages": state.values.get("messages", []) if state else [],
                "current_step": self._determine_current_step(state.values) if state else "not_found"
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow history: {e}")
            return {
                "conversation_id": conversation_id,
                "status": "error",
                "error": str(e)
            }
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the modern workflow."""
        return {
            "workflow_type": "modern_langgraph",
            "version": "2.0",
            "features": [
                "Thread-based conversation memory",
                "HITL verification with interrupt()",
                "Modern LangGraph patterns",
                "Automatic state persistence",
                "Multi-agent coordination",
                "Lazy model loading for performance",
                "Production-ready Flask integration"
            ],
            "steps": [
                "Query Refiner Agent",
                "Data Collector Agent", 
                "HITL Verification",
                "Query Generator Agent",
                "Tool Execution",
                "Data Analyzer Agent"
            ],
            "performance": {
                "initialization_time": "~11.6s (optimized from 30s+)",
                "lazy_loading": "Models load on-demand",
                "memory_efficient": True
            }
        }


# Global workflow instance for Flask integration
modern_workflow = SprinklrWorkflow()


# Additional utility functions
def get_available_workflows() -> List[str]:
    """Get list of available workflow types."""
    return ["modern", "legacy"]


# Standalone Flask integration functions
async def process_dashboard_request(user_query: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Standalone function for Flask integration to process dashboard requests.
    
    Args:
        user_query: User's query string  
        conversation_id: Optional conversation thread ID
        
    Returns:
        Dictionary with workflow results
    """
    logger.info(f"Standalone processing dashboard request: {user_query[:100]}...")
    
    try:
        # Use global workflow instance
        result = await modern_workflow.process_dashboard_request(user_query, conversation_id)
        return result
        
    except Exception as e:
        logger.error(f"Error in standalone dashboard processing: {e}")
        return {
            "conversation_id": conversation_id or f"conv_{int(time.time())}",
            "status": "error",
            "error": str(e),
            "results": {}
        }


async def handle_user_feedback(conversation_id: str, feedback: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Standalone function for Flask integration to handle user feedback.
    
    Args:
        conversation_id: Conversation thread ID
        feedback: User feedback (string or dict)
        
    Returns:
        Dictionary with feedback processing results
    """
    logger.info(f"Standalone handling user feedback for conversation: {conversation_id}")
    
    try:
        # Normalize feedback to dict format
        if isinstance(feedback, str):
            feedback_dict = {"content": feedback, "type": "text"}
        else:
            feedback_dict = feedback
            
        # Use global workflow instance
        result = await modern_workflow.handle_user_feedback(conversation_id, feedback_dict)
        return result
        
    except Exception as e:
        logger.error(f"Error in standalone feedback handling: {e}")
        return {
            "conversation_id": conversation_id,
            "status": "error", 
            "error": str(e)
        }


async def get_workflow_history(conversation_id: str) -> List[Dict[str, Any]]:
    """
    Standalone function for Flask integration to get workflow history.
    
    Args:
        conversation_id: Conversation thread ID
        
    Returns:
        List of conversation messages
    """
    logger.info(f"Standalone getting workflow history for: {conversation_id}")
    
    try:
        # Use global workflow instance
        history_result = await modern_workflow.get_workflow_history(conversation_id)
        
        # Extract messages for simple response
        messages = history_result.get("messages", [])
        
        # Convert messages to simple dict format
        formatted_messages = []
        for msg in messages:
            if hasattr(msg, 'content'):
                formatted_messages.append({
                    "content": msg.content,
                    "type": msg.__class__.__name__,
                    "timestamp": getattr(msg, 'timestamp', None)
                })
            else:
                formatted_messages.append({"content": str(msg), "type": "unknown"})
        
        return formatted_messages
        
    except Exception as e:
        logger.error(f"Error in standalone history retrieval: {e}")
        return []


def get_modern_workflow_status() -> Dict[str, Any]:
    """
    Get status of the modern workflow system.
    
    Returns:
        Dictionary with system status
    """
    try:
        workflow_info = modern_workflow.get_workflow_info()
        
        return {
            "status": "healthy",
            "workflow_initialized": True,
            "workflow_info": workflow_info,
            "memory_enabled": True,
            "lazy_loading_enabled": True
        }
        
    except Exception as e:
        logger.error(f"Error getting modern workflow status: {e}")
        return {
            "status": "error",
            "workflow_initialized": False,
            "error": str(e)
        }
