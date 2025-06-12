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
            entities = state.get("entities", [])
            industry = state.get("industry", "")
            sub_vertical = state.get("sub_vertical", "")
            use_case = state.get("use_case", "")
            defaults_applied = state.get("defaults_applied", {})

            
            if not refined_query:
                logger.warning("No refined query found, using keywords only for Boolean query generation")
            
            # Generate Boolean query with all available data
            boolean_query = await self._generate_boolean_query(
                refined_query=refined_query,
                keywords=keywords,
                filters=filters,
                entities=entities,
                industry=industry, 
                sub_vertical=sub_vertical,
                use_case=use_case,
                defaults_applied=defaults_applied
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

    async def _generate_boolean_query(self, refined_query: str, keywords: List[str], filters: List[Dict], entities: List[str], industry: str, sub_vertical: str, use_case: str, defaults_applied: Dict) -> Optional[str]:
        """
        Generate Boolean query using LLM with proper syntax.
        
        Args:
            refined_query: User's refined query
            keywords: List of keywords
            filters: List of exact filters to apply
            entities: List of entities
            industry: Industry string
            sub_vertical: Sub-vertical string
            use_case: Use case string
            defaults_applied: Dictionary of defaults applied

        Returns:
            Boolean query string or None if generation fails
        """
        try:

            system_prompt = f"""
            You are a Boolean Query Generator for retrieving raw user messages that exactly match the user’s refined intent.

            Your output **must** be one single Boolean query string, formatted to:

            1. **Define the universe first**  
               • Start with the entity or filter (if any), e.g. `entity: FERRARI` or `source: TWITTER`.  
               • Then join with `AND`.

            2. **Enforce use‐case, industry & sub‐vertical**  
               • Select 1–2 strong keywords that express the use‐case (e.g., monitoring, sentiment).  
               • Select 1–2 keywords for industry/sub‐vertical context (e.g., automotive, manufacturing).  
               • Join each concept group with `AND`.

            3. **Embed message‐level indicators**  
               • Choose 3–5 everyday terms or short phrases people write (e.g., love, hate, worst experience).  
               • Group synonyms/variants with `OR` in parentheses: `(hate OR dislike)`.

            4. **Use proximity or exclusions**  
               • Use `NEAR/<n>` or `ONEAR/<n>` to link sentiment to object: e.g. `"hate" NEAR/3 "Ferrari"`.  
               • Use `NOT` to remove unwanted topics.

            **Operator rules**  
            - **AND**: join distinct concepts  
            - **OR**: within‐group synonyms/variants only  
            - **NEAR/<n>**, **ONEAR/<n>**: proximity  
            - **NOT**: exclusion  

            **Syntax**  
            - Wrap multi‐word phrases in escaped quotes: `\"...\"`  
            - Inline filters as `field:<space>value`  
            - Separate every token with spaces  
            - Use parentheses for OR groups only  

            **Example final query**  
            entity: FERRARI AND source: TWITTER AND (monitoring OR tracking) AND automotive AND ("hate" NEAR/3 "Ferrari" OR "love" NEAR/3 "Ferrari") NOT "complaint"

            Return **only** the Boolean query string, no explanation.
            """


            user_prompt = f"""
            Generate one Boolean query string for these details:

            Refined Query:
            {refined_query}

            Context:
            - Entity: {entities}
            - Use Case: {use_case}
            - Industry: {industry}
            - Sub‐Vertical: {sub_vertical}
            - Filters: {json.dumps(filters, indent=2)}
            - Defaults Applied: {json.dumps(defaults_applied, indent=2)}

            Available Keywords:
            {keywords}

            Follow these steps in your query:
            1. Start with the entity filter (if present) then `AND`.  
            2. Add use‐case and industry/sub‐vertical keywords, each joined by `AND`.  
            3. Add a parenthesized group of 3–5 message‐level indicators with `OR`.  
            4. Use `NEAR/⟨n⟩` or `ONEAR/⟨n⟩` to link sentiment to the entity when beneficial.  
            5. Use `NOT` to exclude irrelevant terms if needed.  
            6. Wrap phrases in `\"...\"`, filters as `field: VALUE`, and use uppercase operators.  
            7. Return only the final Boolean query string.  
            """



            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.safe_llm_call(messages)
            
            if response:
                # Clean up the response - remove quotes and extra whitespace
                boolean_query = response.strip().strip('"').strip("'").strip("`").strip()
                
                # Validate that it contains Boolean operators
                if any(op in boolean_query.upper() for op in ['AND', 'OR', 'NOT', 'NEAR', 'ONEAR']):
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