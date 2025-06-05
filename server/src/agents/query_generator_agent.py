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
from src.agents.base.modern_agent_base import ModernLLMAgent
from src.helpers.modern_states import ModernDashboardState

logger = logging.getLogger(__name__)


class ModernQueryGeneratorAgent(ModernLLMAgent):
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
            return {"syntax_keywords": ["AND", "OR", "NOT", "NEAR"], "example_queries": []}
    
    async def __call__(self, state: ModernDashboardState) -> Dict[str, Any]:
        """
        Generate Boolean query from refined query, keywords, and filters.
        
        Args:
            state: Current workflow state containing refined_query, keywords, filters
            
        Returns:
            State update with boolean_query
        """
        try:
            self.log_operation("Generating Boolean query")
            
            # Extract required data from state
            refined_query = state.get("refined_query", "")
            keywords = state.get("keywords", [])
            filters = state.get("filters", [])
            extracted_data = state.get("extracted_data", {})
            
            if not refined_query:
                return {"error": "No refined query available for Boolean query generation"}
            
            # Generate Boolean query
            boolean_query = await self._generate_boolean_query(
                refined_query=refined_query,
                keywords=keywords,
                filters=filters,
                extracted_data=extracted_data
            )
            
            if boolean_query:
                self.log_operation("Boolean query generated successfully", boolean_query[:100] + "...")
                return {
                    "boolean_query": boolean_query,
                    "query_generation_status": "success",
                    "messages": [HumanMessage(content=f"Generated Boolean query: {boolean_query}")]
                }
            else:
                return {"error": "Failed to generate Boolean query"}
                
        except Exception as e:
            self.logger.error(f"Query generation failed: {e}")
            return {"error": f"Query generation error: {str(e)}"}
    
    async def _generate_boolean_query(self, refined_query: str, keywords: List[str], 
                                    filters: List[Dict], extracted_data: Dict) -> Optional[str]:
        """
        Generate Boolean query using LLM with proper syntax.
        
        Args:
            refined_query: User's refined query
            keywords: List of important keywords
            filters: List of exact filters to apply
            extracted_data: Extracted products, brands, timeline, location, etc.
            
        Returns:
            Boolean query string or None if generation fails
        """
        try:
            # Create system prompt with examples
            system_prompt = f"""You are a Boolean Query Generator for social media data retrieval.

Your task is to create Boolean queries using AND, OR, NEAR, NOT operators.

Available Syntax Keywords: {', '.join(self.query_patterns.get('syntax_keywords', []))}

Example Queries:
{chr(10).join(self.query_patterns.get('example_queries', []))}

Rules:
1. Use AND for required terms that must appear together
2. Use OR for alternative terms (brands, products, synonyms)
3. Use NEAR for terms that should appear close to each other
4. Use NOT to exclude unwanted content
5. Use parentheses to group logical operations
6. Include source filters when specified
7. Consider sentiment/emotion from the refined query

Generate a Boolean query that captures the user's intent effectively."""

            # Create user prompt with context
            user_prompt = f"""Generate a Boolean query for this request:

Refined Query: {refined_query}

Keywords: {keywords}

Filters: {json.dumps(filters, indent=2)}

Extracted Data: {json.dumps(extracted_data, indent=2)}

Generate a Boolean query that:
- Includes the most important keywords with proper operators
- Applies the specified filters
- Reflects the sentiment/intent from the refined query
- Uses proper Boolean syntax

Return only the Boolean query string, no explanation needed."""

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
    
    async def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Alternative interface for LangGraph compatibility.
        """
        return await self.__call__(input_data)


def create_query_generator_agent(llm=None) -> ModernQueryGeneratorAgent:
    """
    Factory function to create a Modern Query Generator Agent.
    
    Args:
        llm: Language model instance (optional)
        
    Returns:
        Configured ModernQueryGeneratorAgent instance
    """
    return ModernQueryGeneratorAgent(llm=llm)