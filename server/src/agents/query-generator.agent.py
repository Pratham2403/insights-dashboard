"""
# Boolean Keyword Query Generator Agent
This agent is responsible for generating a boolean keyword query based on the Data provided by the Data Collector Agent. It constructs a query that can be used to fetch data from the Sprinklr API, ensuring that it adheres to the boolean logic required for effective data retrieval.

# Knowledge Base Context:
- This Agent has Access to the Knowledge Base Context which contains the list of example boolean keyword queries with certain description of that Query. This Boolean Keyword Query will be used to fetch the data from the Sprinklr API. 
- This agent in in its Prompt will have the Rules for constructing the boolean keyword query, 

# Functionality:
- Based on the Data Provided by the Data Collector Agent, the Boolean Keyword Query Generator Agent will analyze the data and construct a boolean keyword query that can be used to fetch data from the Sprinklr API.
- The agent will ensure that the query is structured correctly, using appropriate RULES and keywords to filter the data effectively.
- The generated query will be returned to the ToolNode, which will then use it to fetch the data from the Sprinklr API.


# Additional Functionality : 
This Agent May be used by the Data Analyzer Agent to Generate the boolean keyword query for each  Theme (Bucket) of data that it has categorized. This will help in fetching the data related to that specific bucket from the Sprinklr API.


"""

import logging
from typing import Dict, Any, Optional, List
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field
import importlib.util
import os

# Import helper function
def import_module_from_file(filepath, module_name):
    """Helper function to import modules with dots in filenames"""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Get paths
setup_path = os.path.join(os.path.dirname(__file__), '..', 'setup')
rag_path = os.path.join(os.path.dirname(__file__), '..', 'rag')
helpers_path = os.path.join(os.path.dirname(__file__), '..', 'helpers')

# Import the required classes
llm_module = import_module_from_file(os.path.join(setup_path, 'llm.setup.py'), 'llm_setup')
filters_module = import_module_from_file(os.path.join(rag_path, 'filters.rag.py'), 'filters_rag')
prompts_module = import_module_from_file(os.path.join(helpers_path, 'prompts.helper.py'), 'prompts_helper')
states_module = import_module_from_file(os.path.join(helpers_path, 'states.py'), 'states')

LLMSetup = llm_module.LLMSetup
FiltersRAG = filters_module.FiltersRAG
DashboardState = states_module.DashboardState
BooleanQueryData = states_module.BooleanQueryData

# Configure logging
logger = logging.getLogger(__name__)

class QueryGenerationRequest(BaseModel):
    """Request model for query generation"""
    user_data: Dict[str, Any] = Field(..., description="User collected data")
    refined_query: str = Field(..., description="Refined user query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Applied filters")
    theme_data: Optional[Dict[str, Any]] = Field(None, description="Theme-specific data for targeted query generation")

