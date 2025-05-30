"""
Query Generation Agent for the Sprinklr Insights Dashboard.
"""
from typing import Dict, List, Any, Optional
import json
import logging
from pathlib import Path
import os
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config.settings import settings
from app.models.state import UserRequirements, QueryBatch
from uuid import uuid4
from datetime import datetime


logger = logging.getLogger(__name__)


# Define system prompt for the Query Generation agent
QUERY_GEN_SYSTEM_PROMPT = """You are an expert in generating Boolean keyword queries for social media and news analysis.
Your task is to convert user requirements into optimized Boolean keyword queries that will be used to retrieve relevant data.

You must follow these rules when generating queries:
1. Use Boolean operators: AND, OR, NOT, NEAR, ONEAR
2. Group related terms with parentheses ()
3. Use quotes for exact phrases
4. Create focused queries for specific combinations of products, channels, and goals
5. Include relevant hashtags and common variations of terms
6. Exclude irrelevant content (e.g., spam, promotions)
7. Maximum query length is 500 tokens
8. Generate multiple targeted queries rather than a single broad query

Your queries should follow the syntax patterns in these examples:
- ( samsungs8 OR s8 OR galaxys8 OR #s8 OR #galaxys8 OR #samsungs8 )
- ("Hisense air purifier" OR (Hisense AND "air purifier"))
- ((specific features) AND (brand terms) AND NOT (spam terms))

For each product-channel-goal combination, generate 2-3 optimized queries.
"""

# Load query patterns from file for examples
def load_query_patterns():
    """
    Load query patterns from JSON file.
    
    Returns:
        Dictionary containing query patterns.
    """
    try:
        file_path = Path(__file__).parents[2] / "keyword_query_patterns.json"
        if not file_path.exists():
            # Try an alternative path
            file_path = Path(os.getcwd()) / "keyword_query_patterns.json"
        
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading query patterns: {e}")
        return {
            "syntax_keywords": ["AND", "OR", "NOT", "ONEAR", "NEAR", "(", ")"],
            "example_queries": [
                "( samsungs8 OR s8 OR galaxys8 OR #s8 OR #galaxys8 OR #samsungs8 )",
                "(\"Hisense air purifier\" OR (\"Hisense\" AND \"air purifier\"))"
            ]
        }


class QueryGenerationAgent:
    """
    Agent responsible for generating Boolean keyword queries based on user requirements.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the Query Generation agent.
        
        Args:
            model_name: The name of the language model to use.
        """
        self.model_name = model_name or settings.DEFAULT_MODEL_NAME
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0.2,
            max_tokens=2000,
            google_api_key=settings.GEMINI_API_KEY
        )
        self.query_patterns = load_query_patterns()
    
    async def generate_queries(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Boolean keyword queries based on user requirements.
        
        Args:
            state: The current state of the conversation.
            
        Returns:
            Updated state with generated queries.
        """
        # Initialize query_batches if not present
        if "query_batches" not in state:
            state["query_batches"] = []
        
        # Get user requirements
        user_requirements = UserRequirements(**state["user_requirements"])
        
        # Check if all required fields are filled
        if not user_requirements.is_complete():
            # Log missing fields and return state unchanged
            missing_fields = user_requirements.get_missing_fields()
            logger.warning(f"Cannot generate queries: missing fields {missing_fields}")
            
            # Add a message to the state
            state["messages"].append({
                "role": "system",
                "content": f"Cannot generate queries: missing fields {missing_fields}"
            })
            
            return state
        
        # Generate queries
        queries = await self._generate_query_batch(user_requirements)
        
        # Create query batch
        query_batch = QueryBatch(
            id=uuid4(),
            queries=queries,
            created_at=datetime.now(),
            metadata={
                "products": user_requirements.products,
                "channels": user_requirements.channels,
                "goals": user_requirements.goals,
                "time_period": user_requirements.time_period,
                "focus_areas": user_requirements.focus_areas
            }
        )
        
        # Add query batch to state
        state["query_batches"].append(query_batch.dict())
        
        # Update current step
        state["current_step"] = "QUERY_GENERATION"
        
        return state
    
    async def _generate_query_batch(self, requirements: UserRequirements) -> List[str]:
        """
        Generate a batch of Boolean keyword queries based on user requirements.
        
        Args:
            requirements: The user requirements.
            
        Returns:
            List of generated queries.
        """
        # Construct prompt for query generation
        prompt_template = """
        Generate Boolean keyword queries based on the following requirements:
        
        Products: {products}
        Channels: {channels}
        Goals: {goals}
        Time Period: {time_period}
        Focus Areas: {focus_areas}
        Additional Notes: {additional_notes}
        
        Use the following Boolean operators: AND, OR, NOT, NEAR, ONEAR
        Group related terms with parentheses ()
        Use quotes for exact phrases
        
        Here are some example query patterns for reference:
        {example_queries}
        
        For each product-channel-goal combination, generate 2-3 optimized queries.
        
        Return your response as a JSON array of query strings.
        """
        
        # Format example queries for prompt
        example_queries_text = "\n".join([f"- {q}" for q in self.query_patterns["example_queries"]])
        
        # Format prompt with user requirements
        prompt = prompt_template.format(
            products=", ".join(requirements.products),
            channels=", ".join(requirements.channels),
            goals=", ".join(requirements.goals),
            time_period=requirements.time_period,
            focus_areas=", ".join(requirements.focus_areas) if requirements.focus_areas else "N/A",
            additional_notes=requirements.additional_notes or "N/A",
            example_queries=example_queries_text
        )
        
        # Create messages for the LLM
        messages = [
            SystemMessage(content=QUERY_GEN_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        # Generate queries
        response = await self.llm.ainvoke(messages)
        
        try:
            # Parse the JSON response
            # Extract JSON from response if needed
            content = response.content
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                # Try to find JSON array between square brackets
                json_match = re.search(r'(\[.*\])', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            
            queries = json.loads(content)
            
            # Validate and filter queries
            valid_queries = []
            for query in queries:
                if isinstance(query, str) and len(query) > 0:
                    # Check if query is within token limit
                    if len(query) <= settings.MAX_QUERY_TOKENS:
                        valid_queries.append(query)
                    else:
                        logger.warning(f"Query exceeds token limit: {query[:100]}...")
            
            return valid_queries
            
        except Exception as e:
            logger.error(f"Error parsing query generation response: {e}")
            
            # Try to extract any query-like strings from the response
            import re
            
            # Look for text between parentheses that contains boolean operators
            potential_queries = re.findall(r'\([^()]*(?:AND|OR|NOT|NEAR|ONEAR)[^()]*\)', response.content)
            
            if potential_queries:
                return potential_queries[:5]  # Limit to 5 queries
            
            # If all else fails, return a basic query based on the products
            basic_queries = []
            for product in requirements.products:
                basic_query = f'("{product}" OR #{product.replace(" ", "")})'
                basic_queries.append(basic_query)
            
            return basic_queries
