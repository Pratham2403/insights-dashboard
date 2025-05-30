from typing import List, Optional, Dict, Any
from server.agents.base.agent_base import Agent
from server.models.project_state import ProjectState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage # Import AIMessage
from langchain_openai import ChatOpenAI
import os
from server.config.settings import settings # Import settings
from pydantic import SecretStr

class HITLVerificationAgent(Agent):
    """
    Agent responsible for verifying collected user data,
    identifying missing information, and generating prompts for clarification.
    """

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.required_fields: List[str] = ["user_persona", "products", "channels", "goals", "time_period"]
        if llm:
            self.llm = llm
        else:
            # Pass API key directly if available in settings
            api_key_str = settings.OPENAI_API_KEY.get_secret_value() if isinstance(settings.OPENAI_API_KEY, SecretStr) else settings.OPENAI_API_KEY
            if not api_key_str:
                api_key_str = os.getenv("OPENAI_API_KEY")

            if api_key_str:
                self.llm = ChatOpenAI(temperature=0, model=settings.DEFAULT_LLM_MODEL, api_key=SecretStr(api_key_str))
            else:
                self.llm = ChatOpenAI(temperature=0, model=settings.DEFAULT_LLM_MODEL)
                print("WARNING: OPENAI_API_KEY not found for HITLVerificationAgent. LLM calls may fail if key is not in environment.")

    async def invoke(self, state: ProjectState) -> ProjectState:
        """
        Processes the current state to validate required fields and generate prompts if necessary.
        """
        state.current_stage = "validating"
        missing_fields = self._identify_missing_fields(state)
        state.missing_fields = missing_fields

        if not missing_fields:
            state.is_complete = True
            state.requires_human_input = False 
            last_message_is_ai_confirmation = False
            confirmation_message = "All required information has been collected. Ready to proceed."
            if state.messages and state.messages[-1]['role'] == 'ai' and state.messages[-1]['content'] == confirmation_message:
                last_message_is_ai_confirmation = True
            
            if not last_message_is_ai_confirmation:
                 state.messages.append({"role": "ai", "content": confirmation_message})
        else:
            state.is_complete = False
            state.requires_human_input = True
            prompt_for_user = await self._generate_clarification_prompt(state, missing_fields)
            last_message_is_same_question = False
            if state.messages and state.messages[-1]['role'] == 'ai' and state.messages[-1]['content'] == prompt_for_user:
                last_message_is_same_question = True
            
            if not last_message_is_same_question:
                state.messages.append({"role": "ai", "content": prompt_for_user})
        
        return state

    def _identify_missing_fields(self, state: ProjectState) -> List[str]:
        """Identifies which of the required fields are missing or empty in the current state."""
        missing = []
        for field in self.required_fields:
            value = getattr(state, field, None)
            if value is None or (isinstance(value, list) and not value):
                missing.append(field)
        return missing

    async def _generate_clarification_prompt(self, state: ProjectState, missing_fields: List[str]) -> str:
        """
        Generates a contextual prompt to ask the user for the missing information.
        """
        if not missing_fields:
            return "All necessary information seems to be collected. How should we proceed?"

        next_field_to_ask = missing_fields[0]

        prompts_map = {
            "user_persona": "To better tailor the insights, could you describe your role or who this dashboard is for? (e.g., Marketing Manager, Product Owner)",
            "products": "What specific products are you interested in analyzing? Please list them.",
            "channels": "Which channels do you want to analyze? (e.g., Twitter, Facebook, News articles, etc.)",
            "goals": "What are your primary goals for this analysis? (e.g., Brand Awareness, Customer Satisfaction, Competitor Tracking)",
            "time_period": "What time period should the analysis cover? (e.g., Last 3 months, Last year, specific date range)",
            "location": "Are you interested in insights from a specific location or region? If so, please specify.",
            "additional_notes": "Is there anything else specific you'd like to focus on or any additional notes for the analysis?"
        }
        
        question = prompts_map.get(next_field_to_ask, f"Could you please provide details for: {next_field_to_ask.replace('_', ' ')}?")
        
        # LLM-based prompt generation (optional enhancement)
        # if self.llm:
        #     prompt_template = ChatPromptTemplate.from_messages([
        #         ("system", "You are a helpful assistant gathering requirements for an insights dashboard. Ask a clear, concise question for the missing field."),
        #         ("human", "Current context: We have {current_data_summary}. We are missing {missing_field_description}. Please formulate a question for the user.")
        #     ])
        #     chain = prompt_template | self.llm
        #     try:
        #         response = await chain.ainvoke({
        #             "current_data_summary": self._summarize_current_data(state),
        #             "missing_field_description": next_field_to_ask.replace('_', ' ')
        #         })
        #         if isinstance(response, AIMessage) and response.content:
        #             return response.content.strip()
        #     except Exception as e:
        #         print(f"Error using LLM for prompt generation: {e}")
        #         # Fallback to default question if LLM fails
        return question

    def _summarize_current_data(self, state: ProjectState) -> str:
        """Helper to create a summary of collected data for LLM context."""
        summary_parts = []
        if state.user_persona: summary_parts.append(f"User Persona: {state.user_persona}")
        if state.products: summary_parts.append(f"Products: {', '.join(state.products)}")
        if state.location: summary_parts.append(f"Location: {state.location}")
        if state.channels: summary_parts.append(f"Channels: {', '.join(state.channels)}")
        if state.goals: summary_parts.append(f"Goals: {', '.join(state.goals)}")
        if state.time_period: summary_parts.append(f"Time Period: {state.time_period}")
        if state.additional_notes: summary_parts.append(f"Additional Notes: {state.additional_notes}")
        
        return "\n".join(summary_parts) if summary_parts else "No information collected yet."