class QueryGeneratorAgent:
    """
    Boolean Keyword Query Generator Agent for creating optimized Sprinklr API queries.
    
    This agent generates boolean keyword queries based on user data and requirements,
    utilizing RAG context from the knowledge base to create effective search queries.
    """
    
    def __init__(self):
        """Initialize the Query Generator Agent"""
        self.llm_setup = LLMSetup()
        self.filters_rag = FiltersRAG()
        self.prompts_module = prompts_module
        self.llm = self.llm_setup.get_agent_llm("query_generator")
        logger.info("QueryGeneratorAgent initialized successfully")
    
    async def generate_query(self, request: QueryGenerationRequest) -> Dict[str, Any]:
        """
        Generate a boolean keyword query based on user data and requirements.
        
        Args:
            request: QueryGenerationRequest containing user data and context
            
        Returns:
            Dict containing the generated boolean query and metadata
        """
        try:
            logger.info("Starting boolean query generation")
            
            # Get RAG context for query patterns
            rag_context = await self._get_rag_context(request)
            
            # Generate the boolean query
            query_response = await self._generate_boolean_query(request, rag_context)
            
            # Validate and format the query
            formatted_query = await self._validate_and_format_query(query_response)
            
            return {
                "success": True,
                "boolean_query": formatted_query["query"],
                "query_metadata": formatted_query["metadata"],
                "confidence": formatted_query.get("confidence", 0.8),
                "query_components": formatted_query.get("components", {}),
                "estimated_results": self._convert_estimated_results_to_int(formatted_query.get("estimated_results", "unknown"))
            }
            
        except Exception as e:
            logger.error(f"Error in query generation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_query": await self._generate_fallback_query(request)
            }
    
    async def generate_theme_query(self, theme_data: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a boolean query for a specific theme/bucket.
        
        Args:
            theme_data: Data for the specific theme
            user_context: Original user context and requirements
            
        Returns:
            Dict containing the theme-specific boolean query
        """
        try:
            logger.info(f"Generating theme-specific query for: {theme_data.get('name', 'Unknown Theme')}")
            
            # Create theme-specific request
            theme_request = QueryGenerationRequest(
                user_data=user_context,
                refined_query=f"Generate query for theme: {theme_data.get('name', '')} - {theme_data.get('description', '')}",
                theme_data=theme_data
            )
            
            # Get theme-specific RAG context
            rag_context = await self._get_theme_rag_context(theme_data)
            
            # Generate theme-specific query
            query_response = await self._generate_theme_specific_query(theme_request, rag_context, theme_data)
            
            return {
                "success": True,
                "theme_name": theme_data.get("name"),
                "boolean_query": query_response["query"],
                "query_metadata": query_response["metadata"],
                "theme_confidence": query_response.get("confidence", 0.8)
            }
            
        except Exception as e:
            logger.error(f"Error in theme query generation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "theme_name": theme_data.get("name"),
                "fallback_query": await self._generate_theme_fallback_query(theme_data)
            }
    
    async def _get_rag_context(self, request: QueryGenerationRequest) -> Dict[str, Any]:
        """Get relevant RAG context for query generation"""
        try:
            # Extract key terms from user data and refined query
            search_terms = self._extract_search_terms(request)
            search_query = " ".join(search_terms[:5])  # Use top 5 terms for search
            
            # Get query patterns from RAG using correct method names
            query_patterns = self.filters_rag.search_keyword_patterns(search_query)
            
            # Get relevant filters using correct method name
            relevant_filters = self.filters_rag.search_filters(search_query)
            
            return {
                "query_patterns": query_patterns,
                "relevant_filters": relevant_filters,
                "search_terms": search_terms
            }
            
        except Exception as e:
            logger.error(f"Error getting RAG context: {str(e)}")
            return {"query_patterns": [], "relevant_filters": [], "search_terms": []}
    
    async def _get_theme_rag_context(self, theme_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get RAG context specific to a theme"""
        try:
            theme_terms = [
                theme_data.get("name", ""),
                theme_data.get("description", ""),
                *theme_data.get("keywords", [])
            ]
            search_query = " ".join(filter(None, theme_terms[:5]))  # Filter out empty strings
            
            query_patterns = self.filters_rag.search_keyword_patterns(search_query)
            relevant_filters = self.filters_rag.search_filters(search_query)
            
            return {
                "query_patterns": query_patterns,
                "relevant_filters": relevant_filters,
                "theme_terms": theme_terms
            }
            
        except Exception as e:
            logger.error(f"Error getting theme RAG context: {str(e)}")
            return {"query_patterns": [], "relevant_filters": [], "theme_terms": []}
    
    async def _generate_boolean_query(self, request: QueryGenerationRequest, rag_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the main boolean query using LLM"""
        try:
            # Get the query generation prompt
            system_prompt = self.prompts_module.QUERY_GENERATOR_SYSTEM_PROMPT
            
            # Prepare context for the LLM
            context = {
                "user_data": request.user_data,
                "refined_query": request.refined_query,
                "filters": request.filters or {},
                "rag_context": rag_context,
                "query_patterns": rag_context.get("query_patterns", []),
                "relevant_filters": rag_context.get("relevant_filters", [])
            }
            
            # Create the user message
            user_message = f"""
            Please generate a boolean keyword query based on the following context:
            
            Refined User Query: {request.refined_query}
            
            User Data: {request.user_data}
            
            Available Query Patterns: {rag_context.get('query_patterns', [])}
            
            Relevant Filters: {rag_context.get('relevant_filters', [])}
            
            Generate a boolean query that will effectively retrieve relevant data from the Sprinklr API.
            """
            
            # Get response from LLM
            messages = [
                HumanMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Handle both string and message object responses
            if hasattr(response, 'content'):
                response_content = response.content
            else:
                response_content = str(response)
            
            # Parse the response
            return self._parse_query_response(response_content)
            
        except Exception as e:
            logger.error(f"Error generating boolean query: {str(e)}")
            raise
    
    async def _generate_theme_specific_query(self, request: QueryGenerationRequest, rag_context: Dict[str, Any], theme_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a theme-specific boolean query"""
        try:
            system_prompt = self.prompts_module.QUERY_GENERATOR_SYSTEM_PROMPT
            
            user_message = f"""
            Generate a boolean keyword query specifically for this theme:
            
            Theme Name: {theme_data.get('name')}
            Theme Description: {theme_data.get('description')}
            Theme Keywords: {theme_data.get('keywords', [])}
            
            Original Context: {request.refined_query}
            User Data: {request.user_data}
            
            Available Query Patterns: {rag_context.get('query_patterns', [])}
            
            Create a focused boolean query that will retrieve data specifically for this theme.
            """
            
            messages = [
                HumanMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Handle both string and message object responses
            if hasattr(response, 'content'):
                response_content = response.content
            else:
                response_content = str(response)
                
            return self._parse_query_response(response_content)
            
        except Exception as e:
            logger.error(f"Error generating theme-specific query: {str(e)}")
            raise
    
    async def _validate_and_format_query(self, query_response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and format the generated query"""
        try:
            query = query_response.get("query", "")
            
            # Basic validation
            if not query or len(query.strip()) < 3:
                raise ValueError("Generated query is too short or empty")
            
            # Format the query
            formatted_query = {
                "query": query.strip(),
                "metadata": {
                    "generated_at": "2025-06-01",  # Current date
                    "query_type": "boolean_keyword",
                    "validation_status": "passed"
                },
                "confidence": query_response.get("confidence", 0.8),
                "components": self._extract_query_components(query),
                "estimated_results": self._convert_estimated_results_to_int(query_response.get("estimated_results", "medium"))
            }
            
            return formatted_query
            
        except Exception as e:
            logger.error(f"Error validating query: {str(e)}")
            raise
    
    def _extract_search_terms(self, request: QueryGenerationRequest) -> List[str]:
        """Extract key search terms from the request"""
        terms = []
        
        # Extract from refined query
        if request.refined_query:
            terms.extend(request.refined_query.split())
        
        # Extract from user data
        if isinstance(request.user_data, dict):
            for key, value in request.user_data.items():
                if isinstance(value, str):
                    terms.extend(value.split())
                elif isinstance(value, list):
                    terms.extend([str(item) for item in value])
        
        # Clean and filter terms
        cleaned_terms = [term.strip().lower() for term in terms if term.strip() and len(term.strip()) > 2]
        return list(set(cleaned_terms))[:20]  # Limit to 20 most unique terms
    
    def _parse_query_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the LLM response to extract query information"""
        try:
            # This is a simplified parser - in production, you might want more sophisticated parsing
            lines = response_content.strip().split('\n')
            
            query = ""
            confidence = 0.8
            estimated_results = "medium"
            
            for line in lines:
                if "query:" in line.lower():
                    query = line.split(":", 1)[1].strip()
                elif "confidence:" in line.lower():
                    try:
                        confidence = float(line.split(":", 1)[1].strip())
                    except:
                        confidence = 0.8
                elif "estimated" in line.lower() and "results" in line.lower():
                    estimated_results = line.split(":", 1)[1].strip()
            
            if not query:
                # If no structured response, use the entire content as query
                query = response_content.strip()
            
            return {
                "query": query,
                "confidence": confidence,
                "estimated_results": self._convert_estimated_results_to_int(estimated_results)
            }
            
        except Exception as e:
            logger.error(f"Error parsing query response: {str(e)}")
            return {
                "query": response_content.strip(),
                "confidence": 0.5,
                "estimated_results": self._convert_estimated_results_to_int("unknown")
            }
    
    def _extract_query_components(self, query: str) -> Dict[str, List[str]]:
        """Extract components from the boolean query"""
        components = {
            "keywords": [],
            "operators": [],
            "filters": []
        }
        
        # Simple extraction logic
        words = query.split()
        boolean_operators = ["AND", "OR", "NOT", "&&", "||", "!"]
        
        for word in words:
            if word.upper() in boolean_operators:
                components["operators"].append(word.upper())
            elif ":" in word:
                components["filters"].append(word)
            else:
                components["keywords"].append(word)
        
        return components
    
    async def _generate_fallback_query(self, request: QueryGenerationRequest) -> str:
        """Generate a simple fallback query if main generation fails"""
        try:
            # Create a basic query from user data
            terms = self._extract_search_terms(request)
            if terms:
                return " AND ".join(terms[:5])  # Use first 5 terms
            else:
                return "general OR content"
        except:
            return "general"
    
    async def _generate_theme_fallback_query(self, theme_data: Dict[str, Any]) -> str:
        """Generate a fallback query for theme-specific requests"""
        try:
            name = theme_data.get("name", "")
            keywords = theme_data.get("keywords", [])
            
            if keywords:
                return " OR ".join(keywords[:3])
            elif name:
                return name
            else:
                return "theme"
        except:
            return "theme"
    
    def _convert_estimated_results_to_int(self, estimated_results: Any) -> Optional[int]:
        """Convert estimated_results string values to integers."""
        if isinstance(estimated_results, int):
            return estimated_results
        elif isinstance(estimated_results, str):
            # Map common string values to integers
            mapping = {
                "low": 100,
                "medium": 1000,
                "high": 10000,
                "unknown": None,
                "small": 50,
                "large": 50000
            }
            return mapping.get(estimated_results.lower(), None)
        else:
            return None
    
    # State management methods for LangGraph integration
    async def process_state(self, state: DashboardState) -> DashboardState:
        """Process the dashboard state for query generation"""
        try:
            logger.info("Processing state for query generation")
            
            # Create request from state
            request = QueryGenerationRequest(
                user_data=state.user_collected_data.data if state.user_collected_data else {},
                refined_query=state.query_refinement_data.refined_query if state.query_refinement_data else "",
                filters=state.user_collected_data.filters if state.user_collected_data else None
            )
            
            # Generate the query
            result = await self.generate_query(request)
            
            # Update state
            if result["success"]:
                # Convert query_components from dict to list if needed
                query_components = result["query_components"]
                if isinstance(query_components, dict):
                    # Extract all components from the dict and flatten to a list
                    components_list = []
                    for category, items in query_components.items():
                        if isinstance(items, list):
                            components_list.extend(items)
                        else:
                            components_list.append(str(items))
                    query_components = components_list
                elif not isinstance(query_components, list):
                    query_components = [str(query_components)]
                
                boolean_query_data = BooleanQueryData(
                    boolean_query=result["boolean_query"],
                    query_components=query_components,
                    target_channels=result.get("target_channels", []),
                    filters_applied=result.get("filters_applied", {}),
                    estimated_results=result.get("estimated_results")
                )
                state.query_generation_data = boolean_query_data
                state.boolean_query_data = boolean_query_data  # Also set legacy field
                state.workflow_status = "query_generated"
                logger.info("Boolean query generated successfully")
            else:
                state.errors.append(f"Query generation failed: {result.get('error', 'Unknown error')}")
                state.workflow_status = "query_generation_failed"
                logger.error("Query generation failed")
            
            return state
            
        except Exception as e:
            logger.error(f"Error processing state: {str(e)}")
            state.errors.append(f"Query generation error: {str(e)}")
            state.workflow_status = "query_generation_failed"
            return state