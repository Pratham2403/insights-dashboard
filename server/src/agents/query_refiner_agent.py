"""
# Query Refiner Agent
This agent is responsible for refining user queries based on the RAG Context. It analyzes the user's input, identifies areas for improvement and the additional Contexts that can be Added in the User Query and Generates a More Refined prompt and returns this Refined JSON to the "Data Collector Agent" which Works with HITL.


# RAG Context:
This Consists of the List of all the available and existing Filters / Keyword in the Sprinklr Dashboard. This will be used to search / imporove the User Query and generate a more refined query / Data JSON that will eventually be used to fetch the data from the Sprinklr API.

# Functionality:
- Based on the User Input, the Agent Understands the Context and searches for the most relevant filters / keywords that can be used to refine the user query.
- The Agent using LLM will generate a more refined query based on the user input and the RAG Context.
- The agent then generates a JSON object that contains the refined query and, the key:value pairs based on the refined IInformation that it has Collected or any additional information.
- The Agent returns the JSON Object to the "Data Collector Agent" which will use this refined query / Data JSON to Analyze what more data that needs to be collected from the user and works with HITL to confirm the data.


# Example: 
Input: "I want to do my Brand Health Monitoring"
Output: {
  "refined_query": "Brand Health Monitoring",
  "filters": {
    "topic": "brand health monitoring",
  }
}


"""

import json
import logging
import os
import importlib.util
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
import sys
from src.utils.files_helper import import_module_from_file
from src.agents.base.agent_base import LLMAgent, create_agent_factory

logger = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

