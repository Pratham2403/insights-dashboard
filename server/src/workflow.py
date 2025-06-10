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
from langgraph.types import interrupt, Command


# Import our components
from src.config.settings import settings
from src.helpers.states import DashboardState, create_initial_state
from src.setup.llm_setup import LLMSetup
from src.tools.get_tool import get_sprinklr_data
from src.agents.query_refiner_agent import QueryRefinerAgent
from src.agents.data_collector_agent import DataCollectorAgent
from src.agents.data_analyzer_agent2 import DataAnalyzerAgent
from src.agents.query_generator_agent import  QueryGeneratorAgent
from src.utils.hitl_detection import detect_approval_intent, determine_hitl_action
# from src.persistence.mongodb_checkpointer import MongoDBPersistenceManager



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
        """Initialize the workflow with all components"""
        logger.info("Initializing Modern Sprinklr Workflow...")
        
        # Setup LLM
        self.llm_setup = LLMSetup()
        self.llm = self.llm_setup.get_agent_llm("workflow")
        
        # Initialize agents
        self.query_refiner = QueryRefinerAgent(self.llm)
        self.data_collector = DataCollectorAgent(self.llm)
        self.data_analyzer = DataAnalyzerAgent(self.llm) 
        self.query_generator = QueryGeneratorAgent(self.llm)
        
        # Setup tools
        self.tools = [get_sprinklr_data]
        self.tool_node = ToolNode(self.tools)
        
        # Memory management
        self.memory = MemorySaver()
        
        # Initialize current hits storage (separate from state to prevent memory explosion)
        self._current_hits = []
        
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
        
        # HITL verification can loop back or continue - following helper_hitl_demo_code.py pattern
        workflow.add_conditional_edges(
            "hitl_verification",
            self._should_continue_hitl,
            {
                "continue": "query_generator",
                "refine": "query_refiner"
            }
        )
        
        workflow.add_edge("query_generator", "tools")
        workflow.add_edge("tools", "data_analyzer")
        workflow.add_edge("data_analyzer", END)
        
        # Compile with memory - using helper demo pattern
        compiled_workflow = workflow.compile(
            checkpointer=self.memory
        )
        
        logger.info("📋 Workflow compiled with memory checkpointer")
        logger.info(f"📊 Workflow nodes: {list(workflow.nodes.keys()) if hasattr(workflow, 'nodes') else 'Unknown'}")
        
        return compiled_workflow
    
    def _log_state_debug(self, stage: str, state: DashboardState):
        """
        Log the entire state as model_dump() for debugging purposes as per requirements.
        This logs the multi_agent_system_project_state structure from PROMPT.md
        """
        logger.info(f"🔍 ========== {stage.upper()} - COMPLETE STATE DUMP ==========")
        
        # Create state dict matching PROMPT.md structure exactly
        multi_agent_system_project_state = {
            "query": state.get("query", []),
            "refined_query": state.get("refined_query", ""),
            "keywords": state.get("keywords", []),
            "filters": state.get("filters", {}),
            "boolean_query": state.get("boolean_query", ""),
            "themes": state.get("themes", [])
        }
        
        # Log query list details for debugging
        query_list = state.get("query", [])
        logger.info(f"📝 Query List Summary: {len(query_list)} total queries")
        for i, query in enumerate(query_list):
            logger.info(f"   Query {i+1}: {query[:100]}...")
        
        # Log the complete state dump as simple JSON (no beautification)
        logger.info(f"STATE_DUMP: {json.dumps(multi_agent_system_project_state, default=str)}")
        logger.info(f"🔍 ========== END {stage.upper()} STATE DUMP ==========\n")

    async def _query_refiner_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 1: Query Refiner Agent
        - Uses completeUseCase.txt for context
        - Handles conversation context intelligently
        """
        logger.info("🔍 Step 1: Query Refiner Agent")
        
        # Log state BEFORE processing
        self._log_state_debug("QUERY_REFINER_BEFORE", state)
        
        try:
            # Get the current query list from state
            query_list = state.get("query", [])
            
            if not query_list:
                logger.error("No query list found in state")
                return {"error": "No query list provided"}
            
            logger.info(f"🔍 Processing query list with {len(query_list)} queries: {query_list}")
            
            # Process with query refiner - pass the entire state
            refined_result = await self.query_refiner(state)
            # Extract refinement data

            query_refinement = refined_result.get("query_refinement", {})
            
            if "error" in query_refinement:
                logger.error(f"Query refinement error: {query_refinement['error']}")
                error_msg = AIMessage(content=f"Error in query refinement: {query_refinement['error']}")
                return {"messages": [error_msg], "errors": [query_refinement["error"]]}
            
            # Update state following PROMPT.md structure
            refined_query = query_refinement.get("refined_query", "")
            
            if not refined_query:
                logger.error("No refined query received from agent")
                error_msg = AIMessage(content="No refined query generated")
                return {"messages": [error_msg], "errors": ["No refined query generated"]}
            
            # Add system message about refinement
            refinement_msg = AIMessage(
                content=f"Query refined with context: {refined_query}"
            )
            
            result = {
                "refined_query": refined_query,  # New or updated refined query
                "data_requirements": query_refinement.get("data_requirements", []),
                "messages": [refinement_msg],
                "current_stage": "query_refined"
            }
            # Log state AFTER processing
            self._log_state_debug("QUERY_REFINER_AFTER", {**state, **result})
            
            return result
            
        except Exception as e:
            logger.error(f"Query Refiner error: {e}")
            error_msg = AIMessage(content=f"Error in query refinement: {str(e)}")
            return {"messages": [error_msg], "errors": [str(e)]}
    
    async def _data_collector_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 2: Data Collector Agent
        - Extracts relevant data from refined query
        - Uses filters.json for filter options
        - Creates keywords and filters lists
        """
        logger.info("📊 Step 2: Data Collector Agent")
        # Log state BEFORE processing
        self._log_state_debug("DATA_COLLECTOR_BEFORE", state)
        
        try:
            refined_query = state.get("refined_query", state.get("query")[-1])
            
            if not refined_query:
                logger.error("No refined query found in state")
            
            # Process with data collector - pass the full state
            collection_result = await self.data_collector({
                **state,
                "refined_query": refined_query
            })

            keywords = collection_result.get("keywords", [])
            filters = collection_result.get("filters", {})
            
            # Create summary message
            summary = f"""Data collection complete:
            - Keywords: {len(keywords)} extracted
            - Filters: {', '.join(filters.keys()) if filters else 'None'}"""
            
            collection_msg = AIMessage(content=summary)
            
            logger.info(f"📊 Data Collector completed successfully: {len(keywords)} keywords, {len(filters)} filters")
            
            result = {
                "keywords": keywords,
                "filters": filters,
                "messages": [collection_msg],
                "current_stage": "data_collected",
                "hitl_step": 1  # Set initial HITL step for verification
            }
            
            # Log state AFTER processing
            self._log_state_debug("DATA_COLLECTOR_AFTER", {**state, **result})
            
            return result
            
        except Exception as e:
            logger.error(f"Data Collector error: {e}")
            error_msg = AIMessage(content=f"Error in data collection: {str(e)}")
            return {"messages": [error_msg]}
    
    async def _hitl_verification_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 3: Mandatory HITL Verification - Following helper_hitl_demo_code.py pattern
        - Implements step-based HITL logic for progressive interaction
        - Uses interrupt() for each step to pause execution
        - Routes correctly based on HITL step progression
        
        FIXED: Prevents loop conditions by properly segregating user responses:
        - Clear approval ("yes") → Proceed to Boolean Query Generator
        - Clarifications/new requirements → Treat as fresh user input (no duplication)
        """
        logger.info("👤 Step 3: Mandatory HITL Verification (Human-in-the-Loop)")
        
        # Log state BEFORE processing
        self._log_state_debug("HITL_VERIFICATION_BEFORE", state)
        
        # Get HITL step - following helper_hitl_demo_code.py pattern
        step = state.get("hitl_step", 1)  # Default to step 1 for normal verification
        logger.info(f"🔢 HITL Step: {step}")
        
        # For normal workflows, we start at step 1 (verification)
        # Step 0 is only used when clarification is explicitly needed
        if step == 0 and state.get("reason") != "clarification_needed":
            step = 1
            logger.info("🔢 Adjusted HITL step from 0 to 1 for normal verification")
        
        # Step 0: Initial clarification check (trigger HITL when clarification needed)
        if step == 0 and state.get("reason") == "clarification_needed":
            logger.info("🚨 Step 0: Clarification needed - requesting details")
            
            # Trigger interrupt for user input
            interrupt({
                "question": "Please provide more details to clarify your query.",
                "step": 0,
                "current_state": state
            })
            
            # Return state update for step transition
            return {"hitl_step": 1}
            
        # Step 1: Main verification - show user the analysis and ask for approval  
        elif step == 1:
            logger.info("✏️ Step 1: Main verification - requesting user approval")
            
            # Prepare verification data to show the user
            refined_query = state.get("refined_query", "")
            keywords = state.get("keywords", [])
            filters = state.get("filters", {})
            
            verification_data = {
                "question": "Please review the analysis below and approve to continue:",
                "step": 1,
                "refined_query": refined_query,
                "keywords": keywords[:5],  # Show first 5 keywords
                "filters": filters,
                "instructions": "Reply 'yes' to approve or provide feedback to refine"
            }
            
            # Use interrupt to capture user input
            user_response = interrupt(verification_data)
            
            # Process the user response directly after interrupt
            logger.info(f"📝 Processing user response: '{user_response}'")
            
            # Use dynamic positive and negative analysis from our system
            approval_analysis = detect_approval_intent(user_response)
            logger.info(f"🤖 Dynamic Analysis Result: {approval_analysis}")
            
            # Process response based on analysis (following helper_hitl_demo_code.py pattern)
            if approval_analysis["is_approval"] and approval_analysis["confidence"] in ["high", "medium"]:
                logger.info(f"✅ Approval detected - proceeding to query generator without modifying query")
                return {
                    "hitl_step": 0,  # Reset for next time
                    "next_node": "query_generator"  # Set explicit routing to query generator
                }
            else:
                logger.info(f"❌ User provided clarification/new requirements - treating as fresh user input")
                
                # For clarifications/new requirements, replace the original query entirely
                # This prevents duplication and loop conditions
                return {
                    "query": [user_response],  # Replace with fresh user input as list
                    "hitl_step": 0,  # Reset for next iteration
                    "next_node": "query_refiner",  # Route to query refiner for fresh processing
                    "current_stage": "query_received"  # Reset stage to start fresh
                }
        
        # Step 3: Process additional information and route back to refiner
        elif step == 3:
            logger.info("🔄 Step 3: Processing additional input - routing back to query refiner")
            
            # Get additional input following helper_hitl_demo_code.py pattern
            query_list = state.get("query", [])
            if isinstance(query_list, str):
                additional_input = query_list
            elif isinstance(query_list, list) and len(query_list) > 1:
                additional_input = query_list[-1]  # Get latest input
            else:
                additional_input = ""
            
            logger.info(f"📝 Processing additional input: '{additional_input}'")
            
            # Return state update for routing back to query refiner
            return {
                "next_node": "query_refiner",  # Match helper_hitl_demo_code.py
                "hitl_step": 0  # Reset for next iteration
            }
        
        # Default case - should not reach here in normal operation
        else:
            logger.warning(f"⚠️ Unexpected HITL step: {step}, using default verification")
            
            # Trigger interrupt for clarification
            interrupt({
                "question": "Please review the query analysis and provide feedback to continue.",
                "step": "default",
                "unexpected_step": step
            })
            
            # Reset to step 1 and request clarification
            return {"hitl_step": 1}
    
    def _should_continue_hitl(self, state: DashboardState) -> str : 
        """
        Decision logic for HITL workflow routing following helper_hitl_demo_code.py pattern.
        Routes based on next_node field set by HITL verification node.
        
        Returns:
        - "continue": Proceed to Boolean Query Generator (with explicit approval) 
        - "refine": Go back to Query Refiner Agent
        """
        logger.info(f"🔀 HITL Routing Decision - State: {state.get('current_stage', 'unknown')}")
        
        # Check if HITL node set explicit routing via next_node (helper_hitl_demo_code.py pattern)
        next_node = state.get("next_node")
        if next_node:
            logger.info(f"🎯 Explicit routing from HITL: {next_node}")
            
            if next_node == "query_generator":
                logger.info("✅ Routing to query_generator - user approved")
                return "continue"
            elif next_node == "query_refiner":
                logger.info("🔄 Routing to query_refiner - user provided clarification/new requirements")
                return "refine"
        
        # If no explicit routing, this is an error state - default to refine
        logger.warning("⚠️ No explicit routing found from HITL node - defaulting to refine for safety")
        return "refine"
    


    async def _query_generator_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 4: Query Generator Agent  
        - Creates Boolean queries using AND/OR/NEAR/NOT operators
        - Uses keyword_query_patterns.json for examples
        """
        logger.info("🔧 Step 4: Query Generator Agent")
        
        # Log state BEFORE processing
        self._log_state_debug("QUERY_GENERATOR_BEFORE", state)
        
        try:
            keywords = state.get("keywords", [])
            filters = state.get("filters", {})
            refined_query = state.get("refined_query", "")
            
            logger.info(f"🔗 Boolean query generation starting with {len(keywords)} keywords")
            
            # Generate Boolean query using correct method
            boolean_query_result = await self.query_generator({
                "refined_query": refined_query,
                "keywords": keywords,
                "filters": filters,
            })
            
            boolean_query = boolean_query_result.get("boolean_query", "")
            
            # Ensure boolean_query is generated
            if not boolean_query and keywords:
                # Fallback boolean query generation
                boolean_query = " AND ".join([f'"{keyword}"' for keyword in keywords[:5]])
                logger.info(f"🔗 Generated fallback Boolean query: {boolean_query}")
            
            query_metadata = {
                "generated_at": datetime.now().isoformat(),
                "keywords_count": len(keywords),
                "filters_applied": list(filters.keys()) if filters else []
            }
            
            query_msg = AIMessage(
                content=f"Boolean query generated: {boolean_query[:200]}..."
            )
            
            logger.info(f"🔗 Boolean query generated successfully: {boolean_query[:100]}...")
            
            result = {
                "messages": [query_msg],
                "boolean_query": boolean_query,
                "query_metadata": query_metadata,
                "current_stage": "boolean_query_generated"
            }
            
            # Log state AFTER processing
            self._log_state_debug("QUERY_GENERATOR_AFTER", {**state, **result})
            
            return result
            
        except Exception as e:
            logger.error(f"Query Generator error: {e}")
            # Generate simple fallback query to ensure workflow continues
            keywords = state.get("keywords", [])
            if keywords:
                fallback_query = " AND ".join([f'"{keyword}"' for keyword in keywords[:3]])
                logger.info(f"🔗 Generated emergency fallback query: {fallback_query}")
                return {
                    "boolean_query": fallback_query,
                    "messages": [AIMessage(content=f"Fallback query generated: {fallback_query}")],
                    "current_stage": "boolean_query_generated"
                }
            else:
                error_msg = AIMessage(content=f"Error in query generation: {str(e)}")
                return {"messages": [error_msg], "errors": [str(e)]}

    async def _tool_execution_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 5: Tool Execution (ToolNode)
        - Executes the Boolean query via Sprinklr API
        - Returns relevant posts/comments data
        - IMPORTANT: Does NOT store hits in state to prevent memory explosion
        """
        logger.info("🛠️ Step 5: Tool Execution")
        
        # Log state BEFORE processing
        self._log_state_debug("TOOL_EXECUTION_BEFORE", state)
        
        try:
            boolean_query = state.get("boolean_query", "")
            
            if not boolean_query:
                logger.error("No Boolean query found for tool execution")
                error_msg = AIMessage(content="Error: No Boolean query available for data retrieval")
                return {"messages": [error_msg]}
            

            logger.info(f"🛠️ Executing tool with Boolean query: {boolean_query[:100]}...")
            
            # Execute the get_sprinklr_data tool using the invoke method (modern LangChain pattern)
            hits = await get_sprinklr_data.ainvoke({"query": boolean_query, "limit": 500})
            
            logger.info(f"🛠️ Retrieved {len(hits)} hits from Sprinklr API")
            
            # Store hits temporarily in workflow instance (NOT in state)
            # This prevents memory explosion in LangGraph state
            self._current_hits = hits
            
            tool_msg = AIMessage(
                content=f"Tool execution completed: Retrieved {len(hits)} hits from Sprinklr API"
            )
            
            result = {
                "messages": [tool_msg],
                "hits_count": len(hits),  # Store only count, not actual hits
                "tool_execution_completed": True
            }
            
            # Log state AFTER processing (without hits to prevent log explosion)
            self._log_state_debug("TOOL_EXECUTION_AFTER", {**state, **result})
            
            return result
            
        except Exception as e:
            logger.error(f"Tool Execution error: {e}")
            error_msg = AIMessage(content=f"Error in tool execution: {str(e)}")
            return {"messages": [error_msg]}

    async def _data_analyzer_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 6: Data Analyzer Agent
        - Gets hits from workflow instance (NOT from state) to prevent memory explosion
        - Processes hits using BERTopic theme analysis
        - Updates themes in state and returns final results
        """
        logger.info("📈 Step 6: Data Analyzer Agent")
        
        # Log state BEFORE processing
        self._log_state_debug("DATA_ANALYZER_BEFORE", state)
        
        try:
            # Get hits from workflow instance (NOT from state) to prevent memory explosion
            hits = getattr(self, '_current_hits', [])
            
            if not hits:
                logger.warning("No hits found in workflow instance - returning empty themes")
                analysis_msg = AIMessage(content="No data available for analysis")
                return {
                    "messages": [analysis_msg],
                    "themes": [],
                    "workflow_status": "completed",
                    "completed_at": datetime.now().isoformat()
                }
            
            # Pass hits and state separately to data analyzer (as per requirement)
            # The hits are NOT stored in LangGraph state to prevent memory explosion
            logger.info(f"🔍 Processing {len(hits)} hits with Data Analyzer Agent...")
            
            # Call data analyzer with hits and state separately
            themes_result = await self.data_analyzer.analyze_hits_and_state(
                hits=hits,     # Hits passed separately (NOT stored in state)
                state=state    # LangGraph state passed separately
            )
            
            # Extract themes from result
            themes = themes_result.get("themes", [])
            
            # Clear hits from workflow instance to free memory
            if hasattr(self, '_current_hits'):
                delattr(self, '_current_hits')
            
            analysis_msg = AIMessage(
                content=f"Analysis completed: Generated {len(themes)} themes from {len(hits)} hits"
            )
            
            result = {
                "messages": [analysis_msg],
                "themes": themes,  # Update themes state as per requirement
                "workflow_status": "completed",
                "completed_at": datetime.now().isoformat()
            }
            
            # Log state AFTER processing
            self._log_state_debug("DATA_ANALYZER_AFTER", {**state, **result})
            
            return result
            
        except Exception as e:
            logger.error(f"Data Analyzer error: {e}")
            # Clear hits from workflow instance even on error
            if hasattr(self, '_current_hits'):
                delattr(self, '_current_hits')
            error_msg = AIMessage(content=f"Error in data analysis: {str(e)}")
            return {
                "messages": [error_msg],
                "themes": [],
                "workflow_status": "error",
                "completed_at": datetime.now().isoformat(),
                "errors": [str(e)]
            }

    def _serialize_state_for_json(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize state for JSON response following PROMPT.md structure exactly.
        Returns only the core multi_agent_system_project_state fields as defined in PROMPT.md.
        
        This ensures we avoid duplicating data in the API response.
        """
        if not state:
            return {
                "query": [],
                "refined_query": None,
                "keywords": None,
                "filters": None,
                "boolean_query": None,
                "themes": None
            }
        
        # Create a clean dictionary matching PROMPT.md structure exactly
        # Use comprehensive serialization to handle any nested AIMessage objects
        serialized_state = {
            "query": self._serialize_for_json_comprehensive(state.get("query", [])),
            "refined_query": self._serialize_for_json_comprehensive(state.get("refined_query")),
            "keywords": self._serialize_for_json_comprehensive(state.get("keywords", [])),
            "filters": self._serialize_for_json_comprehensive(state.get("filters", {})),
            "boolean_query": self._serialize_for_json_comprehensive(state.get("boolean_query", "")),
            "themes": self._serialize_for_json_comprehensive(state.get("themes", []))
        }
        
        # Log the exact format of the serialized state for debugging
        logger.info(f"STATE_DUMP: {json.dumps(serialized_state, default=str)}")
        
        return serialized_state

    def _serialize_for_json_comprehensive(self, data: Any) -> Any:
        """
        Comprehensive serialization that handles AIMessage objects and other non-serializable types.
        
        Args:
            data: Data to serialize (can be dict, list, or any type)
            
        Returns:
            JSON-serializable version of the data
        """
        from langchain_core.messages import BaseMessage
        
        if isinstance(data, dict):
            return {key: self._serialize_for_json_comprehensive(value) for key, value in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._serialize_for_json_comprehensive(item) for item in data]
        elif isinstance(data, BaseMessage):
            # Convert LangChain messages to serializable format
            return {
                "type": data.__class__.__name__,
                "content": str(data.content),
                "role": getattr(data, 'role', 'unknown')
            }
        elif hasattr(data, '__dict__'):
            # Handle objects with __dict__ (like custom classes)
            try:
                return str(data)
            except Exception:
                return f"<{data.__class__.__name__}>"
        else:
            # For primitive types and other serializable types
            try:
                import json
                json.dumps(data)  # Test if it's serializable
                return data
            except (TypeError, ValueError):
                return str(data)

    async def run_workflow(
        self, 
        user_query: str, 
        thread_id: str = None,
        config: Optional[RunnableConfig] = None
    ) -> Dict[str, Any]:
        """
        Run the complete workflow with conversation memory following helper_hitl_demo_code.py pattern
        
        Args:
            user_query: The user's query to process
            thread_id: Conversation ID for memory persistence
            config: Optional runnable configuration
            
        Returns:
            Final state with analysis results
        """
        logger.info(f"🚀 Starting Modern Sprinklr Workflow for query: {user_query[:100]}...")
        
        # Setup thread config following helper pattern
        if not thread_id:
            import uuid
            thread_id = str(uuid.uuid4())
            logger.info(f"🆕 Generated new thread ID: {thread_id}")
            
        thread_config = {"configurable": {"thread_id": thread_id}}
        if config:
            thread_config.update(config)
        
        try:
            # Follow helper_hitl_demo_code.py pattern - check if resuming or starting new
            current_state = None
            try:
                current_state = await self.workflow.aget_state(thread_config)
            except:
                pass  # New conversation
            
            inputs = None
            if current_state is None or not current_state.values:
                # New conversation - set initial inputs
                inputs = {"query": [user_query]}
                logger.info("🆕 Starting new conversation with initial inputs")
            else:
                # Existing conversation - update state with new query
                logger.info("🔄 Resuming existing conversation")
                await self.workflow.aupdate_state(
                    config=thread_config,
                    values={"query": [user_query]}  # Single query for continuation as list
                )
            
            # Stream execution following helper pattern
            final_state = None
            is_interrupted = False
            interrupt_data = {}
            
            async for event in self.workflow.astream(inputs, config=thread_config):
                logger.info(f"📨 Stream event: {list(event.keys())}")
                
                # Check for interruption
                if "__interrupt__" in event:
                    logger.info("🛑 Workflow interrupted for HITL")
                    is_interrupted = True
                    interrupt_info = event["__interrupt__"]
                    interrupt_data = {
                        "type": "human_verification_required",
                        "message": interrupt_info[0].get("message", "Human input required") if interrupt_info else "Human input required",
                        "thread_id": thread_id
                    }
                    # Get current state for interrupt response
                    final_state = await self.workflow.aget_state(thread_config)
                    break
                
                # Track final state from stream events
                for node_name, node_output in event.items():
                    if node_name != "__interrupt__":
                        final_state = node_output
            
            # Return results following helper pattern
            if is_interrupted:
                logger.info("🛑 Workflow interrupted - awaiting human input")
                return {
                    "status": "waiting_for_input",
                    "message": interrupt_data.get("message", "Human input required"),
                    "thread_id": thread_id
                }
            
            # Check if workflow completed successfully
            if final_state and final_state.get("boolean_query"):
                logger.info("✅ Workflow completed successfully")
                return {
                    "status": "completed",
                    "result": final_state,
                    "thread_id": thread_id
                }
            
            # Get final state if stream ended without explicit completion
            if not final_state:
                state_snapshot = await self.workflow.aget_state(thread_config)
                final_state = state_snapshot.values if state_snapshot else {}
            
            return {
                "status": "completed",
                "result": final_state,
                "thread_id": thread_id
            }
            
        except Exception as e:
            logger.error(f"❌ Workflow execution error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "thread_id": thread_id
            }
    
    async def resume_workflow(
        self,
        thread_id: str,
        user_input: str = None,
        config: Optional[RunnableConfig] = None
    ) -> Dict[str, Any]:
        """
        Resume a workflow from HITL interruption with proper feedback handling
        
        Args:
            thread_id: Conversation ID to resume
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
        
        try:
            # Get current state to check if we're at an interrupt point
            current_state = await self.workflow.aget_state(thread_config)
            
            if not current_state:
                logger.error(f"No state found for thread {thread_id}")
                return {
                    "thread_id": thread_id,
                    "status": "error",
                    "error": f"No thread found with ID {thread_id}"
                }
            
            # Check if we're at an interrupt point
            if not current_state.next or 'hitl_verification' not in current_state.next:
                logger.warning(f"Thread {thread_id} is not at an interrupt point. Next: {current_state.next}")
                return {
                    "thread_id": thread_id,
                    "status": "error",
                    "error": "Workflow is not waiting for human input"
                }
            
            # Prepare feedback data if provided
            input_data = None
            if user_input:
                human_message = HumanMessage(content=user_input)
                
                # Get current query list and append new input if it's a new query
                current_values = current_state.values if current_state and hasattr(current_state, 'values') else {}
                existing_query_list = current_values.get("query", [])
                
                # Check if this is feedback or a new query
                continuation_keywords = ["yes", "proceed", "continue", "ok", "okay", "approved", "correct", "good", "yep", "yeah", "yup", "no", "not", "wrong", "incorrect", "refine", "change", "modify"]
                is_feedback = user_input.lower().strip() in continuation_keywords or len(user_input.split()) <= 3
                
                if not is_feedback and user_input not in existing_query_list:
                    # This looks like a new query, append it to the query list
                    updated_query_list = existing_query_list + [user_input]
                    logger.info(f"📝 Appending new query to list in resume_workflow. Total queries: {len(updated_query_list)}")
                    
                    input_data = {
                        "human_feedback": user_input,
                        "messages": [human_message],
                        "query": updated_query_list  # Update the query list
                    }
                else:
                    # This is feedback, not a new query
                    input_data = {
                        "human_feedback": user_input,
                        "messages": [human_message]
                    }
                
                # Update state with feedback before resuming
                await self.workflow.aupdate_state(thread_config, input_data)
                logger.info(f"✅ Updated state with human feedback: {user_input}")
            
            # Resume workflow execution
            is_interrupted = False
            interrupt_data = {}
            final_state = None
            
            # Resume from interrupt point
            async for state_update in self.workflow.astream(None, config=thread_config):
                final_state = state_update
                
                # Check for another interrupt
                if isinstance(state_update, dict) and '__interrupt__' in state_update:
                    is_interrupted = True
                    logger.info("🛑 Workflow interrupted again during resumption")
                    
                    # Get current state for interrupt handling
                    updated_state = await self.workflow.aget_state(thread_config)
                    if updated_state and hasattr(updated_state, 'values'):
                        final_state = updated_state.values
                        
                        interrupt_data = {
                            "type": "human_verification_required",
                            "next_node": "hitl_verification",
                            "state": "interrupted_before_hitl",
                            "thread_id": thread_id
                        }
                    break
            
            # Return appropriate response
            if is_interrupted:
                return {
                    "thread_id": thread_id,
                    "status": "awaiting_human_input",
                    "interrupt_data": interrupt_data,
                    "current_state": self._serialize_state_for_json(final_state),
                    "message": "Additional HITL verification required"
                }
            else:
                # Get final state after completion
                complete_state = await self.workflow.aget_state(thread_config)
                if complete_state and hasattr(complete_state, 'values'):
                    final_state_values = complete_state.values
                else:
                    final_state_values = final_state
                
                return {
                    "thread_id": thread_id,
                    "status": "completed",
                    "workflow_status": "completed",
                    "results": self._serialize_state_for_json(final_state_values),
                    "message": "Workflow resumed and completed successfully"
                }
            
        except Exception as e:
            logger.error(f"❌ Resume workflow failed: {e}")
            logger.error(traceback.format_exc())
            return {
                "thread_id": thread_id,
                "status": "error",
                "error": str(e)
            }
    
    async def get_workflow_status(self, thread_id: str) -> Dict[str, Any]:
        """Get current status of a workflow conversation"""
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
    
    async def process_dashboard_request(self, user_query: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhanced function to process dashboard requests with intelligent conversation handling.
        
        Features:
        - Automatic conversation continuation detection
        - Mandatory HITL verification for all queries (no auto-approval)
        - Enhanced state logging for PROMPT.md compliance
        
        Args:
            user_query: User's query string
            thread_id: Optional conversation thread ID
            
        Returns:
            Dictionary with workflow results
        """
        logger.info(f"🔍 Processing dashboard request: {user_query[:100]}...")
        
        try:
            # Determine if this is a new conversation or continuation
            is_new_conversation = thread_id is None
            if is_new_conversation:
                thread_id = f"conv_{int(time.time())}"
                logger.info(f"🆕 Starting new conversation: {thread_id}")
            else:
                logger.info(f"🔗 Continuing conversation: {thread_id}")
                
                # Check if this is a continuation query like "Yes", "Proceed", etc.
                continuation_keywords = ["yes", "proceed", "continue", "ok", "okay", "approved", "correct", "good", "yep", "yeah", "yup"]
                is_continuation_query = user_query.lower().strip() in continuation_keywords
                
                if is_continuation_query:
                    logger.info(f"🔄 Detected continuation query: '{user_query}' - using resume workflow")
                    # For continuation queries, use the resume workflow with feedback
                    return await self.resume_workflow(thread_id, user_query)
            
            # Intelligent query analysis for continuation
            if not is_new_conversation:
                # Get existing state to analyze context
                config = RunnableConfig(configurable={"thread_id": thread_id})
                existing_state = self.workflow.get_state(config)
                context = existing_state.values if existing_state and hasattr(existing_state, 'values') else {}
                
                # Use intelligent HITL detection to determine action - for logging only
                hitl_action = determine_hitl_action(user_query, context)
                logger.info(f"🤖 Analysis only (not for approval): {hitl_action['action']} - {hitl_action['reasoning']}")
                
                # Always require human input regardless of query content
                logger.info(f"👤 Human verification required for all queries - no auto-approval")
                
                # For any continuation queries, we always require human input
                # This is a deliberate choice to ensure human oversight
                logger.info(f"👤 Human verification will always be triggered")
                
            # Create initial state (for new conversations or when resume fails)
            initial_state = create_initial_state(user_query, thread_id)
            
            # Add continuation flag if needed
            if not is_new_conversation:
                initial_state["is_continuation"] = True
                
                # For continuing conversations, append new query to existing query list
                try:
                    config = RunnableConfig(configurable={"thread_id": thread_id})
                    existing_state = self.workflow.get_state(config)
                    if existing_state and hasattr(existing_state, 'values'):
                        existing_query_list = existing_state.values.get("query", [])
                        # Append new query to existing list (avoid duplicates)
                        if user_query not in existing_query_list:
                            updated_query_list = existing_query_list + [user_query]
                            initial_state["query"] = updated_query_list
                            logger.info(f"📝 Appended new query to existing list. Total queries: {len(updated_query_list)}")
                        else:
                            initial_state["query"] = existing_query_list
                            logger.info(f"📝 Query already exists in list. Total queries: {len(existing_query_list)}")
                except Exception as e:
                    logger.warning(f"Could not append to existing query list: {e}")
                    # Fall back to creating new list with current query
                    pass
            
            # Create config with thread_id for memory
            config = RunnableConfig(
                configurable={"thread_id": thread_id}
            )
            
            # Log initial state for PROMPT.md compliance
            logger.info("🎯 ========== WORKFLOW INITIALIZATION ==========")
            logger.info(f"📝 User query: {user_query}")
            logger.info(f"🆔 Conversation ID: {thread_id}")
            logger.info(f"🔄 Is continuation: {not is_new_conversation}")
            logger.info(f"📊 Initial state keys: {list(initial_state.keys())}")
            logger.info("🎯 ========== END WORKFLOW INITIALIZATION ==========")
            
            # Use streaming execution to handle interrupts properly
            final_state = None
            is_interrupted = False
            interrupt_data = None
            
            try:
                # Stream the workflow execution to handle HITL interrupts
                async for state_update in self.workflow.astream(initial_state, config):
                    final_state = state_update
                    
                    # Enhanced logging for each node execution
                    if isinstance(state_update, dict):
                        for node_name, node_state in state_update.items():
                            logger.info(f"✅ Node '{node_name}' completed execution")
                            if hasattr(node_state, 'get') and node_state.get('current_stage'):
                                logger.info(f"   📍 Current stage: {node_state.get('current_stage')}")
                
                logger.info(f"🎯 Workflow stream completed for conversation: {thread_id}")
                
                # Enhanced interrupt detection and handling
                if isinstance(final_state, dict) and '__interrupt__' in final_state:
                    logger.info("🛑 Detected workflow interrupt - preparing HITL response")
                    is_interrupted = True
                    
                    # Get current state for interrupt handling
                    current_state = self.workflow.get_state(config)
                    if current_state and hasattr(current_state, 'values'):
                        final_state = current_state.values
                        
                        # Enhanced interrupt data with intelligence
                        interrupt_data = {
                            "type": "human_verification_required",
                            "next_node": "hitl_verification", 
                            "state": "interrupted_before_hitl",
                            "thread_id": thread_id,
                            "state_values": self._serialize_state_for_json(current_state.values),
                            "intelligent_analysis": True
                        }
                        
                        # Check if we should provide guidance based on query analysis
                        latest_message = ""
                        if current_state.values.get("messages"):
                            for msg in reversed(current_state.values["messages"]):
                                if hasattr(msg, 'content') and hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage':
                                    latest_message = msg.content
                                    break
                        
                        if latest_message:
                            hitl_guidance = determine_hitl_action(latest_message, current_state.values)
                            interrupt_data["guidance"] = hitl_guidance
                            logger.info(f"📋 HITL Guidance: {hitl_guidance['reasoning']}")
                
            except Exception as e:
                logger.error(f"❌ Workflow execution error: {e}")
                logger.error(f"📍 Error occurred during conversation: {thread_id}")
                raise
            
            # Return appropriate response based on workflow completion
            if is_interrupted:
                logger.info("🛑 Workflow interrupted - awaiting human input")
                
                # Create a clean, simplified response with no duplication
                return {
                    "thread_id": thread_id,
                    "status": "awaiting_human_input",
                    "interrupt_data": {
                        "type": interrupt_data.get("type", "human_verification_required"),
                        "next_node": interrupt_data.get("next_node", "hitl_verification"),
                        "state": interrupt_data.get("state", "interrupted_before_hitl"),
                        "thread_id": thread_id,
                        "guidance": interrupt_data.get("guidance", {})
                    },
                    "current_state": self._serialize_state_for_json(final_state),
                    "message": "HITL verification required - workflow paused for human input"
                }
            
            logger.info("✅ Workflow completed successfully")
            # Return a clean response with no duplication
            return {
                "thread_id": thread_id,
                "status": "completed", 
                "results": self._serialize_state_for_json(final_state),
                "workflow_status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Error processing dashboard request: {e}")
            return {
                "thread_id": thread_id,
                "status": "error",
                "error": str(e),
                "results": {}
            }
    
    async def handle_user_feedback(self, thread_id: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle user feedback for HITL verification using proper LangGraph patterns.
        
        Args:
            thread_id: Conversation thread ID
            feedback: User feedback data
            
        Returns:
            Dictionary with feedback processing results
        """
        logger.info(f"Handling user feedback for conversation: {thread_id}")
        
        try:
            # Create config with thread_id
            config = RunnableConfig(
                configurable={"thread_id": thread_id}
            )
            
            # Get current state from memory
            state = await self.workflow.aget_state(config)
            
            if not state:
                logger.error(f"No state found for conversation {thread_id}")
                return {
                    "thread_id": thread_id,
                    "status": "error",
                    "error": f"No conversation found with ID {thread_id}"
                }
            
            # Check if the workflow is actually at an interrupt point
            logger.info(f"Current state next nodes: {state.next}")
            
            if not state.next or 'hitl_verification' not in state.next:
                logger.warning(f"Workflow not at interrupt point. Next nodes: {state.next}")
                return {
                    "thread_id": thread_id,
                    "status": "error",
                    "error": "Workflow is not waiting for human input"
                }
            
            # Prepare feedback for the workflow
            if isinstance(feedback, str):
                user_response = feedback
            else:
                user_response = feedback.get("content", "")
            
            # Add human message to messages list to ensure it's saved in the thread
            human_message = HumanMessage(content=user_response)
            
            # Get current query list and check if we need to append new query
            current_values = state.values if state and hasattr(state, 'values') else {}
            existing_query_list = current_values.get("query", [])
            
            # Check if this is feedback or a new query
            continuation_keywords = ["yes", "proceed", "continue", "ok", "okay", "approved", "correct", "good", "yep", "yeah", "yup", "no", "not", "wrong", "incorrect", "refine", "change", "modify"]
            is_feedback = user_response.lower().strip() in continuation_keywords or len(user_response.split()) <= 3
            
            # Add human feedback to the state before resuming
            state_update = {
                "human_feedback": user_response,
                "messages": [human_message],
                "human_input_payload": {
                    "approved": True,
                    "feedback": user_response,
                    "next_action": "continue"
                }
            }
            
            # If this looks like a new query (not just feedback), append it to query list
            if not is_feedback and user_response not in existing_query_list:
                updated_query_list = existing_query_list + [user_response]
                state_update["query"] = updated_query_list
                logger.info(f"📝 Appending new query to list in handle_user_feedback. Total queries: {len(updated_query_list)}")
            
            # Check for rejection keywords to set appropriate action
            rejection_keywords = ['no', 'incorrect', 'wrong', 'reject', 'refine', 'change', 'modify']
            if any(keyword in user_response.lower() for keyword in rejection_keywords):
                state_update["human_input_payload"]["approved"] = False
                state_update["human_input_payload"]["next_action"] = "refine"
                logger.info(f"Detected rejection in response: {user_response}")
            
            # Update the state with human feedback
            await self.workflow.aupdate_state(config, state_update)
            
            # Resume the workflow execution
            logger.info(f"Resuming workflow with human feedback: {user_response}")
            
            # Track if the workflow is interrupted again during resumption
            is_interrupted = False
            interrupt_data = None
            final_state = None
            
            try:
                # For interrupt_before patterns, we should pass None to continue from interrupt point
                # The human feedback should be added to the state during the HITL verification node execution
                async for state_update in self.workflow.astream(None, config=config):
                    final_state = state_update
                    
                    if isinstance(state_update, dict) and '__interrupt__' in state_update:
                        is_interrupted = True
                        logger.info("Workflow interrupted again during resumption")
                        
                        # Get current state for interrupt handling
                        current_state = await self.workflow.aget_state(config)
                        if current_state and hasattr(current_state, 'values'):
                            final_state = current_state.values
                            
                            interrupt_data = {
                                "type": "human_verification_required",
                                "next_node": "hitl_verification", 
                                "state": "interrupted_before_hitl",
                                "thread_id": thread_id
                            }
                
                logger.info(f"🎯 Workflow resumed successfully")
                
            except Exception as e:
                logger.error(f"Error during workflow resumption: {e}")
                return {
                    "thread_id": thread_id,
                    "status": "error",
                    "error": f"Error during workflow resumption: {str(e)}"
                }
            
            if not final_state:
                logger.error("No result returned from workflow resumption")
                return {
                    "thread_id": thread_id,
                    "status": "error",
                    "error": "Failed to resume workflow after user input"
                }
            
            # Check if workflow is interrupted again or completed
            if is_interrupted:
                logger.info("Workflow was interrupted again during resumption")
                return {
                    "thread_id": thread_id,
                    "status": "awaiting_human_input",
                    "interrupt_data": interrupt_data,
                    "current_state": self._serialize_state_for_json(final_state),
                    "message": "Additional HITL verification required"
                }
            
            # If workflow completed successfully, return the final state
            logger.info("Workflow resumed and completed without further interruption")
            
            # Get the complete state after resumption
            complete_state = await self.workflow.aget_state(config)
            if complete_state and hasattr(complete_state, 'values'):
                final_state_values = complete_state.values
            else:
                final_state_values = final_state
            
            # Check if there's a boolean query in the state
            boolean_query = final_state_values.get("boolean_query", "")
            if boolean_query:
                logger.info(f"Boolean query found in final state: {boolean_query[:100]}...")
            else:
                logger.warning("No boolean query found in final state after HITL approval")
            
            return {
                "thread_id": thread_id,
                "status": "completed",
                "workflow_status": "completed",
                "results": self._serialize_state_for_json(final_state_values),
                "message": "Your feedback has been processed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error handling user feedback: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "thread_id": thread_id,
                "status": "error",
                "error": str(e)
            }
    
    async def get_workflow_history(self, thread_id: str) -> Dict[str, Any]:
        """Get conversation history for a specific thread."""
        try:
            config = {"configurable": {"thread_id": thread_id}}
            
            # Get state from memory
            state = await self.workflow.aget_state(config)
            
            return {
                "thread_id": thread_id,
                "status": "retrieved",
                "state": state.values if state else {},
                "messages": state.values.get("messages", []) if state else [],
                "current_step": self._determine_current_step(state.values) if state else "not_found"
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow history: {e}")
            return {
                "thread_id": thread_id,
                "status": "error",
                "error": str(e)
            }
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the workflow."""
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
                "Production-ready FastAPI integration"
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


# Global workflow instance for FastAPI integration
modern_workflow = SprinklrWorkflow()


# Standalone FastAPI integration functions
async def process_dashboard_request(user_query: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Standalone function for FastAPI integration to process dashboard requests.
    
    Args:
        user_query: User's query string  
        thread_id: Optional conversation thread ID
        
    Returns:
        Dictionary with workflow results
    """
    logger.info(f"Standalone processing dashboard request: {user_query[:100]}...")
    
    try:
        # Use global workflow instance
        result = await modern_workflow.process_dashboard_request(user_query, thread_id)
        return result
        
    except Exception as e:
        logger.error(f"Error in standalone dashboard processing: {e}")
        return {
            "thread_id": thread_id or f"conv_{int(time.time())}",
            "status": "error",
            "error": str(e),
            "results": {}
        }


async def handle_user_feedback(thread_id: str, feedback: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Standalone function for FastAPI integration to handle user feedback.
    
    Args:
        thread_id: Conversation thread ID
        feedback: User feedback (string or dict)
        
    Returns:
        Dictionary with feedback processing results
    """
    logger.info(f"Standalone handling user feedback for conversation: {thread_id}")
    
    try:
        # Normalize feedback to string format for resume workflow
        if isinstance(feedback, str):
            feedback_text = feedback
        else:
            feedback_text = feedback.get("content", "")
            
        # Use the resume workflow method which is designed for continuation queries
        result = await modern_workflow.resume_workflow(thread_id, feedback_text)
        return result
        
    except Exception as e:
        logger.error(f"Error in standalone feedback handling: {e}")
        return {
            "thread_id": thread_id,
            "status": "error", 
            "error": str(e)
        }


async def get_workflow_history(thread_id: str) -> List[Dict[str, Any]]:
    """
    Standalone function for FastAPI integration to get workflow history.
    
    Args:
        thread_id: Conversation thread ID
        
    Returns:
        List of conversation messages
    """
    logger.info(f"Standalone getting workflow history for: {thread_id}")
    
    try:
        # Use global workflow instance
        history_result = await modern_workflow.get_workflow_history(thread_id)
        
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
    Get status of the workflow system.
    
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
        logger.error(f"Error getting workflow status: {e}")
        return {
            "status": "error",
            "workflow_initialized": False,
            "error": str(e)
        }
