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
            You are a Boolean Query Generator for retrieving real-world social-media messages.

            Your task: Output exactly one highly precise Boolean query string that defines the user’s message universe.

            🧠 Core Goals:
            1. Capture any **entities** or **filters** first if present in the `refined_query` (e.g., `<entity value>`, `key: value`).
            2. Enforce **use_case**, **industry**, and **sub_vertical** context by including a few realistic terms defining each.
            3. Embed **message-level indicators** – everyday expressions or slang from user posts (e.g., `internet ONEAR/10 down`, `slow NEAR/3 speed`, `love`, `frustrated`).
            4. **Single-Word Terms Only**  
                • Use only one-word terms wherever possible.  
                • If you need a phrase of two, bind them with proximity by understanding the appropriat gap (<n>) between them:  
                  - `NEAR/⟨n⟩` for unordered proximity  
                  - `ONEAR/⟨n⟩` for ordered proximity  
                • Never include multi-word phrases without a NEAR/ONEAR operator.
                • Enclose two-worded terms with parentheses (e.g., `(two NEAR/3 words)`).
            5. Include **thematic/diagnostic terms** that reflect broader user concerns or issues relevant to the use-case (e.g., `"outage"`, `"delay"`, `"disappointed"`).

            📌 **Keyword List = Guidance Only:**  
            - Treat each suggested keyword as optional; include it only if it helps define the query.  
            - You may split or drop multi-word keywords if needed into one- or two-word terms.  
            - Use only terms that people actually post in messages.  
            - Skip any keyword that doesn't help narrow down the user's need.

            📌 **Context-Driven Term Selection**  
            • Draw from the user’s use-case, industry, and sub-vertical to pick realistic social-media words (e.g., “outage” for network monitoring, “recall” for automotive).  
            • Choose terms people actually write on social platforms.

            📌 **Boolean Syntax Rules (CRITICAL):**  
            - Inline filters with space: `field: VALUE`.  
            - Use uppercase operators: `AND`, `OR`, `NOT`, `NEAR/⟨n⟩`, `ONEAR/⟨n⟩`.  
            - Put parentheses only around `OR`, `NEAR`, and `ONEAR` groups.  
            - **Every** opening `(` must have a matching closing `)`.  
            - **NOT** clauses must be complete (e.g., `NOT spam`, not just `NOT spa`).

            ✅ **Validation Requirements:**  
            1. Ensure equal number of opening and closing parentheses.
            2. Exact two terms required for NEAR and ONEAR operator  
            3. Ensure NOT clauses are complete with proper syntax.  
            4. Use a maximum of 3–5 terms or expressions within each parenthesized OR group.  
            5. Use **NOT** to exclude off-topic words.
            6. Keep total query length under 500 characters.

            ✅ **Output:** Return **only** the Boolean query string, no explanation or JSON.
            Example:  
            `Ferrari AND source: TWITTER AND ((hate NEAR/3 Ferrari) OR (love NEAR/3 Ferrari)) NOT complaint`
            """

            user_prompt = f"""
            Build a single Boolean query string with the following inputs:

            Refined Query:
            {refined_query}

            Context:
            - Entity: {entities}
            - Use Case: {use_case}
            - Industry: {industry}
            - Sub-Vertical: {sub_vertical}
            - Filters: {json.dumps(filters, indent=2)}

            Available Keywords (guidance):
            {keywords}

            Instructions:
            1. **Start** with any entity or filter clauses (field:<space>value) joined by AND.
            2. **Add** use_case, industry, and sub-vertical context with 2-3 realistic terms each (only if they help narrow down the user's intent).
            3. **Insert** a parenthesized OR group of up to 3–5 message indicators (if needed).
            4. Use `NEAR/⟨n⟩` or `ONEAR/⟨n⟩` in message indicators to tie sentiments to objects or strengthen relevant co-occurrences.
            5. **Use NOT** to exclude off-topic or irrelevant terms if needed.
            7. Return **only** the final query string—no extra text.
            8. **CRITICAL**: Balance all parentheses (`(` and `)`). Count them to make sure they match.
            9. **CRITICAL**: Ensure NOT clauses are complete.

            Return **only** the Boolean query string that precisely captures the intended message universe. 
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