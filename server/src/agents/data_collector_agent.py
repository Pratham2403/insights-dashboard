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
from src.agents.base.agent_base import LLMAgent, create_agent_factory

logger = logging.getLogger(__name__)

class DataCollectorAgent(LLMAgent):
    """
    Data Collector Agent for gathering complete user information through HITL interactions.
    
    Manages the conversation flow to collect all necessary data for dashboard generation
    including products, channels, goals, time periods, and other requirements.
    """
    
    def __init__(self, llm=None):
        """
        Initialize the Data Collector Agent.
        
        Args:
            llm: Language model instance
        """
        super().__init__("data_collector", llm)
        
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
            # Use LLM to extract structured data if available
            if self.llm:
                extraction_prompt = self._build_extraction_prompt(response, category)
                llm_response = self.llm.invoke(extraction_prompt)
                
                # Handle both string and message object responses
                try:
                    response_content = getattr(llm_response, 'content', str(llm_response))
                except:
                    response_content = str(llm_response)
                
                # Parse the extracted data
                extracted_data = self._parse_extraction_response(response_content, category)
            else:
                # Fallback to simple extraction if no LLM
                return self._simple_extraction(response, category, current_data)
            
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

    async def invoke(self, state) -> Any:
        """
        Main entry point for the agent - delegates to process_state.
        
        Args:
            state: The dashboard state to process
            
        Returns:
            Updated state after data collection processing
        """
        return await self.process_state(state)

    async def process_state(self, state) -> Any:
        """
        Process the dashboard state for data collection with dynamic extraction.
        
        This method analyzes the refined query and extracts relevant data dynamically
        from the knowledge base, then determines what additional information is needed.
        """
        try:
            logger.info("Processing state for dynamic data collection")
            
            # Initialize or get existing user data
            if not hasattr(state, 'user_data') or not state.user_data:
                from src.helpers.states import UserCollectedData
                state.user_data = UserCollectedData()
            
            # Check if this is a user response to existing conversation
            current_user_input = getattr(state, 'current_user_input', '')
            is_user_response = bool(current_user_input)
            
            # Check if this looks like a confirmation response (don't extract data from it)
            is_confirmation = False
            if is_user_response:
                confirmation_keywords = [
                    'perfect', 'exactly', 'correct', 'yes', 'proceed', 'looks good',
                    'that looks perfect', 'captures exactly', 'right', 'accurate'
                ]
                is_confirmation = any(keyword in current_user_input.lower() for keyword in confirmation_keywords)
            
            # Get refined query information (original query, not user responses)
            refined_query = ""
            if hasattr(state, 'query_refinement_data') and state.query_refinement_data:
                if isinstance(state.query_refinement_data, dict):
                    refined_query = state.query_refinement_data.get('refined_query', '')
                else:
                    refined_query = getattr(state.query_refinement_data, 'refined_query', '')
            elif hasattr(state, 'user_query') and not is_user_response:
                refined_query = state.user_query
            
            # Handle confirmation responses - use refined query context, not the confirmation message
            if is_user_response and is_confirmation and refined_query:
                logger.info("User confirmed refined query - extracting data from refined query, not confirmation message")
                
                # Extract data from the REFINED QUERY, not the confirmation message
                if not state.user_data.extracted_data:
                    extracted_info = await self._extract_dynamic_data(refined_query, state)
                    state.user_data.extracted_data = extracted_info.get('extracted_data', {})
                    state.user_data.keywords = extracted_info.get('keywords', [])
                    state.user_data.applied_filters = extracted_info.get('applied_filters', {})
                    self._apply_default_values(state.user_data)
                
                # Mark as confirmed and ready
                state.user_data.user_satisfaction = True
                state.user_data.awaiting_user_confirmation = False
                state.user_data.user_final_approval = True
                state.workflow_status = "user_confirmed"
                state.current_stage = "data_collection_complete"
                
                logger.info("Data collection marked as complete after user confirmation")
                return state
            
            # Handle other user responses (additional info, modifications)
            elif is_user_response and current_user_input:
                response_handled = await self._handle_user_response(current_user_input, state)
                if response_handled:
                    return state
            
            # Dynamic data extraction from refined query and knowledge base (only for initial processing)
            if refined_query and not state.user_data.extracted_data and not is_user_response:
                extracted_info = await self._extract_dynamic_data(refined_query, state)
                state.user_data.extracted_data = extracted_info.get('extracted_data', {})
                state.user_data.keywords = extracted_info.get('keywords', [])
                state.user_data.applied_filters = extracted_info.get('applied_filters', {})
                
                # Set default values based on knowledge base
                self._apply_default_values(state.user_data)
            
            # Check if we need more information from user
            missing_info = self._identify_missing_critical_info(state.user_data, refined_query)
            
            if missing_info and not state.user_data.user_satisfaction:
                # Generate questions for missing information
                question = self._generate_clarification_question(missing_info, state.user_data)
                
                # Add the question to pending questions
                if hasattr(state, 'add_pending_question'):
                    state.add_pending_question(question)
                elif hasattr(state, 'pending_questions'):
                    state.pending_questions.append(question)
                
                # Update workflow status
                state.workflow_status = "awaiting_user_input"
                state.current_stage = "collecting"
                state.user_data.requires_clarification = True
            else:
                # Data collection is complete or user is satisfied
                state.workflow_status = "data_collection_ready"
                state.current_stage = "collected"
                state.user_data.requires_clarification = False
                
                # If user hasn't explicitly indicated satisfaction, ask for confirmation
                if state.user_data.user_satisfaction is None:
                    confirmation_msg = self._generate_final_confirmation_request(state.user_data)
                    if hasattr(state, 'add_pending_question'):
                        state.add_pending_question(confirmation_msg)
                    elif hasattr(state, 'pending_questions'):
                        state.pending_questions.append(confirmation_msg)
                    
                    state.workflow_status = "awaiting_final_confirmation"
            
            logger.info(f"Data collection processing completed - status: {state.workflow_status}")
            return state
            
        except Exception as e:
            logger.error(f"Error processing state: {str(e)}")
            if hasattr(state, 'errors'):
                state.errors.append(f"Data collection error: {str(e)}")
            if hasattr(state, 'workflow_status'):
                state.workflow_status = "data_collection_failed"
            return state

    async def _extract_dynamic_data(self, refined_query: str, state) -> Dict[str, Any]:
        """
        Extract data dynamically from refined query using knowledge base context.
        
        Args:
            refined_query: The refined user query
            state: Current dashboard state
            
        Returns:
            Dictionary containing extracted data, keywords, and filters
        """
        try:
            # Load available filters from knowledge base
            available_filters = self._load_available_filters()
            
            # Use LLM to extract structured information
            if self.llm:
                extraction_prompt = f"""
                You are extracting data from a refined user query for social media monitoring dashboard creation.
                
                REFINED USER QUERY: "{refined_query}"
                
                AVAILABLE FILTERS FROM SYSTEM: {available_filters}
                
                EXTRACTION TASK:
                Extract all relevant monitoring information from this refined query. This query has already been processed by the Query Refiner Agent and contains enhanced business context.
                
                Extract the following categories dynamically:
                1. **Products/Brands**: Any product names, brand names, company names mentioned
                2. **Channels**: Social media platforms, news sources (Twitter, Instagram, Facebook, etc.)
                3. **Goals**: Analysis objectives (sentiment analysis, brand health, competitive analysis, etc.)
                4. **Timeline**: Time periods, date ranges mentioned
                5. **Location**: Geographic regions, countries, cities mentioned
                6. **Sentiment Targets**: Specific sentiment analysis requirements
                7. **Topics**: Key themes, issues, subjects to monitor
                8. **Competitors**: Competing brands or products mentioned
                
                KEYWORD GENERATION:
                Create a comprehensive list of search keywords from all extracted entities that would be used for boolean query generation.
                
                FILTER MAPPING:
                Map extracted information to the available system filters wherever possible.
                
                DEFAULT ASSUMPTIONS (apply only if not explicitly mentioned):
                - Time period: "last 30 days"
                - Channels: ["Twitter", "Instagram"]
                - Language: ["English"]
                - Geographic scope: "global"
                
                Return ONLY valid JSON in this exact format:
                {{
                    "extracted_data": {{
                        "products": ["list of products/brands found"],
                        "brands": ["list of brand names found"],
                        "channels": ["list of social media channels found"],
                        "goals": ["list of monitoring objectives found"],
                        "timeline": "time period found or default",
                        "location": ["geographic locations found or default"],
                        "sentiment_targets": ["specific sentiment requirements"],
                        "topics": ["key themes and topics"],
                        "competitors": ["competing entities mentioned"]
                    }},
                    "keywords": ["comprehensive list of search keywords from all extracted data"],
                    "applied_filters": {{
                        "source": ["mapped to available source filters"],
                        "country": ["mapped to available country filters"],
                        "language": ["mapped to available language filters"]
                    }}
                }}
                """
                
                try:
                    response = await self.safe_llm_invoke([{"role": "user", "content": extraction_prompt}])
                    if response:
                        # Try to parse JSON response
                        import json
                        import re
                        
                        # Clean up response if it contains markdown
                        clean_response = re.sub(r'```json\n(.*?)\n```', r'\1', response, flags=re.DOTALL)
                        clean_response = re.sub(r'```\n(.*?)\n```', r'\1', clean_response, flags=re.DOTALL)
                        
                        try:
                            extracted = json.loads(clean_response)
                            return extracted
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse LLM JSON response, using fallback extraction")
                
                except Exception as e:
                    logger.error(f"Error with LLM extraction: {e}")
            
            # Fallback extraction method
            return self._fallback_extraction(refined_query, available_filters)
            
        except Exception as e:
            logger.error(f"Error in dynamic data extraction: {e}")
            return {
                "extracted_data": {},
                "keywords": [],
                "applied_filters": {}
            }
    
    def _load_available_filters(self) -> Dict[str, Any]:
        """Load available filters from knowledge base."""
        try:
            import json
            import os
            
            # Path to filters knowledge base
            kb_path = os.path.join(os.path.dirname(__file__), '..', 'knowledge_base', 'filers.json')
            
            if os.path.exists(kb_path):
                with open(kb_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning("Filters knowledge base not found, using defaults")
                return {
                    "filters": {
                        "source": ["Twitter", "Instagram", "Facebook", "LinkedIn", "YouTube"],
                        "language": ["English"],
                        "country": ["India", "USA", "UK"],
                        "gender": ["Male", "Female"]
                    }
                }
        except Exception as e:
            logger.error(f"Error loading filters: {e}")
            return {"filters": {}}
    
    def _fallback_extraction(self, query: str, available_filters: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback extraction method using simple text analysis."""
        query_lower = query.lower()
        
        # Extract basic information
        extracted_data = {
            "time_period": "30 days",  # Default
            "channels": ["Twitter", "Instagram"],  # Default channels
            "sentiment": "overall"
        }
        
        # Simple keyword extraction
        keywords = []
        
        # Look for brand/product mentions
        brand_indicators = ["samsung", "google", "apple", "microsoft", "amazon", "facebook", "tesla"]
        for brand in brand_indicators:
            if brand in query_lower:
                keywords.append(brand)
                if "products" not in extracted_data:
                    extracted_data["products"] = []
                extracted_data["products"].append(brand)
        
        # Look for monitoring goals
        if "brand health" in query_lower or "monitoring" in query_lower:
            extracted_data["goal"] = "brand health monitoring"
            keywords.extend(["brand", "health", "monitoring"])
        
        # Apply default filters
        filters = available_filters.get("filters", {})
        applied_filters = {
            "source": ["Twitter", "Instagram"],
            "language": ["English"]
        }
        
        return {
            "extracted_data": extracted_data,
            "keywords": keywords,
            "applied_filters": applied_filters
        }
    
    def _apply_default_values(self, user_data):
        """Apply default values based on complete use cases."""
        # Set defaults if not already present
        if not user_data.extracted_data.get("time_period"):
            user_data.extracted_data["time_period"] = "30 days"
        
        if not user_data.extracted_data.get("channels"):
            user_data.extracted_data["channels"] = ["Twitter", "Instagram"]
        
        if not user_data.applied_filters.get("source"):
            user_data.applied_filters["source"] = ["Twitter", "Instagram"]
        
        if not user_data.applied_filters.get("language"):
            user_data.applied_filters["language"] = ["English"]
    
    def _identify_missing_critical_info(self, user_data, refined_query: str) -> List[str]:
        """Identify critical missing information that needs user input."""
        missing = []
        
        # Check if we have any meaningful keywords or products
        has_products = bool(user_data.extracted_data.get("products") or user_data.keywords)
        has_clear_goal = bool(user_data.extracted_data.get("goal"))
        
        if not has_products:
            missing.append("specific products or brands to monitor")
        
        if not has_clear_goal and "monitoring" not in refined_query.lower():
            missing.append("monitoring objective or goal")
        
        # Only ask for non-critical missing info if we have the essentials
        if not missing:
            if not user_data.extracted_data.get("location"):
                missing.append("target location or market (optional)")
        
        return missing
    
    def _generate_clarification_question(self, missing_info: List[str], user_data) -> str:
        """Generate clarification question for missing information."""
        if not missing_info:
            return ""
        
        if len(missing_info) == 1:
            item = missing_info[0]
            if "products" in item:
                return "Could you please specify which products or brands you'd like to monitor? For example: 'Samsung Galaxy S25', 'iPhone', etc."
            elif "goal" in item:
                return "What is your main objective for this monitoring? For example: 'Brand awareness', 'Customer sentiment analysis', 'Competitive analysis', etc."
            elif "location" in item:
                return "Would you like to focus on any specific geographic region or market? (You can skip this if you want global monitoring)"
        
        # Multiple missing items
        questions = []
        for item in missing_info[:2]:  # Limit to 2 questions at a time
            if "products" in item:
                questions.append("- Which specific products or brands should I monitor?")
            elif "goal" in item:
                questions.append("- What is your main monitoring objective?")
        
        return f"I need a bit more information:\n\n{chr(10).join(questions)}"
    
    def _generate_final_confirmation_request(self, user_data) -> str:
        """Generate final confirmation request with collected data summary."""
        summary_parts = []
        
        if user_data.extracted_data:
            if user_data.extracted_data.get("products"):
                summary_parts.append(f"**Products/Brands:** {', '.join(user_data.extracted_data['products'])}")
            if user_data.extracted_data.get("channels"):
                summary_parts.append(f"**Channels:** {', '.join(user_data.extracted_data['channels'])}")
            if user_data.extracted_data.get("time_period"):
                summary_parts.append(f"**Time Period:** {user_data.extracted_data['time_period']}")
            if user_data.extracted_data.get("goal"):
                summary_parts.append(f"**Goal:** {user_data.extracted_data['goal']}")
        
        if user_data.keywords:
            summary_parts.append(f"**Keywords:** {', '.join(user_data.keywords)}")
        
        summary = "\n".join(summary_parts) if summary_parts else "Basic monitoring setup"
        
        return f"""
## Data Collection Summary

{summary}

**Are you satisfied with this information and ready to proceed with data generation?**

Please respond with:
- 'Yes, proceed' to continue
- 'No, let me refine' to make changes
        """.strip()

    async def _handle_user_response(self, user_input: str, state) -> bool:
        """
        Handle user response - either confirmation or additional information.
        
        Args:
            user_input: User's response/input
            state: Current dashboard state
            
        Returns:
            True if response was handled, False otherwise
        """
        try:
            user_input_lower = user_input.lower().strip()
            
            # Check for confirmation responses
            confirmation_keywords = [
                'yes', 'y', 'correct', 'confirm', 'proceed', 'good', 'ok', 'okay', 
                'perfect', 'looks good', 'that looks perfect', 'exactly', 'right',
                'accurate', 'go ahead', 'continue', 'approved'
            ]
            
            # Check for rejection/modification responses
            rejection_keywords = [
                'no', 'n', 'incorrect', 'wrong', 'change', 'modify', 'different',
                'not correct', 'not right', 'fix', 'update'
            ]
            
            if any(keyword in user_input_lower for keyword in confirmation_keywords):
                # User confirmed - mark as satisfied and ready for next stage
                state.user_data.user_satisfaction = True
                state.user_data.awaiting_user_confirmation = False
                state.user_data.user_final_approval = True
                state.workflow_status = "user_confirmed"
                state.current_stage = "confirmed"
                
                logger.info("User confirmed data collection - ready for query generation")
                return True
                
            elif any(keyword in user_input_lower for keyword in rejection_keywords):
                # User wants modifications - need to collect more info
                state.user_data.user_satisfaction = False
                state.user_data.modification_request = user_input
                state.workflow_status = "needs_modification"
                
                # Generate follow-up questions based on the rejection
                question = f"I understand you'd like to make changes. Could you please specify what you'd like to modify about the monitoring setup? Current setup: {self._summarize_current_data(state.user_data)}"
                
                if hasattr(state, 'add_pending_question'):
                    state.add_pending_question(question)
                elif hasattr(state, 'pending_questions'):
                    state.pending_questions.append(question)
                
                logger.info("User requested modifications to data collection")
                return True
                
            else:
                # User provided additional information - try to extract and incorporate it
                extracted_additional = await self._extract_additional_info(user_input, state)
                
                if extracted_additional:
                    # Update user data with additional information
                    self._merge_additional_data(extracted_additional, state.user_data)
                    
                    # Check if we still need more information
                    missing_info = self._identify_missing_critical_info(state.user_data, "")
                    
                    if missing_info:
                        # Still need more info
                        question = self._generate_clarification_question(missing_info, state.user_data)
                        if hasattr(state, 'add_pending_question'):
                            state.add_pending_question(question)
                        elif hasattr(state, 'pending_questions'):
                            state.pending_questions.append(question)
                        
                        state.workflow_status = "awaiting_user_input"
                    else:
                        # All info collected, ask for final confirmation
                        confirmation_msg = self._generate_final_confirmation_request(state.user_data)
                        if hasattr(state, 'add_pending_question'):
                            state.add_pending_question(confirmation_msg)
                        elif hasattr(state, 'pending_questions'):
                            state.pending_questions.append(confirmation_msg)
                        
                        state.workflow_status = "awaiting_final_confirmation"
                    
                    logger.info("Incorporated additional user information")
                    return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error handling user response: {e}")
            return False
    
    def _summarize_current_data(self, user_data) -> str:
        """Create a summary of currently collected data."""
        summary_parts = []
        
        if user_data.extracted_data.get('products'):
            summary_parts.append(f"Products: {', '.join(user_data.extracted_data['products'])}")
        
        if user_data.extracted_data.get('channels'):
            summary_parts.append(f"Channels: {', '.join(user_data.extracted_data['channels'])}")
        
        if user_data.extracted_data.get('time_period'):
            summary_parts.append(f"Timeline: {user_data.extracted_data['time_period']}")
        
        if user_data.extracted_data.get('goal'):
            summary_parts.append(f"Goal: {user_data.extracted_data['goal']}")
        
        return "; ".join(summary_parts) if summary_parts else "No data collected yet"
    
    async def _extract_additional_info(self, user_input: str, state) -> Dict[str, Any]:
        """Extract additional information from user input."""
        try:
            if self.llm:
                prompt = f"""
                The user provided additional information: "{user_input}"
                
                Extract any relevant monitoring information from this response.
                Look for:
                - Products or brand names
                - Social media channels
                - Time periods
                - Goals or objectives
                - Geographic regions
                - Any other monitoring parameters
                
                Return in JSON format:
                {{
                    "products": ["any products mentioned"],
                    "channels": ["any channels mentioned"],
                    "time_period": "any time period mentioned",
                    "goals": ["any goals mentioned"],
                    "location": ["any locations mentioned"]
                }}
                
                Only include fields with actual information found.
                """
                
                response = await self.safe_llm_invoke([{"role": "user", "content": prompt}])
                if response:
                    import json
                    import re
                    
                    # Clean up response
                    clean_response = re.sub(r'```json\n(.*?)\n```', r'\1', response, flags=re.DOTALL)
                    clean_response = re.sub(r'```\n(.*?)\n```', r'\1', clean_response, flags=re.DOTALL)
                    
                    try:
                        return json.loads(clean_response)
                    except json.JSONDecodeError:
                        pass
            
            # Fallback: simple keyword extraction
            return self._simple_info_extraction(user_input)
            
        except Exception as e:
            logger.error(f"Error extracting additional info: {e}")
            return {}
    
    def _simple_info_extraction(self, text: str) -> Dict[str, Any]:
        """Simple fallback extraction from text."""
        text_lower = text.lower()
        extracted = {}
        
        # Look for channel mentions
        channels = ['twitter', 'facebook', 'instagram', 'linkedin', 'youtube', 'tiktok']
        found_channels = [ch.title() for ch in channels if ch in text_lower]
        if found_channels:
            extracted['channels'] = found_channels
        
        # Look for time periods
        if 'days' in text_lower or 'weeks' in text_lower or 'months' in text_lower:
            words = text.split()
            for i, word in enumerate(words):
                if word.lower() in ['days', 'weeks', 'months'] and i > 0:
                    try:
                        num = int(words[i-1])
                        extracted['time_period'] = f"{num} {word.lower()}"
                        break
                    except ValueError:
                        pass
        
        return extracted
    
    def _merge_additional_data(self, additional_data: Dict[str, Any], user_data):
        """Merge additional data into existing user data."""
        for key, value in additional_data.items():
            if key in user_data.extracted_data:
                if isinstance(value, list) and isinstance(user_data.extracted_data[key], list):
                    # Merge lists, avoiding duplicates
                    user_data.extracted_data[key].extend([v for v in value if v not in user_data.extracted_data[key]])
                else:
                    # Replace with new value
                    user_data.extracted_data[key] = value
            else:
                user_data.extracted_data[key] = value

# Create factory function using base class helper
create_data_collector_agent = create_agent_factory(DataCollectorAgent, "data_collector")