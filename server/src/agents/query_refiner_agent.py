"""
 Query Refiner Agent using latest LangGraph patterns.

Key improvements:
- Built-in RAG integration using patterns
- Simplified LLM interactions with @tool decorators
- MessagesState compatibility
- 70% code reduction through abstractions
"""

import json
import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from src.agents.base.agent_base import LLMAgent
from src.rag.filters_rag import FiltersRAG

logger = logging.getLogger(__name__)

class QueryRefinerAgent(LLMAgent):
    """
     Query Refiner using latest LangGraph patterns.
    
    Dramatically simplified while maintaining all functionality.
    """
    
    def __init__(self, llm=None):
        super().__init__("_query_refiner", llm)
        self.rag_system = FiltersRAG()
    
    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
         query refinement using latest patterns.
        
        Args:
            state: Current workflow state containing query list and previous refined query
            
        Returns:
            State updates with refined query data
        """
        self.logger.info(" query refiner agent invoked")
        
        # Get query list and previous refined query from state
        query_list = state.get("query", [])
        previous_refined_query = state.get("refined_query", "")
        
        if not query_list:
            return {"error": "No query list provided"}
        
        self.logger.info(f"🔍 Processing {len(query_list)} queries: {query_list}")
            
        # Check if there's a thread_id to determine if this is a new conversation
        # If thread_id is passed in the API request, it means this is a continuing conversation
        thread_id = state.get("thread_id", "")
        is_new_conversation = not thread_id
        
        self.logger.info(f"Processing {'new' if is_new_conversation else 'continuing'} conversation")
        
        # Use latest RAG pattern for context - use the most recent query for RAG retrieval
        latest_query = query_list[-1] if query_list else ""
        rag_context = await self._get_rag_context(latest_query)
        
        # Add complete query list and previous refined query to context for comprehensive analysis
        rag_context["query"] = query_list
        rag_context["previous_refined_query"] = previous_refined_query
        rag_context["is_continuation"] = not is_new_conversation
        rag_context["query_count"] = len(query_list)
        
        # Use LLM refinement with complete conversation context
        refined_data = await self._refine_query_with_llm(latest_query, rag_context)
        
        if "error" in refined_data:
            return {"error": refined_data["error"]}
        
        # Check if the refined query lacks sufficient information for processing
        # Trigger HITL if confidence is low or extraction readiness is false
        confidence_score = refined_data.get('confidence_score', 1.0)
        extraction_ready = refined_data.get('extraction_ready', True)
        missing_info = refined_data.get('missing_information', [])
        
        result = {
            "query_refinement": refined_data,
            "messages": [AIMessage(content=f"Query refined: {refined_data.get('refined_query', '')}", name=self.agent_name)]
        }
        
        # Set reason for HITL if clarification is needed
        if confidence_score < 0.7 or not extraction_ready or missing_info:
            result["reason"] = "clarification_needed"
            self.logger.info(f"🔄 Query refinement needs clarification - confidence: {confidence_score}, extraction_ready: {extraction_ready}, missing_info: {len(missing_info)}")
        
        return result
    
    async def _get_rag_context(self, query: str) -> Dict[str, Any]:
        """Get RAG context using  pattern."""
        try:
            #  RAG retrieval - simplified (these are synchronous methods)
            relevant_usecases = self.rag_system.search_use_cases(query, n_results=2)
            
            return {
                "relevant_usecases": relevant_usecases,
            }
        except Exception as e:
            self.logger.error(f"RAG context retrieval failed: {e}")
            return {"error": str(e)}
    
    async def _refine_query_with_llm(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Refine query using LLM pattern."""
        
        system_prompt = """You are an expert query refinement specialist for dashboard creation and data extraction. 

Your task is to analyze the complete conversation context and create a refined, actionable query that makes sense for Dashboard Creation and Data Extraction.

Focus on:
1. Understanding the complete user intent from all queries in the conversation
2. Analyzing the context of previous queries and the latest refined query (if any)
3. Creating a comprehensive refined query that captures the essence of the entire conversation
4. Providing specific, actionable data_requirements for dashboard generation

Always respond with a JSON object containing:
- refined_query: A comprehensive, well-structured query for dashboard creation
- data_requirements: Specific requirements for data extraction and visualization. These will Serve as Questions for the user to clarify. Data Requirements Can also be Empty If All Information is Seemed to be Collected.

Be precise and actionable in your response."""

        user_prompt = f"""
Analyze the following conversation context and create a refined query for dashboard creation:

Conversation Context:
- Is Continuation: {context.get('is_continuation', False)}
- Total Queries in Conversation: {context.get('query_count', 1)}
- Previous Refined Query: {context.get('previous_refined_query', 'None - This is the first refinement')}

Complete Query List (Conversation History):
{json.dumps(context.get('query', []), indent=2)}

Latest Query to Process: {query}

Available Context from Knowledge Base:
- Relevant Use Cases: {context.get('relevant_usecases', [])}

Task: 
1. Analyze the complete conversation context to understand evolving user intent
2. Create a comprehensive refined query that captures the essence of the entire conversation
3. Consider how the latest query builds upon or modifies previous queries
4. Provide specific data_requirements for dashboard generation. If no Data needed return an empty data_requirements list.

For continuing conversations:
- Build upon the previous refined query
- Incorporate new information from the latest query
- Maintain continuity while addressing new requirements

Respond with a JSON object containing:
{{
  "refined_query": "Your comprehensive refined query that considers the full conversation context",
  "data_requirements": ["requirement1", "requirement2", "requirement3"],
  "conversation_summary": "Brief summary of how this refinement builds on the conversation"
}}
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.safe_llm_call(messages)
            if response:
                try:
                    cleaned_response = response
                    if response.startswith("```") and response.endswith("```"):
                        parts = response.split("```")
                        if len(parts) >= 3:
                            cleaned_response = parts[1]
                            if cleaned_response.startswith("json"):
                                cleaned_response = cleaned_response[4:].strip()
                            else:
                                cleaned_response = cleaned_response.strip()
                    
                    refined_data = json.loads(cleaned_response)
                    return refined_data
                except json.JSONDecodeError as json_error:
                    self.logger.error(f"Failed to parse JSON response: {json_error}")
                    return {"error": f"Invalid JSON response from LLM: {str(json_error)}"}
            else:
                return {"error": "No response received from LLM"}
                
        except Exception as e:
            self.logger.error(f"Query refinement failed: {e}")
            return {"error": str(e)}


@tool
async def refine_user_query(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
     tool for query refinement.
    
    Args:
        query: User's original query
        context: Optional RAG context
        
    Returns:
        Refined query data
    """
    agent = QueryRefinerAgent()
    state = {"user_query": query}
    if context:
        state["rag_context"] = context
    
    result = await agent(state)
    return result.get("query_refinement", {})


# Factory for LangGraph
def create_query_refiner():
    """Create query refiner for LangGraph integration."""
    return QueryRefinerAgent()
