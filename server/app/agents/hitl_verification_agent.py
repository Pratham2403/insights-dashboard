"""
Human-in-the-Loop (HITL) verification agent for the Sprinklr Insights Dashboard.
"""
from typing import Dict, List, Any, TypedDict, Optional, Tuple
import logging
import json
import re
from datetime import datetime
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config.settings import settings
from app.models.state import UserRequirements

logger = logging.getLogger(__name__)


# Define system prompt for the HITL verification agent
HITL_SYSTEM_PROMPT = """You are an AI assistant helping to collect requirements for generating a Sprinklr Insights Dashboard.
Your goal is to gather all necessary information from the user to create the dashboard.

Required information includes:
1. Products - Specific product names or models (e.g., Samsung S25 Ultra, iPhone 15 Pro)
2. Channels - Social media platforms or sources to analyze (e.g., Twitter, Facebook, News)
3. Goals - User's objectives (e.g., Brand Awareness, Customer Satisfaction)
4. Time Period - Timeframe for analysis (e.g., Last 6 months, Last year)

Optional information includes:
1. Focus Areas - Specific aspects to analyze (e.g., Customer Feedback, Sentiment Analysis)
2. Additional Notes - Any other relevant information
3. User Persona - Role of the user (e.g., Sales Manager, Marketing Director)
4. Location - Geographic areas of interest

IMPORTANT: Always maintain context of previously collected information. When the user provides new information, 
combine it with what was already collected. Do not lose track of previous requirements.

When the user provides information, extract and categorize it properly.
If any required information is missing, ask follow-up questions to collect it.
Be conversational but focused on collecting the required information.
Only ask one question at a time.

At any point, if the user wants to know what information has been collected so far, summarize the requirements collected.
"""


# Define the chat template for the HITL verification agent
HITL_CHAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", HITL_SYSTEM_PROMPT),
    ("human", "{input}"),
    ("ai", "{agent_scratchpad}")
])


