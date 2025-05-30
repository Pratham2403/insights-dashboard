from typing import List, Dict, Any, Optional
# Ensure sklearn is installed or handle optional import
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    # from sklearn.cluster import KMeans # Optional, if using TF-IDF + Kmeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    TfidfVectorizer = None # type: ignore
    # KMeans = None

import numpy as np
import os
import json

from server.agents.base.agent_base import Agent
from server.models.project_state import ProjectState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage # Import AIMessage
from langchain_openai import ChatOpenAI
from server.config.settings import settings
from pydantic import SecretStr

class ThemeScoringAlgorithm:
    def __init__(self, top_n: int = 7):
        self.top_n = top_n

    def score_and_select(self, themes_with_docs_content: Dict[str, List[str]], original_docs_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        scored_themes = []
        for theme_label, docs_texts in themes_with_docs_content.items():
            num_docs = len(docs_texts)
            avg_doc_length = np.mean([len(text) for text in docs_texts]) if docs_texts else 0
            score = (num_docs * 0.8) + (avg_doc_length * 0.002) 
            
            scored_themes.append({
                "theme_label": theme_label,
                "score": round(score, 4),
                "document_count": num_docs,
            })
        
        top_themes = sorted(scored_themes, key=lambda x: x["score"], reverse=True)[:self.top_n]
        return top_themes

class DataProcessingAgent(Agent):
    """
    Agent for processing retrieved Elasticsearch data, extracting themes, and scoring them.
    """
    def __init__(self, llm: Optional[ChatOpenAI] = None, top_n_themes: int = 7):
        if llm:
            self.llm = llm
        else:
            api_key_str = settings.OPENAI_API_KEY.get_secret_value() if isinstance(settings.OPENAI_API_KEY, SecretStr) else settings.OPENAI_API_KEY
            if not api_key_str:
                api_key_str = os.getenv("OPENAI_API_KEY")

            if api_key_str:
                self.llm = ChatOpenAI(temperature=0.1, model=settings.DATA_PROCESSING_LLM_MODEL, api_key=SecretStr(api_key_str))
            else:
                self.llm = ChatOpenAI(temperature=0.1, model=settings.DATA_PROCESSING_LLM_MODEL)
                print("WARNING: OPENAI_API_KEY not found for DataProcessingAgent. LLM calls may fail.")
            
        self.theme_scorer = ThemeScoringAlgorithm(top_n=top_n_themes)
        self.theme_extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are an expert data analyst. Extract key themes from the provided text documents. "
             "Focus on topics relevant to the user's goals: {goals}, products: {products}, and persona: {user_persona}. "
             "Output ONLY a valid JSON object where keys are theme labels and values are lists of document indices (0-based) for that theme. "
             "Example: {\"Customer Support Issues\": [0, 5, 12], \"Feature Requests\": [1, 7]}. Do not add any text before or after the JSON object."
            ),
            ("human", 
             "User Goals: {goals}\nUser Products: {products}\nUser Persona: {user_persona}\n\n"
             "Documents (content only, separated by '---DOCUMENT_SEPARATOR---'):\n{document_texts}\n\n"
             "Extract themes and their corresponding document indices."
            )
        ])

    async def invoke(self, state: ProjectState) -> ProjectState:
        state.current_stage = "processing"

        if not state.retrieved_data:
            state.messages.append({"role": "system", "content": "No data retrieved. Skipping data processing."})
            state.processed_themes = []
            state.current_stage = "completed"
            return state

        document_texts = [doc.get("text", "") for doc in state.retrieved_data if doc.get("text")]
        if not document_texts:
            state.messages.append({"role": "system", "content": "No text content in retrieved data. Skipping theme extraction."})
            state.processed_themes = []
            state.current_stage = "completed"
            return state

        themes_with_indices = await self._extract_themes_llm(state, document_texts)

        themes_with_docs_content = {}
        for theme, indices in themes_with_indices.items():
            themes_with_docs_content[theme] = [document_texts[i] for i in indices if 0 <= i < len(document_texts)]

        ranked_themes = self.theme_scorer.score_and_select(themes_with_docs_content, state.retrieved_data)
        
        for theme_info in ranked_themes:
            theme_label = theme_info["theme_label"]
            if theme_label in themes_with_indices:
                doc_indices_for_theme = themes_with_indices[theme_label]
                theme_info["example_doc_ids"] = [
                    state.retrieved_data[i].get("id", f"index_{i}") 
                    for i in doc_indices_for_theme 
                    if 0 <= i < len(state.retrieved_data)
                ][:3] 

        state.processed_themes = ranked_themes
        state.messages.append({"role": "ai", "content": f"Processed data and extracted {len(ranked_themes)} top themes."})
        
        state.current_stage = "completed"
        state.is_complete = True 
        state.requires_human_input = False
        return state

    async def _extract_themes_llm(self, state: ProjectState, document_texts: List[str]) -> Dict[str, List[int]]:
        chain = self.theme_extraction_prompt | self.llm
        
        separator = "\n---DOCUMENT_SEPARATOR---\n"
        MAX_LLM_INPUT_CHARS = 15000 
        
        texts_for_llm = []
        current_char_count = 0
        docs_processed_indices_map = {} # Maps index in texts_for_llm to original index in document_texts

        for original_idx, text in enumerate(document_texts):
            if current_char_count + len(text) + len(separator) > MAX_LLM_INPUT_CHARS:
                # print(f"Warning: Truncating documents for LLM theme extraction due to size. Processed {len(texts_for_llm)} docs.")
                break
            texts_for_llm.append(text)
            docs_processed_indices_map[len(texts_for_llm) - 1] = original_idx
            current_char_count += len(text) + len(separator)

        if not texts_for_llm:
            return {}
            
        combined_texts_for_llm = separator.join(texts_for_llm)
        llm_response_content = ""

        try:
            response = await chain.ainvoke({
                "goals": ", ".join(state.goals) if state.goals else "General understanding",
                "products": ", ".join(state.products) if state.products else "Not specified",
                "user_persona": state.user_persona if state.user_persona else "Not specified",
                "document_texts": combined_texts_for_llm
            })

            if isinstance(response, AIMessage):
                # Ensure content is treated as a string. If it's a list, take the first text part.
                if isinstance(response.content, str):
                    llm_response_content = response.content.strip()
                elif isinstance(response.content, list) and response.content:
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
                llm_response_content = str(response).strip()

            if llm_response_content.startswith("```json"):
                llm_response_content = llm_response_content[7:]
            if llm_response_content.endswith("```"):
                llm_response_content = llm_response_content[:-3]
            
            themes_raw = json.loads(llm_response_content)
            valid_themes: Dict[str, List[int]] = {}

            if isinstance(themes_raw, dict):
                for theme_label, llm_indices in themes_raw.items():
                    if isinstance(theme_label, str) and isinstance(llm_indices, list):
                        original_doc_indices = []
                        for llm_idx in llm_indices:
                            if isinstance(llm_idx, int) and 0 <= llm_idx < len(texts_for_llm):
                                original_doc_indices.append(docs_processed_indices_map[llm_idx])
                        if original_doc_indices:
                             valid_themes[theme_label] = sorted(list(set(original_doc_indices))) # Ensure unique and sorted
            return valid_themes

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse LLM response for themes: {e}. Response: '{llm_response_content}'"
            state.messages.append({"role": "system", "content": error_msg})
            return {}
        except Exception as e:
            error_msg = f"Unexpected error in LLM theme extraction: {e}. Response: '{llm_response_content}'"
            state.messages.append({"role": "system", "content": error_msg})
            return {}

    # TF-IDF based theme extraction (alternative, requires sklearn)
    def _extract_themes_tfidf(self, document_texts: List[str], num_themes: int = 5) -> Dict[str, List[int]]:
        if not SKLEARN_AVAILABLE or not TfidfVectorizer:
            print("Skipping TF-IDF: scikit-learn not available.")
            return {}
        if not document_texts or len(document_texts) < num_themes:
            return {}
        try:
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000, min_df=2, ngram_range=(1,2))
            tfidf_matrix = vectorizer.fit_transform(document_texts)
            # This is a simplified approach: take top terms as themes (not clustering)
            # For a more robust approach, use KMeans or other clustering algorithms here.
            feature_names = np.array(vectorizer.get_feature_names_out())
            themes: Dict[str, List[int]] = {}
            # Example: Create themes from some top terms (very naive)
            # A proper implementation would involve clustering (e.g., KMeans) and then labeling clusters.
            # For now, this part is a placeholder for a more complex non-LLM theme extraction.
            print("TF-IDF theme extraction is a placeholder and needs a clustering step for meaningful themes.")
            # Example: find documents where top N terms appear
            # top_n_terms_indices = tfidf_matrix.sum(axis=0).argsort()[0, ::-1][0, :num_themes].A1
            # for i, term_idx in enumerate(top_n_terms_indices):
            #    theme_label = f"KeywordTheme: {feature_names[term_idx]}"
            #    # Find docs containing this term (simplified)
            #    doc_indices = [doc_idx for doc_idx, score in enumerate(tfidf_matrix[:, term_idx].toarray()) if score > 0.1]
            #    if doc_indices:
            #        themes[theme_label] = doc_indices
            return themes
        except Exception as e:
            print(f"Error in TF-IDF processing: {e}")
            return {}

