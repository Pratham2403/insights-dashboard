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
from src.agents.query_generator_agent import QueryGeneratorAgent
from src.agents.theme_modifier_agent import ThemeModifierAgent
from src.utils.hitl_detection import detect_approval_intent, determine_hitl_action, analyze_theme_query_context
from src.persistence.mongodb_checkpointer import get_async_mongodb_checkpointer
import asyncio



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
    
    def __init__(self, checkpointer=None):
        """Initialize the workflow with all components. If checkpointer is None, must call async_init."""
        logger.info("Initializing Modern Sprinklr Workflow...")
        # Setup LLM
        self.llm_setup = LLMSetup()
        self.llm = self.llm_setup.get_agent_llm("workflow")
        
        # Initialize agents
        self.query_refiner = QueryRefinerAgent(self.llm)
        self.data_collector = DataCollectorAgent(self.llm)
        self.data_analyzer = DataAnalyzerAgent(self.llm) 
        self.query_generator = QueryGeneratorAgent(self.llm)
        self.theme_modifier_agent = ThemeModifierAgent(self.llm)
        
        # Setup tools
        self.tools = [get_sprinklr_data]
        self.tool_node = ToolNode(self.tools)
        
        # Initialize current hits storage (separate from state to prevent memory explosion)
        self._current_hits = []
        self.checkpointer = checkpointer
        self.workflow = None
        if checkpointer is not None:
            self.workflow = self._build_workflow()
        logger.info("Modern Sprinklr Workflow initialized successfully")

    async def async_init(self):
        """Async initializer to set up MongoDB checkpointer and build workflow."""
        self.checkpointer = await get_async_mongodb_checkpointer()
        self.workflow = self._build_workflow()

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
        
        # Add Theme HITL nodes
        workflow.add_node("theme_hitl_verification", self._theme_hitl_verification_node)
        workflow.add_node("theme_modifier", self._theme_modifier_node)
        
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
        
        # Add Theme HITL flow after data analyzer
        workflow.add_edge("data_analyzer", "theme_hitl_verification")
        
        # Theme HITL can continue or modify themes
        workflow.add_conditional_edges(
            "theme_hitl_verification",
            self._should_continue_theme_hitl,
            {
                "continue": END,
                "modify": "theme_modifier",
                "refine": "data_analyzer"
            }
        )
        
        # Theme modifier goes back to theme HITL for verification
        workflow.add_edge("theme_modifier", "theme_hitl_verification")
        
        # Use MongoDB checkpointer for persistence
        compiled_workflow = workflow.compile(
            checkpointer=self.checkpointer
        )
        
        logger.info("📋 Workflow compiled with MongoDB checkpointer and Theme HITL nodes")
        logger.info(f"📊 Workflow nodes: {list(workflow.nodes.keys()) if hasattr(workflow, 'nodes') else 'Unknown'}")
        
        return compiled_workflow
    



    async def _query_refiner_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 1: Query Refiner Agent
        - Uses completeUseCase.txt for context
        - Handles conversation context intelligently
        """
        logger.info("🔍 Step 1: Query Refiner Agent")
        logger.info(" ==================== QUERY REFINER STARTED ====================")
        # Log state BEFORE processing
        logger.info(f"🔍 Logging state before Query Refiner processing {state}")

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
                "entities": query_refinement.get("entities", state.get("entities", [])),
                "industry": query_refinement.get("industry", state.get("industry", "")),
                "sub_vertical": query_refinement.get("sub_vertical", state.get("sub_vertical", "")),
                "use_case": query_refinement.get("use_case", state.get("use_case", "")),
                "messages": [refinement_msg],
                "current_stage": "query_refined"
            }
            # Log state AFTER processing
            logger.info(f" ==================== QUERY REFINER COMPLETED ====================")

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
        logger.info(" ==================== DATA COLLECTOR STARTED ====================")

        logger.info(f"🔍 Logging state before Data Collector processing {state}")

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
            summary = collection_result.get("conversation_summary", "")
            defaults_applied = collection_result.get("defaults_applied", {})
            reason = collection_result.get("reason", "")
            
            collection_msg = AIMessage(content=summary)
            
            logger.info(f"📊 Data Collector completed successfully: {len(keywords)} keywords, {len(filters)} filters")
            
            result = {
                "keywords": keywords,
                "filters": filters,
                "defaults_applied": defaults_applied,
                "conversation_summary": summary,
                "messages": [collection_msg],
                "current_stage": "data_collected",
                "hitl_step": 1,  # Set initial HITL step for verification
                "reason": reason
            }
            
            logger.info(" ==================== DATA COLLECTOR COMPLETED ====================")
            
            return result
            
        except Exception as e:
            logger.error(f"Data Collector error: {e}")
            error_msg = AIMessage(content=f"Error in data collection: {str(e)}")
            return {"messages": [error_msg]}
        finally:
            # Log state AFTER processing
            logger.info(" ==================== DATA COLLECTOR COMPLETED ====================")
    
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
        logger.info(" ==================== HITL VERIFICATION STARTED ====================")

        logger.info(f"Logging State Before HITL Verification: {state}")

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
                "instructions": "Reply with your clarification or new requirements."
            })

            # Return state update for step transition
            return {"hitl_step": 1}
            
        # Step 1: Main verification - show user the analysis and ask for approval  
        elif step == 1:
            logger.info("✏️ Step 1: Main verification - requesting user approval")
            
            
            verification_data = {
                "question": "Please review the analysis below and approve to continue:",
                "step": 1,
                "instructions": "Reply 'yes' to approve or provide feedback to refine"
            }
            
            # Use interrupt to capture user input
            interrupt(verification_data)
            
            # After resume, check for user input in the state
            user_input = state.get("user_input")
            if not user_input:
                # If no user input, stay in verification step
                return {"hitl_step": 1}
            
            # Process the user response directly after interrupt
            logger.info(f"📝 Processing user response: '{user_input}'")
            
            # Use dynamic positive and negative analysis from our system
            approval_analysis = detect_approval_intent(user_input)
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
                    "query": [user_input],  # Replace with fresh user input as list
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
        

        logger.info(" ==================== HITL VERIFICATION COMPLETED ====================")
   
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
        logger.info(" ==================== BOOLEANQUERY GENERATOR STARTED ====================")
        # Log state BEFORE processing
        logger.info(f"🔍 Logging state before Query Generator processing {state}")

        try:
            
            # Generate Boolean query using correct method
            boolean_query_result = await self.query_generator({**state})
            
            boolean_query = boolean_query_result.get("boolean_query", "")
            
            # Ensure boolean_query is generated
            if not boolean_query:
                # Fallback boolean query generation
                # boolean_query = " AND ".join([f'"{keyword}"' for keyword in keywords[:5]])
                logger.info(f"🔗 No Boolean query generated")
                error_msg = AIMessage(content="No Boolean query generated - using fallback")
                return {
                    "messages": [error_msg],
                    "boolean_query": "",
                    "current_stage": "boolean_query_generated"
                }

            logger.info(f"🔗 Generated Boolean query: {boolean_query}  ...")
            
            query_msg = AIMessage(
                content=f"Boolean query is generated"
            )
                        
            result = {
                "messages": [query_msg],
                "boolean_query": boolean_query,
                "current_stage": "boolean_query_generated"
            }
            

            
            
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
        finally:
            logger.info(" ==================== BOOLEANQUERY GENERATOR COMPLETED ====================")

    async def _tool_execution_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 5: Tool Execution (ToolNode)
        - Executes the Boolean query via Sprinklr API
        - Returns relevant posts/comments data
        - IMPORTANT: Does NOT store hits in state to prevent memory explosion
        """
        logger.info("🛠️ Step 5: Tool Execution")
        logger.info(" ==================== TOOL EXECUTION STARTED ====================")
        # Log state BEFORE processing
        logger.info(f"🔍 Logging state before Tool Execution processing {state}")

        try:
            boolean_query = state.get("boolean_query", "")
            
            if not boolean_query:
                logger.error("No Boolean query found for tool execution")
                error_msg = AIMessage(content="Error: No Boolean query available for data retrieval")
                return {"messages": [error_msg]}

            logger.info(f"🛠️ Executing tool with Boolean query: {boolean_query[:100]}")
            
            # Execute the get_sprinklr_data tool using the invoke method (modern LangChain pattern)
            hits = await get_sprinklr_data.ainvoke({"query": boolean_query, "limit": 5000})
            
            logger.info(f"🛠️ Retrieved {len(hits)} hits from Sprinklr API")
            
            # Store hits temporarily in workflow instance (NOT in state)
            # This prevents memory explosion in LangGraph state
            self._current_hits = hits
            
            tool_msg = AIMessage(
                content=f"Tool execution completed: Retrieved {len(hits)} hits from Sprinklr API"
            )
            
            result = {
                "messages": [tool_msg],
                "current_stage": "tool_execution_completed",
                "next_node": "data_analyzer",  
            }
            
        
            logger.info(f"🛠️ Tool execution completed with {len(hits)} hits")
            
            return result
            
        except Exception as e:
            logger.error(f"Tool Execution error: {e}")
            error_msg = AIMessage(content=f"Error in tool execution: {str(e)}")
            return {"messages": [error_msg]}
        finally:
            logger.info(" ==================== TOOL EXECUTION COMPLETED ====================")

    async def _data_analyzer_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Step 6: Data Analyzer Agent
        - Gets hits from workflow instance (NOT from state) to prevent memory explosion
        - Processes hits using BERTopic theme analysis
        - Updates themes in state and returns final results
        """
        logger.info("📈 Step 6: Data Analyzer Agent")
        logger.info(" ==================== DATA ANALYZER STARTED ====================")
        logger.info(f"🔍 Logging state before Data Analyzer processing {state}")

        
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
        finally:
            logger.info(" ==================== DATA ANALYZER COMPLETED ====================")
            logger.info(f"🔍 Logging FINAL STATE {state}")



    async def _theme_hitl_verification_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Theme HITL Verification Node after Data Analyzer Agent
        - Implements human-in-the-loop verification for themes
        - Uses interrupt() to pause execution for user input
        - Analyzes user intent for theme modifications
        """
        logger.info("🎨 Theme HITL Verification - Human-in-the-Loop for Themes")
        logger.info(" ==================== THEME HITL VERIFICATION STARTED ====================")
        
        try:
            themes = state.get("themes", [])
            step = state.get("theme_hitl_step", 1)
            
            logger.info(f"🔢 Theme HITL Step: {step}")
            logger.info(f"📊 Number of themes to review: {len(themes)}")
            
            # Step 1: Present themes for user review
            if step == 1:
                logger.info("📋 Step 1: Presenting themes for user review")
                
                # Format themes for user review
                themes_summary = self._format_themes_for_review(themes)
                
                verification_data = {
                    "question": "Please review the generated themes below and provide feedback:",
                    "themes": themes_summary,
                    "step": 1,
                    "instructions": """
You can:
• Type 'yes' or 'approve' to proceed with these themes
• Request modifications like:
  - "Add a theme about customer complaints"
  - "Remove the pricing theme"  
  - "Modify the service theme to focus on support quality"
  - "Create sub-themes for the product feedback theme"
• Ask for clarifications or adjustments

What would you like to do?
                    """.strip()
                }
                
                # Use interrupt to pause execution for user input
                interrupt(verification_data)
                
                # After resume, check for user input in the state
                user_input = state.get("user_input")
                if not user_input:
                    # If no user input, stay in verification step
                    return {"theme_hitl_step": 1}
                
                logger.info(f"📝 User response received: '{user_input}'")
                
                # Analyze user response using enhanced HITL detection
                analysis = analyze_theme_query_context(user_input, themes)
                
                logger.info(f"🤖 Theme analysis result: {analysis}")
                
                # Route based on analysis
                if analysis["primary_action"] == "approval":
                    logger.info("✅ User approved themes - proceeding to completion")
                    return {
                        "theme_hitl_step": 0,  # Reset for next time
                        "next_node": "continue",
                        "workflow_status": "completed",
                        "completed_at": datetime.now().isoformat(),
                        "messages": [AIMessage(content="Themes approved by user. Analysis complete.")]
                    }
                    
                elif analysis["primary_action"] == "theme_modification":
                    logger.info("🔧 User requested theme modifications")
                    modification_data = analysis["modification_analysis"]
                    
                    return {
                        "theme_hitl_step": 2,  # Move to modification step
                        "theme_modification_intent": modification_data["intent"],
                        "target_theme": modification_data["target_theme"],
                        "theme_modification_details": user_input,
                        "original_themes": themes.copy(),  # Backup original themes
                        "next_node": "modify",
                        "user_input": user_input
                    }
                    
                else:
                    logger.info("📋 User provided general feedback - staying in verification")
                    return {
                        "theme_hitl_step": 1,  # Stay in verification 
                        "next_node": "refine",  # Go back to data analyzer for refinement
                        "user_input": user_input,
                        "messages": [HumanMessage(content=user_input)]
                    }
            
            # Step 2: Handle post-modification verification
            elif step == 2:
                logger.info("🔄 Step 2: Post-modification verification")
                
                verification_data = {
                    "question": "Please review the updated themes:",
                    "themes": self._format_themes_for_review(themes),
                    "step": 2,
                    "instructions": "Are you satisfied with the theme modifications? Reply 'yes' to proceed or request further changes."
                }
                
                # Use interrupt to pause execution for user input
                interrupt(verification_data)
                
                # After resume, check for user input in the state
                user_input = state.get("user_input")
                if not user_input:
                    # If no user input, stay in verification step
                    return {"theme_hitl_step": 2}
                
                # Analyze response
                analysis = analyze_theme_query_context(user_input, themes)
                
                if analysis["primary_action"] == "approval":
                    logger.info("✅ User approved modified themes")
                    return {
                        "theme_hitl_step": 0,
                        "next_node": "continue",
                        "workflow_status": "completed",
                        "completed_at": datetime.now().isoformat(),
                        "messages": [AIMessage(content="Modified themes approved. Analysis complete.")]
                    }
                elif analysis["primary_action"] == "theme_modification":
                    logger.info("🔧 User requested additional modifications")
                    modification_data = analysis["modification_analysis"]
                    
                    return {
                        "theme_hitl_step": 2,  # Stay in modification loop
                        "theme_modification_intent": modification_data["intent"],
                        "target_theme": modification_data["target_theme"],
                        "theme_modification_details": user_input,
                        "next_node": "modify",
                        "user_input": user_input
                    }
                else:
                    logger.info("📋 User provided feedback - going back for refinement")
                    return {
                        "theme_hitl_step": 1,
                        "next_node": "refine",
                        "user_input": user_input,
                        "messages": [HumanMessage(content=user_input)]
                    }
            
            # Default fallback
            else:
                logger.warning(f"⚠️ Unknown theme HITL step: {step}")
                return {
                    "theme_hitl_step": 1,
                    "next_node": "continue"
                }
                
        except Exception as e:
            logger.error(f"❌ Theme HITL verification error: {e}")
            return {
                "theme_hitl_step": 0,
                "next_node": "continue",
                "errors": [f"Theme HITL error: {str(e)}"],
                "messages": [AIMessage(content=f"Error in theme verification: {str(e)}")]
            }
        finally:
            logger.info(" ==================== THEME HITL VERIFICATION COMPLETED ====================")
    
    
    def _should_continue_theme_hitl(self, state: DashboardState) -> str:
        """
        Decision logic for theme HITL workflow routing
        Routes based on next_node field set by theme HITL verification node.
        
        Returns:
        - "continue": Proceed to final results
        - "modify": Go to Theme Modifier Agent  
        - "refine": Go back to Data Analyzer Agent for refinement
        """
        next_node = state.get("next_node", "continue")
        
        logger.info(f"🔀 Theme HITL routing decision: {next_node}")
        
        # Route based on next_node field
        if next_node == "modify":
            return "modify"
        elif next_node == "refine":
            return "refine"
        else:
            return "continue"
    
    
    async def _theme_modifier_node(self, state: DashboardState) -> Dict[str, Any]:
        """
        Theme Modifier Node after Theme HITL Verification
        - Allows user to modify themes based on HITL feedback
        - Uses Theme Modifier Agent for supervised theme manipulation
        """
        logger.info("🔧 Theme Modifier Agent - Processing Theme Modifications")
        logger.info(" ==================== THEME MODIFIER STARTED ====================")
        
        try:
            # Initialize Theme Modifier Agent if not already done
            if not hasattr(self, 'theme_modifier_agent'):
                self.theme_modifier_agent = ThemeModifierAgent()
            
            # Get modification parameters from state
            intent = state.get("theme_modification_intent", "modify")
            current_themes = state.get("themes", [])
            user_request = state.get("theme_modification_details", "")
            target_theme = state.get("target_theme")
            
            logger.info(f"🎯 Modification intent: {intent}")
            logger.info(f"🎯 Target theme: {target_theme}")
            logger.info(f"📝 User request: {user_request}")
            
            # Get original data if available for re-clustering
            context_data = getattr(self, '_current_hits', None)
            if context_data and isinstance(context_data, list):
                # Extract text content for theme analysis
                docs = [hit.get('message', '') for hit in context_data if hit.get('message')]
            else:
                docs = None
            
            # Process the modification
            result = await self.theme_modifier_agent.process_theme_modification(
                intent=intent,
                current_themes=current_themes,
                user_request=user_request,
                target_theme=target_theme,
                context_data=docs
            )
            
            if result["success"]:
                logger.info(f"✅ Theme modification successful: {result.get('message')}")
                
                # Update state with modified themes
                return {
                    "themes": result["themes"],
                    "theme_hitl_step": 2,  # Go to post-modification verification
                    "current_stage": "theme_modified",
                    "messages": [AIMessage(content=f"Themes updated: {result.get('message')}")]
                }
            else:
                logger.error(f"❌ Theme modification failed: {result.get('error')}")
                
                # Return to verification with error message
                return {
                    "theme_hitl_step": 1,
                    "errors": [result.get("error", "Theme modification failed")],
                    "messages": [AIMessage(content=f"Theme modification failed: {result.get('error')}. Please try again.")]
                }
                
        except Exception as e:
            logger.error(f"❌ Theme modifier error: {e}")
            return {
                "theme_hitl_step": 1,
                "errors": [f"Theme modifier error: {str(e)}"],
                "messages": [AIMessage(content=f"Error modifying themes: {str(e)}")]
            }
        finally:
            logger.info(" ==================== THEME MODIFIER COMPLETED ====================")
    
    def _format_themes_for_review(self, themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format themes for user review in HITL verification.
        
        Args:
            themes: List of theme dictionaries
            
        Returns:
            Formatted themes for display
        """
        formatted_themes = []
        
        for i, theme in enumerate(themes, 1):
            formatted_theme = {
                "number": i,
                "name": theme.get("theme_name", f"Theme {i}"),
                "description": theme.get("description", "No description available"),
                "keywords": theme.get("keywords", [])[:5],  # Show first 5 keywords
                "confidence": theme.get("confidence_score", 0.0),
                "document_count": theme.get("document_count", 0),
                "boolean_query": theme.get("boolean_query", "")[:100] + "..." if len(theme.get("boolean_query", "")) > 100 else theme.get("boolean_query", "")
            }
            formatted_themes.append(formatted_theme)
        
        return formatted_themes




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
    

    def _determine_current_step(self, state: Dict[str, Any]) -> str:
        """Determine current workflow step based on state"""
        if state.get("themes"):
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
   

    async def get_workflow_history(self, thread_id: str) -> Dict[str, Any]:
        """Get conversation history for a specific thread."""
        try:
            config = {"configurable": {"thread_id": thread_id}}
            
            # Get state from memory
            state = await self.workflow.workflow.aget_state(config)
            logger.info(f"📜 Retrieved state for thread {thread_id}: {state}")
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
    


# Global workflow instance for FastAPI integration
workflow = SprinklrWorkflow()





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
        history_result = await workflow.get_workflow_history(thread_id)
        
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

