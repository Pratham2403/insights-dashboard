from typing import List, Dict, Any, Optional
from server.agents.base.agent_base import Agent
from server.models.project_state import ProjectState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage # Import AIMessage
from langchain_openai import ChatOpenAI
import json
import os
from server.config.settings import settings
from pydantic import SecretStr

class QueryGenerationAgent(Agent):
    """
    Agent responsible for converting user requirements from the project state
    into optimized Elasticsearch queries.
    """

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        if llm:
            self.llm = llm
        else:
            api_key_str = settings.OPENAI_API_KEY.get_secret_value() if isinstance(settings.OPENAI_API_KEY, SecretStr) else settings.OPENAI_API_KEY
            if not api_key_str:
                api_key_str = os.getenv("OPENAI_API_KEY")

            if api_key_str:
                self.llm = ChatOpenAI(temperature=0, model=settings.QUERY_GENERATION_LLM_MODEL, api_key=SecretStr(api_key_str))
            else:
                self.llm = ChatOpenAI(temperature=0, model=settings.QUERY_GENERATION_LLM_MODEL)
                print("WARNING: OPENAI_API_KEY not found for QueryGenerationAgent. LLM calls may fail.")

        self.query_template = ChatPromptTemplate.from_messages([
            ("system", 
             "You are an expert Elasticsearch query generator. Convert user requirements into optimized Elasticsearch queries. "
             "Generate multiple targeted queries if necessary. "
             "Format: {\"page\": 0, \"size\": 100, \"keywords\": [...], \"filters\": {\"field_name\": \"value\"}}. " # Clarified filter structure
             "Keywords: list of strings. Filters: dictionary. "
             "Create specific queries for product-channel-goal combinations. "
             "Convert time period to Elasticsearch range query for a 'timestamp' field (e.g., {\"range\": {\"timestamp\": {\"gte\": \"now-6M/M\", \"lte\": \"now/M\"}}} for 'last 6 months'). "
             "Use location as a keyword or a filter if a specific field like 'location_tag' exists. "
             "If vital info (products, channels, goals) is missing, create broader queries based on user_persona or additional_notes. "
             "Output ONLY a valid JSON list of query objects. Each object in the list is one Elasticsearch query. Do not add any explanatory text before or after the JSON list."
            ),
            ("human", 
             "User Requirements:\n"
             "User Persona: {user_persona}\n"
             "Products: {products}\n"
             "Location: {location}\n"
             "Channels: {channels}\n"
             "Goals: {goals}\n"
             "Time Period: {time_period}\n"
             "Additional Notes: {additional_notes}\n\n"
             "Generate Elasticsearch queries based on these requirements."
            )
        ])

    async def invoke(self, state: ProjectState) -> ProjectState:
        """
        Generates Elasticsearch queries based on the current project state.
        """
        if not state.is_complete:
            # This check should ideally be handled by the workflow logic before calling this agent.
            state.messages.append({"role": "system", "content": "Query generation skipped: requirements collection not complete."})
            return state

        state.current_stage = "querying"
        chain = self.query_template | self.llm
        
        llm_response_content = ""
        try:
            response = await chain.ainvoke({
                "user_persona": str(state.user_persona) if state.user_persona else "Not specified",
                "products": ", ".join(state.products) if state.products else "Not specified",
                "location": str(state.location) if state.location else "Not specified",
                "channels": ", ".join(state.channels) if state.channels else "Not specified",
                "goals": ", ".join(state.goals) if state.goals else "Not specified",
                "time_period": str(state.time_period) if state.time_period else "Not specified",
                "additional_notes": str(state.additional_notes) if state.additional_notes else "Not specified"
            })
            
            if isinstance(response, AIMessage):
                # Ensure content is treated as a string. If it's a list, take the first text part.
                if isinstance(response.content, str):
                    llm_response_content = response.content.strip()
                elif isinstance(response.content, list) and response.content:
                    # Assuming the first part is the relevant text, or join them if appropriate
                    # For this agent, a single string JSON output is expected.
                    first_content_part = response.content[0]
                    if isinstance(first_content_part, str):
                        llm_response_content = first_content_part.strip()
                    elif isinstance(first_content_part, dict) and 'text' in first_content_part: # Handle content blocks
                        llm_response_content = first_content_part['text'].strip()
                    else:
                        llm_response_content = str(response.content).strip() # Fallback
                else:
                    llm_response_content = "" # Or handle as an error
            else:
                # Fallback if the response is not an AIMessage (e.g. a raw string from a simpler LLM call)
                llm_response_content = str(response).strip()

            # Clean potential markdown fences
            if llm_response_content.startswith("```json"):
                llm_response_content = llm_response_content[7:]
            if llm_response_content.endswith("```"):
                llm_response_content = llm_response_content[:-3]
            
            parsed_queries = json.loads(llm_response_content)
            
            if isinstance(parsed_queries, dict): 
                state.elasticsearch_queries = [parsed_queries]
            elif isinstance(parsed_queries, list):
                # Ensure all items in the list are dictionaries (queries)
                if all(isinstance(q, dict) for q in parsed_queries):
                    state.elasticsearch_queries = parsed_queries
                else:
                    raise ValueError("LLM returned a list, but not all items are valid query dictionaries.")
            else:
                raise ValueError(f"LLM returned an unexpected format for queries: {type(parsed_queries)}")

            state.messages.append({"role": "ai", "content": f"Generated {len(state.elasticsearch_queries)} Elasticsearch queries."})

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse LLM response for queries: {e}. Response was: '{llm_response_content}'"
            state.messages.append({"role": "system", "content": error_msg})
            state.elasticsearch_queries = []
        except ValueError as e: # Catch specific value errors from our validation
            error_msg = f"Error processing LLM query response: {e}. Response was: '{llm_response_content}'"
            state.messages.append({"role": "system", "content": error_msg})
            state.elasticsearch_queries = []
        except Exception as e:
            error_msg = f"An unexpected error occurred during query generation: {e}. Response was: '{llm_response_content}'"
            state.messages.append({"role": "system", "content": error_msg})
            state.elasticsearch_queries = []
            
        return state

async def _main_test_query_gen():
    agent = QueryGenerationAgent()
    test_state = ProjectState(
        user_persona="Tech Reviewer",
        products=["Smartphone X", "Laptop Y"],
        channels=["YouTube", "Tech Blogs"],
        goals=["Performance Benchmarks", "User Sentiment"],
        time_period="Last 3 months",
        additional_notes="Focus on battery life and camera quality for Smartphone X.",
        is_complete=True, 
        current_stage="validating"
    )
    print("--- Test Query Generation ---")
    updated_state = await agent.invoke(test_state)
    print(f"AI Message: {updated_state.messages[-1]['content'] if updated_state.messages else 'No message'}")
    print("Generated Queries:")
    if updated_state.elasticsearch_queries:
        for q_idx, q_val in enumerate(updated_state.elasticsearch_queries):
            print(f"  Query {q_idx+1}: {json.dumps(q_val, indent=2)}")
    else:
        print("  No queries generated or an error occurred.")

if __name__ == "__main__":
    import asyncio
    # from dotenv import load_dotenv
    # load_dotenv()
    # if not settings.OPENAI_API_KEY:
    #     print("OPENAI_API_KEY not set for query gen test.")
    # else:
    #     asyncio.run(_main_test_query_gen())
    asyncio.run(_main_test_query_gen())