async def _main_test_data_proc():
    agent = DataProcessingAgent(top_n_themes=3)
    sample_retrieved_data = [
        {"id": "doc_1", "text": "The new phone has amazing battery life and a great camera."},
        {"id": "doc_2", "text": "Customer support was slow to respond to my billing query."},
        {"id": "doc_3", "text": "I wish the laptop had more USB ports, but performance is good."},
        {"id": "doc_4", "text": "The camera quality on the phone is superb in low light."},
        {"id": "doc_5", "text": "Billing issues are frustrating, took three calls to resolve."},
        {"id": "doc_6", "text": "The phone's battery easily lasts two days with normal use."}
    ]
    test_state = ProjectState(
        retrieved_data=sample_retrieved_data,
        goals=["Identify product strengths", "Find customer pain points"],
        products=["New Phone", "Laptop Model Z"],
        user_persona="Product Manager",
        current_stage="querying"
    )
    print("--- Test Data Processing (LLM based) ---")
    updated_state = await agent.invoke(test_state)
    print(f"AI Message: {updated_state.messages[-1]['content'] if updated_state.messages else 'No message'}")
    print("Processed Themes:")
    if updated_state.processed_themes:
        for theme in updated_state.processed_themes:
            print(json.dumps(theme, indent=2))
    else:
        print("  No themes extracted or an error occurred.")
    
    # Test TF-IDF (if sklearn available)
    # if SKLEARN_AVAILABLE:
    #     print("\n--- Test Data Processing (TF-IDF placeholder) ---")
    #     themes_tfidf = agent._extract_themes_tfidf([d['text'] for d in sample_retrieved_data])
    #     print("TF-IDF Themes (placeholder output):")
    #     for label, docs in themes_tfidf.items():
    #         print(f"  {label}: {docs[:3]}...")

if __name__ == "__main__":
    import asyncio
    # from dotenv import load_dotenv
    # load_dotenv()
    # if not settings.OPENAI_API_KEY:
    #     print("OPENAI_API_KEY not set for data proc test.")
    # else:
    #     asyncio.run(_main_test_data_proc())
    asyncio.run(_main_test_data_proc())