async def _main_test_hitl():
    agent = HITLVerificationAgent() 
    
    initial_state = ProjectState(conversation_id="hitl-test-1")
    print("--- Test 1: Initial state ---")
    updated_state = await agent.invoke(initial_state)
    print(f"AI: {updated_state.messages[-1]['content']}")
    print(f"Missing: {updated_state.missing_fields}, Complete: {updated_state.is_complete}, Human Input: {updated_state.requires_human_input}\n")

    # Simulate user responding to the first question
    initial_state.messages.append({"role": "user", "content": "I am a CEO"}) # User provides persona
    initial_state.user_persona = "CEO"
    print("--- Test 1a: User responds with persona ---")
    updated_state_1a = await agent.invoke(initial_state)
    print(f"AI: {updated_state_1a.messages[-1]['content']}") # Should ask for products
    print(f"Missing: {updated_state_1a.missing_fields}\n")

    state_all_required = ProjectState(
        conversation_id="hitl-test-3",
        user_persona="CEO",
        products=["Product A", "Service B"],
        channels=["Online News", "Twitter"],
        goals=["Brand Reputation", "Market Trends"],
        time_period="Last 3 Months",
        messages=[{"role":"user", "content":"Here is all my info."}]
    )
    print("--- Test 3: All required fields provided ---")
    updated_state_3 = await agent.invoke(state_all_required)
    print(f"AI: {updated_state_3.messages[-1]['content']}")
    print(f"Missing: {updated_state_3.missing_fields}, Complete: {updated_state_3.is_complete}, Human Input: {updated_state_3.requires_human_input}\n")
    # Test idempotency: invoking again with complete state should not add duplicate confirmation
    updated_state_3_idem = await agent.invoke(updated_state_3)
    assert len(updated_state_3.messages) == len(updated_state_3_idem.messages), "Confirmation message duplicated"
    print("Idempotency test passed for confirmation.")

if __name__ == "__main__":
    import asyncio
    # from dotenv import load_dotenv
    # load_dotenv()
    # if not settings.OPENAI_API_KEY:
    #     print("OPENAI_API_KEY not set. LLM-dependent parts of the test might not work as expected.")
    asyncio.run(_main_test_hitl())
