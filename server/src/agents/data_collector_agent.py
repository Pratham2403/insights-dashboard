"""
# Data Collector Agent
This agent is responsible for collecting data from the user based on the refined query / JSON Object provided by the Query Refiner Agent. It interacts with the user to gather additional information, clarifies any ambiguities, and ensures that all necessary data is collected before proceeding with further processing.

# Agent Knowledge Base Context: 
This agent has the Context from the knowledge base of some pre-existing and Complete User Prompts, and Some Completed Use Cases. This Present in the Form of a simple txt file that contains the list of all the available and existing filters / keywords in the Sprinklr Dashboard. This will be used to search / improve the user query and generate a more refined query that can be used to fetch the data from the Sprinklr API.

# Functionality:
- Based on the refined query / JSON provided by the Query Refiner Agent, the Data Collector Agent will analyze the query and identify any missing information or additional data that needs to be collected from the user.
- The missing information can include specific filters, keywords, or any other relevant data that is necessary to complete the user request, which the agent will undestand from its Knowledgebase
- This Agents then with the HITL Confirms the data with the user and collects the additional information.
- The additional Information is then Again sent to the Query Refiner Agent for further processing.
- And this happens in loop until the user is satisfied with the data collected and the query is complete.
- After the user satisfaction, this data is sent to the Boolean Keyword Query Generator Ageent for Making the final query that can be used to fetch the data from the Sprinklr API.

# Example:
Input: 
{
    "refined_query": "Brand Health Monitoring",
    "filters": {
        "topic": "brand health monitoring",
    }
}

Agent Will Understand that : 
- The user is interested in monitoring the health of their brand on social media.
- The user wants to focus on a specific topic related to brand health monitoring.
- The user may want to analyze data from multiple social media channels.
- The User may want to kno the number of times their brand has been mentioned in the last 30 days.
- What was the sentiment of the mentions, and what were the top channels where their brand was mentioned.
- Key Topics that were discussed about their Brancd on Different Channels.
- What are the top influencers talking about their brand on social media.
- What are the key PR Metrics.

Then the Data is Appropirately Filled into the JSON Object and returned to the Query Refiner Agent for further processing with HITL

# The LLM Will Figure out about the Filters based on the Context
Output: 
{
    "refined_query": "Brand Health Monitoring",
    "agent_query": ["
    "What are the key metrics for brand health monitoring?",
    "What are the top channels where the brand is mentioned?",
    "What is the sentiment of the brand mentions?",
    "What are the key topics discussed about the brand?",
    "Who are the top influencers talking about the brand?",
    "What are the key PR metrics for the brand?"
    ],  
    "filters": {
        "topic": "brand health monitoring",
    }
}  
}


"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)

class DataCollectorAgent:
    """
    Data Collector Agent for gathering complete user information through HITL interactions.
    
    Manages the conversation flow to collect all necessary data for dashboard generation
    including products, channels, goals, time periods, and other requirements.
    """
    
    def __init__(self, llm):
        """
        Initialize the Data Collector Agent.
        
        Args:
            llm: Language model instance
        """
        self.llm = llm
        self.agent_name = "data_collector"
        
        # Define data collection categories and their requirements
        self.collection_categories = {
            "products": {
                "required": True,
                "description": "Specific products, services, or brand names to monitor",
                "question_template": "What specific products or brand names would you like to monitor?",
                "examples": ["Samsung Galaxy S25", "iPhone", "Tesla Model 3"]
            },
            "channels": {
                "required": True,
                "description": "Social media platforms and channels",
                "question_template": "Which channels would you like to monitor?",
                "examples": ["Twitter", "Facebook", "Instagram", "LinkedIn", "News", "Blogs"]
            },
            "goals": {
                "required": True,
                "description": "What the user wants to achieve",
                "question_template": "What is your goal with this monitoring?",
                "examples": ["Brand Awareness", "Customer Satisfaction", "Competitive Analysis"]
            },
            "time_period": {
                "required": True,
                "description": "Time range for data analysis",
                "question_template": "What time period are you interested in?",
                "examples": ["Last 30 days", "Last 6 months", "Since product launch"]
            },
            "location": {
                "required": False,
                "description": "Geographic focus",
                "question_template": "Are you focusing on a specific geographic region?",
                "examples": ["Global", "United States", "India", "Europe"]
            },
            "additional_notes": {
                "required": False,
                "description": "Additional requirements or focus areas",
                "question_template": "Any additional requirements or specific areas you'd like to focus on?",
                "examples": ["Customer feedback", "Sentiment analysis", "Influencer mentions"]
            }
        }
    
    def collect_missing_data(self, refined_query_data: Dict[str, Any], 
                           current_user_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Identify missing data and generate appropriate question.
        
        Args:
            refined_query_data: Data from query refiner
            current_user_data: Currently collected user data
            
        Returns:
            Tuple of (question, data_category)
        """
        try:
            # Identify what's missing
            missing_categories = self._identify_missing_data(current_user_data)
            
            if missing_categories:
                # Get the next question to ask
                next_category = missing_categories[0]
                question = self._generate_question(next_category, refined_query_data)
                return question, next_category
            else:
                # All data collected, ask for confirmation
                confirmation = self._generate_confirmation(current_user_data)
                return confirmation, "confirmation"
                
        except Exception as e:
            logger.error(f"Error in data collection: {e}")
            return "Could you please provide more details about what you'd like to monitor?", "general"
    
    def process_user_response(self, user_response: str, expected_category: str, 
                            current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user response and update data collection.
        
        Args:
            user_response: User's response
            expected_category: What category of data we were expecting
            current_data: Current collected data
            
        Returns:
            Updated data dictionary
        """
        try:
            if expected_category == "confirmation":
                return self._handle_confirmation_response(user_response, current_data)
            else:
                return self._extract_and_update_data(user_response, expected_category, current_data)
                
        except Exception as e:
            logger.error(f"Error processing user response: {e}")
            return current_data
    
    def _identify_missing_data(self, current_data: Dict[str, Any]) -> List[str]:
        """Identify which data categories are missing."""
        missing = []
        
        for category, config in self.collection_categories.items():
            if config["required"]:
                value = current_data.get(category)
                if not value or (isinstance(value, list) and len(value) == 0):
                    missing.append(category)
        
        # Add optional categories if we have required ones
        if not missing:
            for category, config in self.collection_categories.items():
                if not config["required"]:
                    value = current_data.get(category)
                    if not value:
                        missing.append(category)
        
        return missing
    
    def _generate_question(self, category: str, context: Dict[str, Any]) -> str:
        """Generate appropriate question for a data category."""
        config = self.collection_categories.get(category, {})
        base_question = config.get("question_template", f"Could you provide information about {category}?")
        examples = config.get("examples", [])
        
        question = base_question
        if examples:
            question += f" For example: {', '.join(examples[:3])}"
        
        # Add context-specific guidance
        if category == "products" and context.get("refined_query"):
            question += f"\n\nBased on your query about '{context['refined_query']}', please specify the exact products or brand names."
        
        return question
    
    def _generate_confirmation(self, user_data: Dict[str, Any]) -> str:
        """Generate confirmation message with collected data."""
        confirmation = "Please confirm the following information:\n\n"
        
        for category, value in user_data.items():
            if value and category in self.collection_categories:
                category_name = category.replace("_", " ").title()
                if isinstance(value, list):
                    confirmation += f"• {category_name}: {', '.join(value)}\n"
                else:
                    confirmation += f"• {category_name}: {value}\n"
        
        confirmation += "\nIs this information correct? Type 'yes' to proceed or specify what you'd like to change."
        return confirmation
    
    def _extract_and_update_data(self, response: str, category: str, 
                                current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from user response and update current data."""
        try:
            # Use LLM to extract structured data
            extraction_prompt = self._build_extraction_prompt(response, category)
            llm_response = self.llm.invoke(extraction_prompt)
            
            # Handle both string and message object responses
            if hasattr(llm_response, 'content'):
                response_content = llm_response.content
            else:
                response_content = str(llm_response)
            
            # Parse the extracted data
            extracted_data = self._parse_extraction_response(response_content, category)
            
            # Update current data
            updated_data = current_data.copy()
            updated_data[category] = extracted_data
            
            return updated_data
            
        except Exception as e:
            logger.error(f"Error extracting data for {category}: {e}")
            # Fallback: simple text processing
            return self._simple_extraction(response, category, current_data)
    
    def _build_extraction_prompt(self, response: str, category: str) -> str:
        """Build prompt for data extraction."""
        config = self.collection_categories.get(category, {})
        examples = config.get("examples", [])
        
        prompt = f"""
Extract {category} information from the user's response.

Category: {category}
Description: {config.get('description', '')}
Expected format: {"List of items" if category in ['products', 'channels', 'goals'] else "Single value"}
Examples: {examples}

User Response: "{response}"

Extract the relevant information and return it in a clean, structured format.
If it's a list category, return items separated by commas.
If it's a single value, return just the value.
"""
        return prompt
    
    def _parse_extraction_response(self, response: str, category: str) -> Any:
        """Parse LLM extraction response."""
        response = response.strip()
        
        # Categories that should be lists
        list_categories = ['products', 'channels', 'goals']
        
        if category in list_categories:
            # Split by common separators
            items = [item.strip() for item in response.replace(',', '\n').replace(';', '\n').split('\n')]
            items = [item for item in items if item and not item.startswith('•')]
            return items[:10]  # Limit to 10 items
        else:
            return response
    
    def _simple_extraction(self, response: str, category: str, 
                          current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simple fallback extraction."""
        updated_data = current_data.copy()
        
        list_categories = ['products', 'channels', 'goals']
        
        if category in list_categories:
            # Simple comma-separated extraction
            items = [item.strip() for item in response.split(',')]
            updated_data[category] = items[:5]  # Limit to 5 items
        else:
            updated_data[category] = response.strip()
        
        return updated_data
    
    def _handle_confirmation_response(self, response: str, 
                                    current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle confirmation response from user."""
        response_lower = response.lower().strip()
        
        # Check for affirmative responses
        affirmative_responses = ['yes', 'y', 'correct', 'confirm', 'proceed', 'good', 'ok', 'okay']
        
        if any(word in response_lower for word in affirmative_responses):
            # Mark as confirmed
            updated_data = current_data.copy()
            updated_data['confirmed'] = True
            return updated_data
        else:
            # User wants to modify something
            updated_data = current_data.copy()
            updated_data['modification_request'] = response
            return updated_data
    
    def is_data_complete(self, user_data: Dict[str, Any]) -> bool:
        """Check if all required data has been collected."""
        for category, config in self.collection_categories.items():
            if config["required"]:
                value = user_data.get(category)
                if not value or (isinstance(value, list) and len(value) == 0):
                    return False
        return True
    
    def get_next_required_field(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Get the next required field that needs to be collected."""
        missing = self._identify_missing_data(user_data)
        return missing[0] if missing else None

    async def process_state(self, state) -> Any:
        """
        Process the dashboard state for data collection.
        
        This method analyzes the current state and determines what additional
        information needs to be collected from the user.
        """
        try:
            logger.info("Processing state for data collection")
            
            # Get current user data from state
            current_data = {}
            if hasattr(state, 'user_data') and state.user_data:
                current_data = state.user_data.to_dict()
            elif hasattr(state, 'user_collected_data') and state.user_collected_data:
                current_data = state.user_collected_data.to_dict()
            
            # Get refined query data if available
            refined_query_data = {}
            if hasattr(state, 'query_refinement_data') and state.query_refinement_data:
                refined_query_data = {
                    "refined_query": state.query_refinement_data.refined_query,
                    "suggested_filters": state.query_refinement_data.suggested_filters,
                    "missing_information": state.query_refinement_data.missing_information
                }
            elif hasattr(state, 'query_refinement') and state.query_refinement:
                refined_query_data = {
                    "refined_query": state.query_refinement.refined_query,
                    "suggested_filters": state.query_refinement.suggested_filters,
                    "missing_information": state.query_refinement.missing_information
                }
            
            # Identify missing data and generate questions
            if not self.is_data_complete(current_data):
                question, category = self.collect_missing_data(refined_query_data, current_data)
                
                # Add the question to pending questions
                if hasattr(state, 'add_pending_question'):
                    state.add_pending_question(question)
                elif hasattr(state, 'pending_questions'):
                    state.pending_questions.append(question)
                
                # Update workflow status
                if hasattr(state, 'workflow_status'):
                    state.workflow_status = "awaiting_user_input"
                if hasattr(state, 'current_stage'):
                    state.current_stage = "collecting"
            else:
                # Data collection is complete
                if hasattr(state, 'workflow_status'):
                    state.workflow_status = "data_collection_complete"
                if hasattr(state, 'current_stage'):
                    state.current_stage = "collected"
            
            logger.info("Data collection processing completed")
            return state
            
        except Exception as e:
            logger.error(f"Error processing state: {str(e)}")
            # Add error to state if it has errors attribute
            if hasattr(state, 'errors'):
                state.errors.append(f"Data collection error: {str(e)}")
            if hasattr(state, 'workflow_status'):
                state.workflow_status = "data_collection_failed"
            return state
def create_data_collector_agent(llm) -> DataCollectorAgent:
    """
    Factory function to create a Data Collector Agent.
    
    Args:
        llm: Language model instance
        
    Returns:
        Configured DataCollectorAgent
    """
    return DataCollectorAgent(llm)