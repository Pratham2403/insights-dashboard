"""
Modern Query Generator Agent - Creates Boolean queries using AND/OR/NEAR/NOT operators.

This agent follows the architecture requirement to generate Boolean keyword queries
using the refined query, extracted data, filters, and keywords from the agent state.

Architecture Flow Position: Step 5
Input: Refined query, keywords list, filters list
Output: Boolean query string for API tool
Context: Uses keyword_query_patterns.json for examples
"""

import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.base.agent_base import LLMAgent
from src.helpers.states import DashboardState

logger = logging.getLogger(__name__)


class QueryGeneratorAgent(LLMAgent):
    """
    Modern Query Generator Agent using latest LangGraph patterns.
    
    Generates Boolean keyword queries using AND, OR, NEAR, NOT operators
    based on the refined query, keywords list, and filters list.
    """
    
    def __init__(self, llm=None):
        super().__init__("query_generator", llm)
        self.query_patterns = self._load_query_patterns()
        
    def _load_query_patterns(self) -> Dict[str, Any]:
        """Load keyword query patterns from knowledge base."""
        try:
            patterns_path = Path(__file__).parent.parent / "knowledge_base" / "keyword_query_patterns.json"
            with open(patterns_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load query patterns: {e}")
            return {"syntax_keywords": ["AND", "OR", "NOT", "NEAR", "ONEAR"], "example_queries": []}
    
    async def __call__(self, state: DashboardState, description: str = "") -> Dict[str, Any]:
        """
        Generate Boolean query from refined query, keywords, and filters.
        
        Args:
            state: Current workflow state containing refined_query, keywords, filters
            
        Returns:
            State update with boolean_query
        """
        try:
            self.logger.info("Generating Boolean query")
            
            # Extract required data from state
            refined_query = state.get("refined_query", description)
            keywords = state.get("keywords", [])
            filters = state.get("filters", {})
            
            if not refined_query:
                logger.warning("No refined query found, using keywords only for Boolean query generation")
            
            # Generate Boolean query with all available data
            boolean_query = await self._generate_boolean_query(
                refined_query=refined_query,
                keywords=keywords,
                filters=filters,
            )
            
            if boolean_query:
                self.logger.info(f"Boolean query generated successfully: {boolean_query[:100]}...")
                return {
                    "boolean_query": boolean_query,
                    "query_generation_status": "success",
                    "messages": [HumanMessage(content=f"Generated Boolean query: {boolean_query}")]
                }
            else:
                # Fallback to simple boolean query if generation failed
                if keywords:
                    fallback_query = " AND ".join([f'"{keyword}"' for keyword in keywords[:5]])
                    logger.info(f"Using fallback Boolean query: {fallback_query}")
                    return {
                        "boolean_query": fallback_query,
                        "query_generation_status": "fallback",
                        "messages": [HumanMessage(content=f"Generated fallback Boolean query: {fallback_query}")]
                    }
                return {"error": "Failed to generate Boolean query - no keywords available"}
                
        except Exception as e:
            self.logger.error(f"Query generation failed: {e}")
            return {"error": f"Query generation error: {str(e)}"}
    
    async def _generate_boolean_query(self, refined_query: str, keywords: List[str], filters: List[Dict]) -> Optional[str]:
        """
        Generate Boolean query using LLM with proper syntax.
        
        Args:
            refined_query: User's refined query
            keywords: List of keywords
            filters: List of exact filters to apply
            
        Returns:
            Boolean query string or None if generation fails
        """
        try:

            logger.info(f"Query Examples : {chr(10).join(self.query_patterns.get('example_queries', []))}")

            # Create system prompt with examples
            system_prompt = f"""
            You are a Boolean Query Generator specialized in retrieving raw user-generated messages from social platforms.

            Your task is to convert a refined intent into one precise Boolean query that returns exactly the user’s messages of interest.

            Key principles:
            1. **Keyword matching**  
               • Use only **message-level indicator terms**—words or short phrases people actually write (e.g., love, hate, worst, amazing, defect, never buying again).  
               • **Do not** use abstract concepts (brand, monitoring, insights).

            2. **Filter matching**  
               • Include only **explicit** "field:<space>value" filters (e.g., "source: TWITTER").  
               • **Do not** invent or assume any filters.

            Supported operators (uppercase only):  
            - AND  – both terms required  
            - OR   – either term acceptable  
            - NOT  – exclude term  
            - NEAR – terms appear close together  
            - ONEAR– terms within a specified distance (e.g., love ONEAR defect)

            Syntax rules:
            - Separate every token and operator with spaces.  
            - Inline filters exactly as field:value (no spaces around “:”).  
            - Use parentheses to group OR expressions.  
            - Use NEAR/ONEAR for proximity-based sentiment‐object pairs.  
            - Only include keywords and filters directly from the provided lists.  

            Examples:
            {chr(10).join(self.query_patterns.get('example_queries', []))}

            """

            # Create user prompt with context
            user_prompt = f"""
            Generate a Boolean query:

            Refined Query:
            {refined_query}

            Available Keywords:
            {keywords}

            Available Filters:
            {json.dumps(filters, indent=2)}

            Requirements:
            - Use **only** message-level indicator keywords from the Available Keywords list.
            - Apply **only** those filters explicitly provided.
            - Group related keywords with parentheses and OR.
            - Use NEAR or ONEAR for sentiment–object proximity (e.g., hate NEAR defect).
            - Combine terms with uppercase Boolean operators (AND, OR, NOT, NEAR, ONEAR).
            - Return **only** the final Boolean query string, no explanation.
            """



            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.safe_llm_call(messages)
            
            if response:
                # Clean up the response - remove quotes and extra whitespace
                boolean_query = response.strip().strip('"').strip("'").strip()
                
                # Validate that it contains Boolean operators
                if any(op in boolean_query.upper() for op in ['AND', 'OR', 'NOT', 'NEAR']):
                    return boolean_query
                else:
                    # If no Boolean operators, create a simple AND query
                    if keywords:
                        return " AND ".join(f'"{keyword}"' for keyword in keywords[:3])
                    else:
                        return f'"{refined_query}"'
            
            return None
            
        except Exception as e:
            self.logger.error(f"Boolean query generation failed: {e}")
            return None



def create_query_generator_agent(llm=None) -> QueryGeneratorAgent:
    """
    Factory function to create a Modern Query Generator Agent.
    
    Args:
        llm: Language model instance (optional)
        
    Returns:
        Configured QueryGeneratorAgent instance
    """
    return QueryGeneratorAgent(llm=llm)