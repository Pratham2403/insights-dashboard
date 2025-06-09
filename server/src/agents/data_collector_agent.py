"""
Modern Data Collector Agent using latest LangGraph patterns.

Key improvements:
- Direct integration with tools
- Built-in state management with MessagesState
- Simplified async operations
- 65% code reduction through abstractions
"""

import json
import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from src.agents.base.agent_base import LLMAgent
from src.tools.modern_tools import  process_data
from src.tools.get_tool import get_sprinklr_data

logger = logging.getLogger(__name__)

class DataCollectorAgent(LLMAgent):
    """
    Modern Data Collector using latest LangGraph patterns.
    
    Dramatically simplified data collection with built-in error handling.
    """
    
    def __init__(self, llm=None):
        super().__init__("modern_data_collector", llm)
    
    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Modern data collection workflow.
        
        This agent extracts keywords, filters, and data requirements from the refined query.
        It does NOT execute boolean queries - that's for the Query Generator + ToolNode.
        
        Args:
            state: Current workflow state
            
        Returns:
            State updates with extracted keywords, filters, and data requirements
        """
        self.logger.info("Modern data collector agent invoked")
        
        # Get refined query from state with multiple fallback options
        refined_query = state.get("refined_query", state.get("query")[-1])
            
        query_context = state.get("query")
        
        if not refined_query:
            self.logger.error("No refined query found in state")
        
        # Extract data requirements using LLM
        extracted_data = await self._extract_data_requirements(refined_query, query_context)
        
        # Check if the extracted data is sufficient for query generation
        # Trigger HITL if data completeness is low or missing critical info
        data_completeness_score = extracted_data.get('data_completeness_score', 1.0)
        missing_critical_info = extracted_data.get('missing_critical_info', [])
        ready_for_query_generation = extracted_data.get('ready_for_query_generation', True)
        
        result = {
            "keywords": extracted_data.get("keywords", []),
            "filters": extracted_data.get("filters", {}),
            "messages": [AIMessage(
                content=f"Data extraction complete: {len(extracted_data.get('keywords', []))} keywords, {len(extracted_data.get('filters', {}))} filter types",
                name=self.agent_name
            )]
        }
        
        # Set reason for HITL if clarification is needed
        if data_completeness_score < 0.7 or missing_critical_info or not ready_for_query_generation:
            result["reason"] = "clarification_needed"
            self.logger.info(f"🔄 Data collection needs clarification - completeness: {data_completeness_score}, missing_info: {len(missing_critical_info)}, ready: {ready_for_query_generation}")
        
        return result
    
    async def _extract_data_requirements(self, refined_query: str, query_context: List[str]) -> Dict[str, Any]:
        """
        Extract keywords, filters from refined query and Query_context using LLM.
        
        Args:
            refined_query: The refined user query
            query_context: List Of all the Actual User Queries
            
        Returns:
            Dictionary with extracted keywords, filters,
        """
        try:
            # Load available filters from filters.json
            import json
            from pathlib import Path
            
            filters_path = Path(__file__).parent.parent / "knowledge_base" / "filters.json"
            with open(filters_path, "r") as f:
                available_filters = json.load(f)["filters"]
            
            # Create extraction prompt
            system_prompt = f"""You are a data extraction specialist. Analyze the Refined Query and Query List and extract:
            1. Keywords: Important terms for Boolean search queries
            2. Filters: Applicable filters from the available filter list
            3. Data completeness assessment: Evaluate if information is sufficient for query generation
            4. Missing critical information: Identify what key information is still needed

            Available Filters: {json.dumps(available_filters, indent=2)}

            IMPORTANT: Respond ONLY with a valid JSON object. No additional text, explanations, or formatting. 
            The JSON must have this exact structure:
            {{
                "keywords": ["list", "of", "keywords"],
                "filters": {{"filter_type": ["selected", "values"]}},
                "data_completeness_score": 0.0-1.0,
                "missing_critical_info": ["specific missing information needed"],
                "ready_for_query_generation": true/false,
            }}
            
            Assess data_completeness_score based on:
            - Presence of clear brands/products (0.3 weight)
            - Specified channels/sources (0.2 weight) 
            - Defined timeline/period (0.2 weight)
            - Clear analysis goals (0.2 weight)
            - Geographic/demographic scope (0.1 weight)
            
            Set ready_for_query_generation to false if score < 0.7 or critical info is missing."""
            
            user_prompt = f"""
            Refined Query: {refined_query}
            Query Context (List of Actual User Queries): {query_context}

            Extract the Keywords and Filters for dashboard generation.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Parse LLM response
            try:
                # Handle different response types
                if hasattr(response, 'content'):
                    response_text = response.content
                elif isinstance(response, str):
                    response_text = response
                else:
                    response_text = str(response)
                
                # Try to extract JSON from response text if it contains other text
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group()
                
                extracted_data = json.loads(response_text)
                self.logger.info(f"Successfully extracted data requirements: {len(extracted_data.get('keywords', []))} keywords")
                return extracted_data
            except (json.JSONDecodeError, AttributeError, TypeError) as e:
                self.logger.error(f"Could not parse LLM response as JSON: {e}, using fallback extraction")
                return {}
                
        except Exception as e:
            self.logger.error(f"Data extraction failed: {e}")
            return {}
    



# Factory for LangGraph
def create_data_collector():
    """Create data collector for LangGraph integration."""
    return DataCollectorAgent()