class QueryRefinerAgent(LLMAgent):
    """
    Query Refiner Agent for analyzing and refining user queries.
    
    Uses RAG context to understand user intent and suggest relevant
    filters and themes for dashboard generation.
    """
    
    def __init__(self, llm=None, rag_system=None):
        """
        Initialize the Query Refiner Agent.
        
        Args:
            llm: Language model instance (optional)
            rag_system: RAG system for context retrieval
        """
        super().__init__("query_refiner", llm)
        self.rag_system = rag_system
        if not self.rag_system:
            # Initialize default RAG system if not provided
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                rag_path = os.path.join(current_dir, '..', 'rag')
                filters_module = import_module_from_file(os.path.join(rag_path, 'filters.rag.py'), 'filters_rag')
                self.rag_system = filters_module.FiltersRAG()
            except Exception as e:
                logger.warning(f"Could not initialize RAG system: {e}")
                self.rag_system = None
    
    async def invoke(self, state) -> Any:
        """
        Main entry point for the agent - delegates to process_state.
        
        Args:
            state: The dashboard state to process
            
        Returns:
            Updated state after query refinement processing
        """
        return await self.process_state(state)
    
    def refine_query(self, user_query: str, additional_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Refine a user query using RAG context.
        
        Args:
            user_query: Original user query
            additional_context: Optional additional context
            
        Returns:
            Refined query data with suggestions
        """
        try:
            # Initialize LLM if not already set
            if not self.llm:
                try:
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    setup_path = os.path.join(current_dir, '..', 'setup')
                    llm_module = import_module_from_file(os.path.join(setup_path, 'llm_setup.py'), 'llm_setup')
                    llm_setup = llm_module.LLMSetup()
                    self.llm = llm_setup.get_agent_llm("query_refiner")
                except Exception as e:
                    logger.error(f"Error initializing LLM: {e}")
                    return self._create_fallback_refinement(user_query)
            
            # Get RAG context for the query
            rag_context = self._get_rag_context(user_query)
            
            # Build the prompt with context
            prompt = self._build_refinement_prompt(user_query, rag_context, additional_context)
            
            # Get LLM response with error handling
            try:
                response = self.llm.invoke([HumanMessage(content=prompt)])
                
                # Handle different response types
                if isinstance(response, str):
                    response_content = response
                elif hasattr(response, 'content'):
                    response_content = response.content
                else:
                    response_content = str(response)
                    
            except Exception as e:
                logger.error(f"Error invoking LLM: {e}")
                return self._create_fallback_refinement(user_query)
            
            # Parse the response
            refined_data = self._parse_refinement_response(response_content)
            
            # Add metadata
            refined_data["original_query"] = user_query
            refined_data["agent"] = self.agent_name
            refined_data["rag_context"] = rag_context
            
            logger.info(f"Successfully refined query: {user_query}")

            return refined_data
            
        except Exception as e:
            logger.error(f"Error refining query: {e}")
            return self._create_fallback_refinement(user_query)
    
    def _get_rag_context(self, query: str) -> Dict[str, Any]:
        """Get relevant context from RAG system."""
        try:
            if self.rag_system and hasattr(self.rag_system, 'get_context_for_query'):
                context = self.rag_system.get_context_for_query(query)
                return context
            else:
                # Fallback to basic context
                return {"filters": [], "themes": [], "query": query}
        except Exception as e:
            logger.error(f"Error getting RAG context: {e}")
            return {"filters": [], "themes": [], "query": query}

    def _build_refinement_prompt(self, user_query: str, rag_context: Dict, additional_context: Optional[Dict] = None) -> str:
        """Build the refinement prompt with context."""
        try:
            # Import prompts using the helper function
            current_dir = os.path.dirname(os.path.abspath(__file__))
            prompts_path = os.path.join(current_dir, '..', 'helpers', 'prompts_helper.py')
            prompts_module = import_module_from_file(prompts_path, 'prompts_helper')
            QUERY_REFINER_SYSTEM_PROMPT = prompts_module.QUERY_REFINER_SYSTEM_PROMPT
        except Exception as e:
            logger.error(f"Error importing prompts: {e}")
            # Fallback prompt
            QUERY_REFINER_SYSTEM_PROMPT = """
            You are a Query Refiner Agent. Analyze the user query: {user_query}
            Available filters: {filters_context}
            Available themes: {themes_context}
            Use cases: {use_cases_context}
            
            Return a JSON object with refined query and suggestions.
            """
        
        # Format context information
        filters_context = self._format_filters_context(rag_context.get("filters", []))
        themes_context = self._format_themes_context(rag_context.get("themes", []))
        use_cases_context = self._format_use_cases_context(rag_context.get("use_cases", []))
        
        prompt = QUERY_REFINER_SYSTEM_PROMPT.format(
            user_query=user_query,
            filters_context=filters_context,
            themes_context=themes_context,
            use_cases_context=use_cases_context
        )
        
        if additional_context:
            prompt += f"\n\nAdditional Context: {json.dumps(additional_context, indent=2)}"
        
        return prompt
    
    def _format_filters_context(self, filters: List[Dict]) -> str:
        """Format filters for prompt context."""
        if not filters:
            return "No specific filters found."
        
        formatted = []
        for filter_item in filters[:5]:  # Limit to top 5
            formatted.append(f"- {filter_item.get('name', 'Unknown')}: {filter_item.get('description', 'No description')}")
        
        return "\n".join(formatted)
    
    def _format_themes_context(self, themes: List[Dict]) -> str:
        """Format themes for prompt context."""
        if not themes:
            return "No specific themes found."
        
        formatted = []
        for theme in themes[:3]:  # Limit to top 3
            formatted.append(f"- {theme.get('name', 'Unknown')}: {theme.get('description', 'No description')}")
        
        return "\n".join(formatted)
    
    def _format_use_cases_context(self, use_cases: List[Dict]) -> str:
        """Format use cases for prompt context."""
        if not use_cases:
            return "No similar use cases found."
        
        formatted = []
        for use_case in use_cases[:2]:  # Limit to top 2
            formatted.append(f"- {use_case.get('title', 'Unknown')}: {use_case.get('description', 'No description')}")
        
        return "\n".join(formatted)
    
    def _parse_refinement_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data."""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Fallback parsing
                return self._extract_refinement_from_text(response)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return self._extract_refinement_from_text(response)
        except Exception as e:
            logger.error(f"Error parsing refinement response: {e}")
            return self._extract_refinement_from_text(response)
    
    def _extract_refinement_from_text(self, response: str) -> Dict[str, Any]:
        """Extract refinement data from plain text response."""
        # Basic extraction logic
        refined_query = response.split('\n')[0] if response else "Brand monitoring analysis"
        
        return {
            "refined_query": refined_query,
            "suggested_filters": [],
            "suggested_themes": [
                {"name": "Brand Health", "description": "Overall brand health monitoring"}
            ],
            "missing_information": ["products", "channels", "time_period"],
            "confidence_score": 0.5
        }
    
    def _create_fallback_refinement(self, user_query: str) -> Dict[str, Any]:
        """Create a fallback refinement when processing fails."""
        return {
            "original_query": user_query,
            "refined_query": f"Social media monitoring and analysis for: {user_query}",
            "suggested_filters": [
                {"name": "Brand Mentions", "description": "Track brand mentions"},
                {"name": "Sentiment Analysis", "description": "Analyze sentiment"},
                {"name": "Channel Filter", "description": "Filter by channels"}
            ],
            "suggested_themes": [
                {"name": "Brand Health", "description": "Overall brand health monitoring"}
            ],
            "missing_information": ["products", "channels", "time_period", "goals"],
            "confidence_score": 0.3,
            "agent": self.agent_name,
            "error": "Fallback refinement used"
        }
    
    def validate_refinement(self, refinement_data: Dict[str, Any]) -> bool:
        """Validate that refinement data has required fields."""
        required_fields = ["refined_query", "suggested_filters", "missing_information"]
        return all(field in refinement_data for field in required_fields)

    async def process_state(self, state) -> Any:
        """
        Process the dashboard state for query refinement.
        
        This method wraps the refine_query method to work with the workflow state.
        """
        try:
            logger.info("Processing state for query refinement")
            
            # Get the user query from state
            # Modify around line 259
            user_query = getattr(state, 'user_query', '') or getattr(state, 'original_query', '')
            if not user_query or not user_query.strip():
                logger.error("No valid user query found in state")
                state.errors.append("No valid user query found for refinement")
                state.workflow_status = "query_refinement_failed"
                return state
            
            # Get additional context from state
            additional_context = getattr(state, 'user_context', {})
            
            # Refine the query
            refinement_result = self.refine_query(user_query, additional_context)
            
            # Create QueryRefinementData object
            # Import using relative path since we're inside src
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            states_path = os.path.join(current_dir, '..', 'helpers', 'states.py')
            states_module = import_module_from_file(states_path, 'states')
            QueryRefinementData = states_module.QueryRefinementData
            
            # Ensure suggested_filters and suggested_themes are lists of dictionaries
            suggested_filters = refinement_result.get("suggested_filters", [])
            if not isinstance(suggested_filters, list):
                suggested_filters = []
            # Convert strings to dictionaries if needed
            for i, filter_item in enumerate(suggested_filters):
                if isinstance(filter_item, str):
                    suggested_filters[i] = {"name": filter_item, "description": f"Filter for {filter_item}"}
            
            suggested_themes = refinement_result.get("suggested_themes", [])
            if not isinstance(suggested_themes, list):
                suggested_themes = []
            # Convert strings to dictionaries if needed
            for i, theme_item in enumerate(suggested_themes):
                if isinstance(theme_item, str):
                    suggested_themes[i] = {"name": theme_item, "description": f"Theme for {theme_item}"}
            
            query_refinement_data = QueryRefinementData(
                original_query=user_query,
                refined_query=refinement_result.get("refined_query", user_query),
                suggested_filters=suggested_filters,
                suggested_themes=suggested_themes,
                missing_information=refinement_result.get("missing_information", []),
                confidence_score=refinement_result.get("confidence_score", 0.0)
            )
            
            # Update state with refinement data
            if hasattr(state, 'query_refinement_data'):
                # Convert to dictionary to avoid validation issues with Pydantic models
                state.query_refinement_data = query_refinement_data.model_dump()
            if hasattr(state, 'query_refinement'):
                # Convert to dictionary to avoid validation issues with Pydantic models
                state.query_refinement = query_refinement_data.model_dump()
            
            # Update workflow status
            if hasattr(state, 'workflow_status'):
                state.workflow_status = "query_refined"
            if hasattr(state, 'current_stage'):
                state.current_stage = "refining"
                
            logger.info("Query refinement completed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error processing state: {str(e)}")
            # Add error to state if it has errors attribute
            if hasattr(state, 'errors'):
                state.errors.append(f"Query refinement error: {str(e)}")
            if hasattr(state, 'workflow_status'):
                state.workflow_status = "query_refinement_failed"
            return state

# Factory function for creating QueryRefinerAgent instances
create_query_refiner_agent = create_agent_factory(QueryRefinerAgent, "query_refiner")