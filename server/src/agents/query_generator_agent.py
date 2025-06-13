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
                keywords=[],
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
                logger.error("Failed to generate Boolean query in Query Generator Agent")
                return {"error": "Failed to generate Boolean query in Query Generator Agent"}
                
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


            system_prompt = """
            You are a Boolean Query Generator designed to retrieve real-world user-generated messages (e.g., social media, reviews, forums) from a database.

            Your task is to return exactly **one highly accurate Boolean query string** that defines the user’s intended message universe.

            ---

            🎯 OBJECTIVE:
            Generate a query that:
            • Reflects the user’s intent based on the refined query, entity, use-case, industry, and sub-vertical.  
            • Uses realistic language and words people actually post, speak and write on social media, reviews, and forums (including slang).  
            • Maximizes relevant coverage without over-filtering.

            ---

            🧠 STRUCTURE & LOGIC:

            1. **Start with Entities + Filters (if available)**  
               - For each entity, group synonyms, nicknames, hashtags, and common misspellings using `OR`:  
                 `(entity OR alias OR #hashtag)`  
               - If filters are present, include them as `field: VALUE` and join filters/entities with `AND`.

            2. **Define Use-Case / Industry Context**  
               - Use word or terms that real users use to talk about the use-case or pain point (e.g., plan, service, refund, quality, wait, pricing).  
               - Include 1 or 2 **distinct concept groups**, joined by `OR` or `AND`, that help define the message universe based on the refined query, entity, use-case, industry, and sub-vertical.

            3. **Express Message-Level Indicators**  
               - Use expressions that indicate emotion, complaint, action, outcome, expectation, etc.  
               - Combine synonymous or similar terms in OR groups: `(happy OR joyful OR (not NEAR/2 sad))`  
               - If using multi-word ideas, connect them using `NEAR/n` or `ONEAR/n`:
                 - `NEAR/n`: unordered proximity (e.g., “internet NEAR/5 down”)  
                 - `ONEAR/n`: ordered proximity (e.g., “payment ONEAR/3 failed”)  
               - Do **not** use plain multi-word strings without NEAR/ONEAR. `(slow OR broken OR (not NEAR/2 working))`

            ---

            ⚙️ BOOLEAN OPERATORS & RULES:

            • `AND`: Only between unrelated concepts (e.g., entity AND intent).  
            • `OR`: For synonyms, variants, or near-equivalent expressions.  
            • `NEAR/n` or `ONEAR/n`: Only when semantic closeness matters; max 2–3 expressions.  
            • `NOT`: To remove clear false positives. Use sparingly and accurately.

            ---

            📌 SYNTAX & VALIDATION RULES:

            1. Wrap multi-word terms with proximity: `(term NEAR/3 term)`  
            2. Use parentheses only around OR or proximity groups.  
            3. Ensure every opening `(` has a matching `)`  
            4. Use UPPERCASE operators only: `AND`, `OR`, `NOT`, `NEAR/n`, `ONEAR/n`  
            5. Use field filters as `field: VALUE` with a space after the colon  
            6. Avoid joining soft topics (e.g., telecom AND mobile) — prefer OR or NEAR/10  
            7. Do not exceed **500 characters** total length.  
            8. Do not use more than:
               - 2 `AND` groups (core concept joins only)  
               - 3 `NEAR/ONEAR` expressions  
               - 3-8 terms per `OR` group

            ---

            ✅ **FINAL CHECKLIST BEFORE OUTPUT**:

            - Does the boolean query reflect the full user intent?
            - Are terms written in the way real people talk or post online?
            - Are NEAR/ONEAR/AND used for precision—not overused?
            - The Number of `AND` groups should be minimal (ideally 1-2).
            - Is the query concise, readable, and within length limits?
            - You should not be using any formal or business terms unless they are commonly used in public messages.

            Return only the final Boolean query string. No explanations or formatting.

            """

            
            user_prompt = f"""
            Build a single Boolean query string using the following inputs:
            
            📌 Refined Query:
            {refined_query}
            
            📌 Context:
            - Entity: {entities}
            - Use Case: {use_case}
            - Industry: {industry}
            - Sub-Vertical: {sub_vertical}
            - Filters: {json.dumps(filters, indent=2)}
            
            📌 Available Keywords (guidance only):
            {keywords}
            
            ---
            
            📋 Instructions:
            
            1. Start with an OR group of synonyms for each entity (if available):  
               e.g., `(BrandX OR #BrandX OR common alias)`  
               Then AND any filter(s) if it is relevant to the intent and use-case using `field: VALUE` format.

            2. Add use-case / industry / problem context using common social message terms (e.g., refund, wait, pricing, delay).  
               - Group alternatives with OR  
               - Join unrelated concepts using `AND` 
            3. Use NEAR/n or ONEAR/n if two terms must appear closely (e.g., “signal NEAR/5 lost”)  
               - Limit total NEAR/ONEAR usage to 2–3  
               - Use `n` between 2–10 based on concept
            
            4. Use NOT only if the there is need to remove clear false positives.
            - Use sparingly and accurately (e.g., “NOT spam” or “NOT NEAR/2 irrelevant”)
            5. Group synonyms or similar terms with OR, e.g., `(happy OR joyful OR (not NEAR/2 sad))`
            6. Prevent using AND between soft topics (e.g., telecom AND mobile) — prefer OR or NEAR/10.
            7. Limit using AND as much as possible, ideally 1-2 groups.
            8. Don’t use formal or business terms unless people use them casually in public messages.
            9. Keep query under 500 characters.
            10. Do not use Two- or more worded strings without NEAR/ONEAR.
            11. Return only the Boolean query string — no explanations or text.
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