class HITLVerificationAgent:
    """
    Agent responsible for verifying user requirements and collecting missing information.
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the HITL verification agent.

        Args:
            model_name: The name of the language model to use.
        """
        self.model_name = model_name or settings.DEFAULT_MODEL_NAME
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0.2,
            max_tokens=1000,
            google_api_key=settings.GEMINI_API_KEY
        )

    async def process_input(self, state: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """
        Process user input and update the state.

        Args:
            state: The current state of the conversation.
            user_input: The user's input.

        Returns:
            Updated state.
        """
        # Initialize messages if not present or not in the correct format
        if "messages" not in state or not isinstance(state["messages"], list):
            state["messages"] = []
        else:
            # Ensure all messages are BaseMessage instances
            state["messages"] = [
                msg if isinstance(msg, BaseMessage) else (
                    HumanMessage(content=msg["content"]) if msg.get("role") == "user" 
                    else AIMessage(content=msg["content"]) if msg.get("role") == "assistant" 
                    else SystemMessage(content=msg["content"]) if msg.get("role") == "system" 
                    else HumanMessage(content=str(msg)) # Fallback for unknown structure
                )
                for msg in state["messages"]
            ]

        # Add user input to messages
        user_message = HumanMessage(content=user_input)
        # Use add_messages logic if available, otherwise append
        if hasattr(state["messages"], 'append'): # Check if it's a list
             state["messages"].append(user_message)
        # If state["messages"] is managed by add_messages, it will handle it.

        # Extract user requirements
        if "user_requirements" not in state or not isinstance(state["user_requirements"], dict):
            state["user_requirements"] = UserRequirements().dict()

        current_requirements_dict = state["user_requirements"]

        # Update user requirements based on input
        updated_requirements_dict, missing_fields = await self._extract_requirements(
            state["messages"], # Pass the list of BaseMessage objects
            current_requirements_dict
        )

        # Update state with new requirements
        state["user_requirements"] = updated_requirements_dict

        # Generate response based on missing fields and current requirements
        ai_response_content = await self._generate_response(state["messages"], missing_fields, updated_requirements_dict)

        # Add AI response to messages
        ai_message = AIMessage(content=ai_response_content)
        if hasattr(state["messages"], 'append'): # Check if it's a list
            state["messages"].append(ai_message)

        # Update current step
        state["current_step"] = "HITL_VERIFICATION"

        # Check if all required fields are filled
        user_req_model = UserRequirements(**state["user_requirements"])
        state["all_requirements_collected"] = user_req_model.is_complete()
        state["last_updated"] = datetime.now().isoformat()

        return state

    async def _extract_requirements(
        self, 
        messages: List[BaseMessage],  # Expect a list of BaseMessage objects
        current_requirements: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Extract requirements from the conversation history.

        Args:
            messages: The conversation history (list of BaseMessage objects).
            current_requirements: The current user requirements as a dictionary.

        Returns:
            Tuple of updated requirements dictionary and list of missing fields.
        """
        conversation_history_for_prompt = []
        for msg in messages:
            role = "unknown"
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            conversation_history_for_prompt.append({"role": role, "content": msg.content})

        extraction_prompt = f"""
        You are updating user requirements for a Sprinklr Insights Dashboard. 
        
        CRITICAL: YOU MUST PRESERVE ALL EXISTING INFORMATION AND ONLY ADD NEW INFORMATION.

        EXISTING REQUIREMENTS (DO NOT LOSE ANY OF THIS):
        {json.dumps(current_requirements, indent=2)}

        CONVERSATION TO ANALYZE FOR NEW INFORMATION:
        {json.dumps(conversation_history_for_prompt[-2:] if len(conversation_history_for_prompt) > 2 else conversation_history_for_prompt)}

        INSTRUCTIONS:
        1. Start with the EXISTING REQUIREMENTS above
        2. Only add new information from the latest conversation messages
        3. For lists (products, channels, goals, focus_areas, location): ADD to existing items, never replace
        4. For strings (time_period, additional_notes, user_persona): UPDATE only if new info provided
        5. Return ALL fields with existing data preserved + any new data added

        Example: If existing products=["Samsung"] and user mentions "S25 Ultra", result should be ["Samsung", "S25 Ultra"]

        Return this exact JSON structure with ALL existing data preserved:
        {{
            "products": {current_requirements.get("products", [])},
            "channels": {current_requirements.get("channels", [])},
            "goals": {current_requirements.get("goals", [])},
            "time_period": {json.dumps(current_requirements.get("time_period"))},
            "focus_areas": {current_requirements.get("focus_areas", [])},
            "additional_notes": {json.dumps(current_requirements.get("additional_notes"))},
            "user_persona": {json.dumps(current_requirements.get("user_persona"))},
            "location": {current_requirements.get("location", [])}
        }}

        Only modify the above JSON if you find NEW information in the conversation to ADD.
        """

        lc_messages_for_extraction = [HumanMessage(content=extraction_prompt)]

        response = await self.llm.ainvoke(lc_messages_for_extraction)

        try:
            content = response.content
            content_to_parse = ""

            json_match_block = re.search(r'```json\n(.*?)\n```', content, re.DOTALL | re.IGNORECASE)
            if json_match_block:
                content_to_parse = json_match_block.group(1)
            else:
                json_match_object = re.search(r'({.*?})', content, re.DOTALL)
                if json_match_object:
                    content_to_parse = json_match_object.group(1)
                else:
                    logger.warning(f"Could not find a clear JSON block or object in LLM response for extraction. Raw content: {content}")
                    content_to_parse = content

            if not isinstance(content_to_parse, str):
                logger.error(f"content_to_parse is not a string: {type(content_to_parse)}. LLM response content: {content}")
                content_to_parse = str(content_to_parse)

            extracted_data_dict = json.loads(content_to_parse)
            
            # Create a UserRequirements instance from current_requirements for easier manipulation
            updated_req_model = UserRequirements(**current_requirements)

            # Ensure extracted_data_dict has all fields
            list_fields = ["products", "channels", "goals", "focus_areas", "location"]
            string_fields = ["time_period", "additional_notes", "user_persona"]

            # Handle list fields - ALWAYS preserve existing and add new
            for field in list_fields:
                current_field_values = getattr(updated_req_model, field) or []
                
                if field in extracted_data_dict and extracted_data_dict[field] is not None:
                    new_values = extracted_data_dict[field]
                    if not isinstance(new_values, list):
                        new_values = [new_values] if new_values else []
                    
                    # Add new values to existing ones, avoiding duplicates
                    for item in new_values:
                        if item and str(item).strip():
                            item_str = str(item).strip()
                            # Check for duplicates case-insensitively
                            if not any(item_str.lower() == existing.lower() for existing in current_field_values):
                                current_field_values.append(item_str)
                
                setattr(updated_req_model, field, current_field_values)

            # Handle string fields - update only if new value provided
            for field in string_fields:
                if field in extracted_data_dict and extracted_data_dict[field] is not None:
                    new_value = str(extracted_data_dict[field]).strip()
                    if new_value:  # Only update if not empty
                        setattr(updated_req_model, field, new_value)
            
            updated_requirements_dict = updated_req_model.dict()
            missing_fields = updated_req_model.get_missing_fields()
            
            logger.info(f"Updated requirements: {updated_requirements_dict}")
            logger.info(f"Missing fields: {missing_fields}")
            
            return updated_requirements_dict, missing_fields
            
        except Exception as e:
            logger.error(f"Error extracting requirements: {e}. Raw LLM response: {response.content}")
            # Fallback: return current requirements and try to determine missing fields from them.
            # This prevents losing all progress if extraction fails.
            # Ensure current_requirements is a valid dict for UserRequirements model
            if not isinstance(current_requirements, dict):
                 current_requirements = UserRequirements().dict() # Default to empty if invalid
            return current_requirements, UserRequirements(**current_requirements).get_missing_fields()

    async def _generate_response(
        self,
        messages: List[BaseMessage], # Expect a list of BaseMessage objects
        missing_fields: List[str],
        current_requirements: Dict[str, Any]
    ) -> str:
        """
        Generate a response based on missing fields and current requirements.

        Args:
            messages: The conversation history (list of BaseMessage objects).
            missing_fields: List of missing required fields.
            current_requirements: The current state of collected user requirements as a dictionary.

        Returns:
            AI response text.
        """
        lc_conversation_history = []
        for msg in messages:
            # Ensure we are passing BaseMessage instances or compatible dicts
            if isinstance(msg, HumanMessage):
                lc_conversation_history.append(HumanMessage(content=msg.content))
            elif isinstance(msg, AIMessage):
                lc_conversation_history.append(AIMessage(content=msg.content))
            elif isinstance(msg, SystemMessage):
                 # System messages might not be directly part of history for some models
                 # but can be prepended to the prompt if needed.
                 pass # Or handle as per LLM expectation
            elif isinstance(msg, dict) and "content" in msg: # Handle dict messages if any slip through
                if msg.get("role") == "user":
                    lc_conversation_history.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    lc_conversation_history.append(AIMessage(content=msg["content"]))

        # Create context-aware system prompt with current requirements
        system_message_content = f"""You are an AI assistant helping to collect requirements for generating a Sprinklr Insights Dashboard.
Your goal is to gather all necessary information from the user to create the dashboard.

CURRENT COLLECTED REQUIREMENTS:
{json.dumps(current_requirements, indent=2)}

Required information includes:
1. Products - Specific product names or models (e.g., Samsung S25 Ultra, iPhone 15 Pro)
2. Channels - Social media platforms or sources to analyze (e.g., Twitter, Facebook, News)
3. Goals - User's objectives (e.g., Brand Awareness, Customer Satisfaction)
4. Time Period - Timeframe for analysis (e.g., Last 6 months, Last year)

Optional information includes:
1. Focus Areas - Specific aspects to analyze (e.g., Customer Feedback, Sentiment Analysis)
2. Additional Notes - Any other relevant information
3. User Persona - Role of the user (e.g., Sales Manager, Marketing Director)
4. Location - Geographic areas of interest

IMPORTANT RULES:
- Always maintain context of previously collected information shown above
- When the user provides new information, combine it with what was already collected
- Do not lose track of previous requirements
- ALWAYS acknowledge what has been collected so far when asking for new information
- Only ask for ONE missing field at a time
- Be conversational but focused on collecting the required information"""

        if missing_fields:
            # Prioritize asking for the first missing field.
            next_field_to_ask = missing_fields[0]
            system_message_content += f"""

Missing fields that still need to be collected: {missing_fields}

Please ask a clear and concise question to collect information for '{next_field_to_ask}'. 
Only ask about this one field. If the user has provided information that seems to fulfill other missing fields, 
acknowledge it briefly before asking for the next specific missing piece.
REMEMBER: Always mention what you've already collected before asking for the next piece of information."""
        else:
            system_message_content += """

All required information has been collected. 
Summarize the collected information for the user and ask if they want to provide any additional optional information 
(Focus Areas, Additional Notes, User Persona, Location) or if they are ready to proceed with generating the dashboard. 
If they have already provided some optional information, acknowledge that as well."""
        
        # Create system message and combine with conversation history
        system_message = SystemMessage(content=system_message_content)
        final_prompt_messages = [system_message] + lc_conversation_history

        try:
            # Generate response
            response = await self.llm.ainvoke(final_prompt_messages)
            return response.content
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            if missing_fields:
                return f"Could you please provide information about: {missing_fields[0]}?"
            else:
                return "Thank you for providing all the information. Shall we proceed with generating the dashboard?"
