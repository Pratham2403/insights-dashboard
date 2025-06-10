# filepath: /Users/pratham.aggarwal/Documents/insights-dashboard/server/src/agents/data_analyzer_agent2.py
"""
Hybrid Data Analyzer Agent combining BERTopic with LLM-enhanced theme refinement

Key features:
- Uses LangGraph state context (refined_query, query list, keywords) to guide clustering
- Implements label-guided clustering to uncover sub-themes within document collections
- Performs cluster-assisted labeling to improve theme naming and descriptions
- Uses iterative approach to feed new clusters back into the model for reduced noise
- Generates optimized boolean queries for each of the top 5-10 identified themes
- Calculates confidence scores to validate theme relevance against original clusters
- Leverages LLM capabilities for natural language theme names and descriptions
- Combines unsupervised clustering with supervised refinement for higher accuracy
"""

import logging
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_core.messages import SystemMessage, HumanMessage

from src.setup.llm_setup import LLMSetup
from src.agents.query_generator_agent import QueryGeneratorAgent
from src.rag.filters_rag import get_filters_rag

logger = logging.getLogger(__name__)


class DataAnalyzerAgent:
    """
    Hybrid Data Analyzer combining BERTopic clustering with LLM-enhanced theme refinement.
    
    This agent implements a sophisticated two-stage approach:
    1. Initial BERTopic clustering for document organization
    2. LLM-guided theme generation and refinement with confidence scoring
    """
    
    def __init__(self, llm=None):
        """
        Initialize hybrid components for BERTopic clustering and LLM theme refinement.
        
        Args:
            llm: Optional LLM instance. If None, will use LLMSetup for agent-specific LLM.
        """
        try:
            # Initialize BERTopic components
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.topic_model = BERTopic(
                embedding_model=self.embedding_model, 
                nr_topics="auto",  # Let BERTopic determine optimal number
                min_topic_size=3   # Minimum documents per topic
            )
            
            # Initialize LLM for theme generation and refinement
            if llm is None:
                llm_setup = LLMSetup()
                self.llm = llm_setup.get_agent_llm("data_analyzer")
            else:
                self.llm = llm
                
            # Initialize QueryGeneratorAgent for boolean query generation
            self.query_generator = QueryGeneratorAgent(llm=self.llm)
            
            # Initialize RAG system for theme context retrieval
            self.rag_system = get_filters_rag()
            
            # Scoring parameters for theme evaluation (very lenient)
            self.min_confidence_score = 0.3  # Extremely low threshold for maximum theme discovery
            self.max_themes_output = 10
            self.min_themes_output = 5
            
            logger.info("DataAnalyzerAgent initialized successfully with hybrid capabilities")
            
        except Exception as e:
            error_msg = f"Failed to initialize DataAnalyzerAgent: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def _generate_potential_themes_with_llm(self, state: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate potential themes using LLM based on LangGraph state context and RAG-retrieved theme context.
        
        Args:
            state: LangGraph state containing refined_query, keywords, filters
            
        Returns:
            List of potential themes with names and descriptions
            
        Raises:
            RuntimeError: If RAG context retrieval fails or LLM response is invalid
        """
        try:
            refined_query = state.get("refined_query", "")
            keywords = state.get("keywords", [])
            filters = state.get("filters", {})
            
            if not refined_query:
                raise ValueError("Refined query is required for theme generation")
            
            # Get RAG context for relevant existing themes from themes.json
            try:
                search_query = f"{refined_query} {' '.join(keywords)}"
                relevant_themes = self.rag_system.search_themes(search_query, n_results=10)
            except Exception as e:
                error_msg = f"Failed to retrieve RAG context for themes: {e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
            
            if not relevant_themes:
                raise RuntimeError("No relevant themes found in RAG context - themes.json may be empty or inaccessible")
            
            # Format RAG themes for LLM context
            rag_themes_context = []
            for theme in relevant_themes:
                theme_info = f"Theme: {theme.get('name', 'Unknown')}\n"
                theme_info += f"Description: {theme.get('description', 'No description')}\n"
                
                # Add keywords if available
                keywords_str = theme.get('keywords', '')
                if keywords_str:
                    theme_info += f"Keywords: {keywords_str}\n"
                
                # Add related topics/sub-themes if available
                related_topics = theme.get('related_topics', '[]')
                if related_topics and related_topics != '[]':
                    try:
                        topics_data = json.loads(related_topics) if isinstance(related_topics, str) else related_topics
                        if topics_data:
                            theme_info += f"Sub-themes: {', '.join([t.get('name', str(t)) for t in topics_data if isinstance(t, dict)])}\n"
                    except:
                        pass
                
                rag_themes_context.append(theme_info)
            
            system_prompt = """You are an expert data analyst specializing in theme identification for business intelligence.
            Your task is to generate 10-15 potential themes based on the user's query and context, leveraging the provided theme knowledge base.

            CONTEXT FROM THEMES KNOWLEDGE BASE:
            {rag_context}

            USER CONTEXT:
            - Refined Query: {refined_query}
            - Keywords: {keywords}
            - Applied Filters: {filters}

            INSTRUCTIONS:
            1. Use the knowledge base themes as inspiration and context.
            2. Generate themes that are relevant to the user's specific query.
            3. You can select existing themes, adapt them, or create new ones based on sub-themes.
            4. Focus on themes that would be discoverable in document clustering.
            5. Do NOT use any entity names (e.g., Apple, HDFC, SBI, etc.) or source names in theme names or descriptions.
            6. Each theme should have a **clear, descriptive name** (no brand names), and a **detailed description** explaining what textual patterns, topics, or issues it represents.
            7. Ensure themes are distinct and cover different facets of the user’s query context.
            8. Write descriptions such that a Boolean query can be crafted using it — with no dependency on specific entity filters.

            Return ONLY a JSON array with this exact structure:
            [
              {{"name": "Theme Name", "description": "Detailed description of what this theme covers"}},
              {{"name": "Another Theme", "description": "Another detailed description"}}
            ]

            Do not include any other text or explanations."""



            human_prompt = system_prompt.format(
                rag_context='\n\n'.join(rag_themes_context),
                refined_query=refined_query,
                keywords=', '.join(keywords) if keywords else 'None',
                filters=json.dumps(filters) if filters else 'None'
            )
            
            messages = [HumanMessage(content=human_prompt)]
            
            # Get LLM response
            response = await self._safe_llm_call(messages)
            if not response:
                raise RuntimeError("LLM failed to generate potential themes")
            
            # Parse JSON response with robust cleaning
            try:
                # Clean the response by removing markdown code blocks and extra whitespace
                cleaned_response = response.strip()
                
                # Handle various markdown code block formats
                if "```json" in cleaned_response:
                    # Extract content between ```json and ```
                    start_idx = cleaned_response.find("```json") + 7
                    end_idx = cleaned_response.find("```", start_idx)
                    if end_idx != -1:
                        cleaned_response = cleaned_response[start_idx:end_idx].strip()
                elif cleaned_response.startswith("```") and cleaned_response.endswith("```"):
                    # Generic code block removal
                    lines = cleaned_response.split("\n")
                    if len(lines) > 2:
                        cleaned_response = "\n".join(lines[1:-1]).strip()
                
                # Remove any remaining leading/trailing whitespace and newlines
                cleaned_response = cleaned_response.strip()
                
                # Attempt to find JSON array if it's embedded in text
                if not cleaned_response.startswith("["):
                    start_bracket = cleaned_response.find("[")
                    end_bracket = cleaned_response.rfind("]")
                    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
                        cleaned_response = cleaned_response[start_bracket:end_bracket + 1]
                
                # Parse the JSON
                potential_themes = json.loads(cleaned_response)
                if not isinstance(potential_themes, list):
                    raise ValueError("Response is not a list")
                
                logger.info(f"Successfully parsed {len(potential_themes)} potential themes from LLM")
                
                # Validate theme structure
                validated_themes = []
                for theme in potential_themes:
                    if isinstance(theme, dict) and "name" in theme and "description" in theme:
                        validated_themes.append({
                            "name": str(theme["name"]).strip(),
                            "description": str(theme["description"]).strip()
                        })
                
                if not validated_themes:
                    raise ValueError("No valid themes found in LLM response")
                
                logger.info(f"Generated {len(validated_themes)} potential themes using RAG context")
                return validated_themes
                
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse LLM response as JSON: {e}"
                logger.error(f"{error_msg}. Cleaned response was: {cleaned_response[:500]}...")
                logger.error(f"Original response was: {response[:300]}...")
                raise RuntimeError(error_msg) from e
                
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            error_msg = f"Error generating potential themes with LLM: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _extract_documents_from_hits(self, hits: List[Dict[str, Any]]) -> List[str]:
        """
        Enhanced text extraction from Sprinklr API hits with better content discovery.
        
        Args:
            hits: List of hits from Sprinklr API
            
        Returns:
            List of extracted document strings
        """
        documents = []
        
        for hit in hits:
            text_content = ""
            
            if isinstance(hit, dict):
                # Try direct text fields first
                for field in ['content', 'text', 'message', 'body', 'description', 'title']:
                    if field in hit and hit[field]:
                        text_content = str(hit[field]).strip()
                        break
                
                # If no direct text field, try nested 'source' object
                if not text_content and 'source' in hit:
                    source = hit['source']
                    if isinstance(source, dict):
                        for field in ['content', 'text', 'message', 'body', 'description', 'title']:
                            if field in source and source[field]:
                                text_content = str(source[field]).strip()
                                break
                
                # Try other common nested structures
                if not text_content:
                    for nested_key in ['data', 'payload', 'document', 'item']:
                        if nested_key in hit and isinstance(hit[nested_key], dict):
                            nested_obj = hit[nested_key]
                            for field in ['content', 'text', 'message', 'body', 'description', 'title']:
                                if field in nested_obj and nested_obj[field]:
                                    text_content = str(nested_obj[field]).strip()
                                    break
                            if text_content:
                                break
            
            # Add document if we found valid content
            if text_content and len(text_content) > 10:  # Minimum length check
                documents.append(text_content)
        
        if not documents:
            raise ValueError(f"No valid text content found in {len(hits)} hits")
        
        logger.info(f"Extracted {len(documents)} documents from {len(hits)} hits")
        return documents

    def _cluster_documents(self, docs: List[str]) -> Tuple[List[int], np.ndarray, BERTopic]:
        """
        Perform initial BERTopic clustering on documents.
        
        Args:
            docs: List of document strings
            
        Returns:
            Tuple of (topics, probabilities, topic_model)
        """
        try:
            logger.info(f"Performing initial clustering on {len(docs)} documents")
            
            # Fit the topic model to the data
            topics, probs = self.topic_model.fit_transform(docs)
            
            # Update topics with documents for better representation
            self.topic_model.update_topics(docs, topics)
            
            logger.info(f"Initial clustering complete: {len(set(topics))} topics found")
            return topics, probs, self.topic_model
            
        except Exception as e:
            logger.error(f"Error in initial clustering: {e}")
            raise RuntimeError(f"Clustering failed: {e}") from e

    async def _refine_clusters_with_labels(
        self, 
        docs: List[str], 
        potential_themes: List[Dict[str, str]], 
        initial_topics: List[int],
        initial_probs: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Refine clusters using LLM-generated theme labels with dynamic similarity thresholds.
        
        Args:
            docs: Original document list
            potential_themes: LLM-generated potential themes
            initial_topics: Initial topic assignments
            initial_probs: Initial topic probabilities
            
        Returns:
            List of refined themes with document associations
        """
        try:
            logger.info("Refining clusters with LLM-generated labels using dynamic thresholds")
            
            # Get document embeddings for semantic similarity
            doc_embeddings = self.embedding_model.encode(docs)
            
            # Create embeddings for theme descriptions
            theme_texts = [f"{theme['name']}: {theme['description']}" for theme in potential_themes]
            theme_embeddings = self.embedding_model.encode(theme_texts)
            
            # Calculate similarity between documents and themes
            similarity_matrix = cosine_similarity(doc_embeddings, theme_embeddings)
            
            # Track document assignments to avoid overlap
            assigned_docs = set()
            refined_themes = []
            
            # Sort themes by their maximum similarity to ensure high-quality themes get priority
            theme_max_sims = [(i, np.max(similarity_matrix[:, i])) for i in range(len(potential_themes))]
            theme_max_sims.sort(key=lambda x: x[1], reverse=True)
            
            for theme_idx, max_sim in theme_max_sims:
                theme = potential_themes[theme_idx]
                theme_similarities = similarity_matrix[:, theme_idx]
                
                # Dynamic threshold based on theme's similarity distribution
                # Very lenient threshold approach for maximum theme discovery
                # Use low percentile thresholds to capture more diverse document-theme associations
                percentile_75 = np.percentile(theme_similarities, 75)
                percentile_50 = np.percentile(theme_similarities, 50)  # Median
                percentile_25 = np.percentile(theme_similarities, 25)
                mean_sim = np.mean(theme_similarities)
                
                # Extremely lenient threshold - prioritize finding themes over quality
                base_threshold = max(0.2, min(percentile_25, mean_sim * 0.5))  # Very low minimum
                quality_threshold = min(0.6, max(base_threshold, percentile_50))  # Use median as cap
                
                logger.debug(f"Theme '{theme['name']}': mean_sim={mean_sim:.3f}, "
                           f"p25={percentile_25:.3f}, p50={percentile_50:.3f}, p75={percentile_75:.3f}, "
                           f"threshold={quality_threshold:.3f}")
                
                # Find unassigned documents above threshold
                candidate_docs = [
                    j for j, sim in enumerate(theme_similarities) 
                    if sim >= quality_threshold and j not in assigned_docs
                ]
                
                if candidate_docs:
                    # Sort by similarity and take the best matches
                    candidate_docs.sort(key=lambda x: theme_similarities[x], reverse=True)
                    
                    # Very permissive document count requirements
                    min_docs = 1  # Accept themes with even 1 document
                    max_docs = min(int(len(docs) * 0.8), 200)  # Allow up to 80% of documents or 200 docs
                    
                    # Take top documents for this theme
                    selected_docs = candidate_docs[:max_docs]
                    
                    if len(selected_docs) >= min_docs:  # Only include if we have enough documents
                        # Mark documents as assigned
                        assigned_docs.update(selected_docs)
                        
                        avg_similarity = np.mean([theme_similarities[j] for j in selected_docs])
                        
                        refined_themes.append({
                            "name": theme["name"],
                            "description": theme["description"],
                            "document_indices": selected_docs,
                            "document_count": len(selected_docs),
                            "avg_similarity": float(avg_similarity),
                            "representative_docs": [docs[j] for j in selected_docs[:3]],
                            "similarity_threshold": float(quality_threshold)
                        })
                        
                        logger.debug(f"Theme '{theme['name']}' assigned {len(selected_docs)} docs with avg similarity {avg_similarity:.3f}")
                    else:
                        logger.debug(f"Theme '{theme['name']}' had {len(candidate_docs)} candidates but needed min {min_docs} docs")
                else:
                    # Log why no candidates were found
                    above_threshold_count = sum(1 for sim in theme_similarities if sim >= quality_threshold)
                    already_assigned_count = sum(1 for j, sim in enumerate(theme_similarities) 
                                               if sim >= quality_threshold and j in assigned_docs)
                    logger.debug(f"Theme '{theme['name']}' had {above_threshold_count} docs above threshold "
                               f"({already_assigned_count} already assigned), available: {above_threshold_count - already_assigned_count}")
            
            logger.info(f"Refined clustering complete: {len(refined_themes)} themes with variable document counts")
            
            # Additional debugging if no themes were generated
            if not refined_themes:
                logger.warning("No themes were generated during refinement!")
                logger.info(f"Total potential themes checked: {len(potential_themes)}")
                logger.info(f"Total documents available: {len(docs)}")
                logger.info(f"Documents already assigned: {len(assigned_docs)}")
                
                # Log a sample of similarity scores for debugging
                if len(potential_themes) > 0:
                    sample_theme = potential_themes[0]
                    sample_sims = similarity_matrix[:, 0]
                    logger.info(f"Sample theme '{sample_theme['name']}' similarity stats: "
                               f"min={np.min(sample_sims):.3f}, max={np.max(sample_sims):.3f}, "
                               f"mean={np.mean(sample_sims):.3f}, median={np.median(sample_sims):.3f}")
            
            return refined_themes
            
        except Exception as e:
            logger.error(f"Error in cluster refinement: {e}")
            # Fallback to initial clustering
            return self._fallback_to_initial_clustering(docs, initial_topics, initial_probs, potential_themes)

    def _fallback_to_initial_clustering(
        self, 
        docs: List[str], 
        topics: List[int], 
        probs: np.ndarray, 
        potential_themes: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Fallback method using initial BERTopic clustering if refinement fails.
        
        Args:
            docs: Document list
            topics: Initial topic assignments
            probs: Initial probabilities
            potential_themes: Potential themes for naming
            
        Returns:
            List of themes based on initial clustering
        """
        try:
            refined_themes = []
            unique_topics = [t for t in set(topics) if t != -1]  # Exclude outliers
            
            for topic_id in unique_topics:
                # Find documents in this topic
                topic_docs_idx = [i for i, t in enumerate(topics) if t == topic_id]
                if not topic_docs_idx:
                    continue
                
                # Get topic info from BERTopic
                topic_info = self.topic_model.get_topic(topic_id)
                topic_words = [word for word, _ in topic_info[:5]] if topic_info else []
                
                # Try to match with potential themes or create generic name
                theme_name = f"Topic {topic_id}: {', '.join(topic_words[:3])}" if topic_words else f"Topic {topic_id}"
                theme_desc = f"Documents discussing {', '.join(topic_words)}" if topic_words else f"Clustered documents in topic {topic_id}"
                
                avg_prob = np.mean([probs[i] for i in topic_docs_idx])
                
                refined_themes.append({
                    "name": theme_name,
                    "description": theme_desc,
                    "document_indices": topic_docs_idx,
                    "document_count": len(topic_docs_idx),
                    "avg_similarity": float(avg_prob),
                    "representative_docs": [docs[i] for i in topic_docs_idx[:3]]
                })
            
            return refined_themes
            
        except Exception as e:
            logger.error(f"Fallback clustering failed: {e}")
            raise RuntimeError(f"Fallback clustering failed: {e}") from e

    def _score_and_select_themes(
        self, 
        themes: List[Dict[str, Any]], 
        docs: List[str], 
        state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Calculate confidence scores for themes and select top performers with improved scoring logic.
        
        Args:
            themes: List of refined themes
            docs: Original document list
            state: LangGraph state for context scoring
            
        Returns:
            List of top-scored themes (5-10 themes)
        """
        try:
            logger.info(f"Scoring and selecting from {len(themes)} themes")
            
            keywords = state.get("keywords", [])
            refined_query = state.get("refined_query", "")
            
            for theme in themes:
                # Calculate composite confidence score with improved logic
                confidence_components = []
                
                # 1. Semantic similarity score (most important factor - 50% weight)
                similarity_score = float(theme.get("avg_similarity", 0.0))
                confidence_components.append(similarity_score * 0.5)
                
                # 2. Document quality score (20% weight)
                # Balanced approach: not too few, not too many documents
                doc_count = theme["document_count"]
                total_docs = len(docs)
                
                # Optimal range: 5% to 25% of total documents
                optimal_min = max(3, int(total_docs * 0.05))
                optimal_max = int(total_docs * 0.25)
                
                if doc_count < optimal_min:
                    # Too few documents - lower confidence
                    quality_score = float(doc_count / optimal_min * 0.7)
                elif doc_count > optimal_max:
                    # Too many documents - might be too generic
                    excess_ratio = (doc_count - optimal_max) / total_docs
                    quality_score = float(max(0.3, 1.0 - excess_ratio * 2))
                else:
                    # In optimal range - high confidence
                    quality_score = 1.0
                
                confidence_components.append(float(quality_score * 0.2))
                
                # 3. Keyword alignment score (20% weight)
                keyword_score = 0.0
                if keywords:
                    theme_text = f"{theme['name']} {theme['description']}".lower()
                    # Enhanced keyword matching with partial matches
                    keyword_matches = 0
                    for keyword in keywords:
                        keyword_lower = keyword.lower()
                        if keyword_lower in theme_text:
                            keyword_matches += 1
                        elif any(word in theme_text for word in keyword_lower.split()):
                            keyword_matches += 0.5  # Partial match
                    
                    keyword_score = float(min(1.0, keyword_matches / len(keywords)))
                confidence_components.append(float(keyword_score * 0.2))
                
                # 4. Query relevance score (10% weight) 
                query_score = 0.0
                if refined_query:
                    query_words = [word.lower() for word in refined_query.split() if len(word) > 3]
                    theme_text = f"{theme['name']} {theme['description']}".lower()
                    
                    if query_words:
                        query_matches = sum(1 for word in query_words if word in theme_text)
                        query_score = float(query_matches / len(query_words))
                confidence_components.append(float(query_score * 0.1))
                
                # Calculate final confidence score
                base_confidence = sum(confidence_components)
                
                # Bonus for themes with similarity threshold data (indicates quality clustering)
                if "similarity_threshold" in theme and theme["similarity_threshold"] > 0.5:
                    base_confidence += 0.05  # Small bonus for high-threshold themes
                
                theme["confidence_score"] = float(min(1.0, base_confidence))  # Cap at 1.0 and ensure Python float
                
                logger.debug(f"Theme '{theme['name']}': similarity={similarity_score:.3f}, quality={quality_score:.3f}, "
                           f"keywords={keyword_score:.3f}, query={query_score:.3f}, final={theme['confidence_score']:.3f}")
            
            # Sort by confidence score and select top themes
            themes.sort(key=lambda x: x["confidence_score"], reverse=True)
            
            # Adjust minimum confidence threshold based on available themes
            if themes:
                max_confidence = float(themes[0]["confidence_score"])
                # Dynamic threshold: at least 60% of the best theme's confidence
                dynamic_threshold = float(max(0.4, max_confidence * 0.6))
                self.min_confidence_score = float(min(self.min_confidence_score, dynamic_threshold))
            
            # Filter by minimum confidence and select appropriate number
            high_confidence_themes = [t for t in themes if t["confidence_score"] >= self.min_confidence_score]
            
            if len(high_confidence_themes) >= self.min_themes_output:
                selected_themes = high_confidence_themes[:self.max_themes_output]
            else:
                # Very lenient fallback - accept any theme with minimal confidence
                min_acceptable_confidence = 0.2  # Extremely low absolute minimum
                acceptable_themes = [t for t in themes if t["confidence_score"] >= min_acceptable_confidence]
                selected_themes = acceptable_themes[:max(self.min_themes_output, len(acceptable_themes))]
                
                # If still no themes, take all available themes
                if not selected_themes and themes:
                    selected_themes = themes[:self.max_themes_output]
                    logger.warning(f"Using all {len(selected_themes)} themes due to very low confidence scores")
            
            if selected_themes:
                logger.info(f"Selected {len(selected_themes)} themes with confidence scores ranging from "
                          f"{selected_themes[-1]['confidence_score']:.3f} to {selected_themes[0]['confidence_score']:.3f}")
            else:
                logger.warning("No themes met minimum confidence requirements")
                
            return selected_themes
            
        except Exception as e:
            logger.error(f"Error in theme scoring: {e}")
            raise RuntimeError(f"Theme scoring failed: {e}") from e

    async def _generate_boolean_queries_for_themes(
        self, 
        themes: List[Dict[str, Any]], 
        state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate boolean queries for each selected theme using QueryGeneratorAgent.
        
        Args:
            themes: List of selected themes
            state: LangGraph state containing original context
            
        Returns:
            List of themes with boolean_query field added
        """
        try:
            logger.info(f"Generating boolean queries for {len(themes)} themes")
            
            enhanced_themes = []
            for theme in themes:
                try:
                    # Create a modified state for this specific theme
                    theme_state = state.copy()
                    theme_state["refined_query"] = f"{theme['description']} {theme['name']}"
                    
                    # Extract keywords from theme representative documents
                    theme_keywords = []
                    if "representative_docs" in theme:
                        # Simple keyword extraction from representative documents
                        for doc in theme["representative_docs"]:
                            words = doc.lower().split()
                            # Filter for meaningful words (basic approach)
                            meaningful_words = [w for w in words if len(w) > 3 and w.isalpha()]
                            theme_keywords.extend(meaningful_words[:3])  # Take first 3 from each doc
                    
                    # Combine with original keywords
                    combined_keywords = list(set(state.get("keywords", []) + theme_keywords[:5]))
                    theme_state["keywords"] = combined_keywords
                    
                    # Generate boolean query for this theme
                    boolean_query_result = await self.query_generator._generate_boolean_query(
                        refined_query=theme_state["refined_query"],
                        keywords=combined_keywords,
                        filters=[]
                    )
                    
                    # Add boolean query to theme
                    theme_copy = theme.copy()
                    theme_copy["boolean_query"] = boolean_query_result or f'"{theme["name"]}"'
                    enhanced_themes.append(theme_copy)
                    
                except Exception as e:
                    logger.error(f"Failed to generate boolean query for theme '{theme.get('name', 'Unknown')}': {e}")
                    raise RuntimeError(f"Boolean query generation failed for theme '{theme.get('name', 'Unknown')}': {e}")
            
            logger.info(f"Boolean query generation complete for {len(enhanced_themes)} themes")
            return enhanced_themes
            
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise  # Re-raise runtime errors
            error_msg = f"Error generating boolean queries: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def analyze_hits_and_state(self, hits: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main analysis method implementing the complete hybrid approach.
        
        Args:
            hits: List of hits from Sprinklr API (not stored in state)
            state: LangGraph state containing refined_query, keywords, filters
            
        Returns:
            Dictionary with enhanced themes containing boolean queries
        """
        if not hits:
            raise ValueError("No hits provided for analysis")
        
        try:
            logger.info(f"Starting hybrid analysis on {len(hits)} hits with state context")
            
            # Step 1: Extract documents from hits
            documents = self._extract_documents_from_hits(hits)
            
            if len(documents) < 2:
                raise ValueError("At least 2 documents required for clustering analysis")
            
            # Step 2: Generate potential themes from state using LLM with RAG context
            potential_themes = await self._generate_potential_themes_with_llm(state)
            
            # Step 3: Perform initial clustering
            initial_topics, initial_probs, topic_model = self._cluster_documents(documents)
            
            # Step 4: Refine clusters with label guidance
            refined_themes = await self._refine_clusters_with_labels(
                documents, potential_themes, initial_topics, initial_probs
            )
            
            if not refined_themes:
                logger.info("No themes could be clustered from the documents - this is a valid result")
                return {
                    "themes": [],
                    "analysis_summary": {
                        "total_documents": len(documents),
                        "initial_topics": len(set(initial_topics)),
                        "potential_themes_generated": len(potential_themes),
                        "final_themes_selected": 0,
                        "avg_confidence_score": 0.0,
                        "analysis_method": "hybrid_bertopic_llm_with_rag",
                        "no_themes_reason": "Documents did not cluster into meaningful themes"
                    }
                }
            
            # Step 5: Score and select top themes
            selected_themes = self._score_and_select_themes(refined_themes, documents, state)
            
            # Step 6: Generate boolean queries for each theme
            final_themes = await self._generate_boolean_queries_for_themes(selected_themes, state)
            
            # Ensure all themes are msgpack serializable
            serializable_themes = [self._ensure_serializable(theme) for theme in final_themes]
            
            # Prepare final output with summary statistics
            result = {
                "themes": serializable_themes,
                "analysis_summary": {
                    "total_documents": len(documents),
                    "initial_topics": len(set(initial_topics)),
                    "potential_themes_generated": len(potential_themes),
                    "final_themes_selected": len(serializable_themes),
                    "avg_confidence_score": float(np.mean([t["confidence_score"] for t in serializable_themes])) if serializable_themes else 0.0,
                    "analysis_method": "hybrid_bertopic_llm_with_rag"
                }
            }
            
            logger.info(f"Hybrid analysis complete: {len(serializable_themes)} themes generated with boolean queries")
            return result
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise  # Re-raise validation errors
            error_msg = f"Hybrid analysis failed: {e}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    async def _safe_llm_call(self, messages: List, **kwargs) -> Optional[str]:
        """
        Safe LLM call with error handling.
        
        Args:
            messages: List of messages for the LLM
            **kwargs: Additional arguments for LLM call
            
        Returns:
            LLM response string or None if call fails
        """
        try:
            response = await self.llm.ainvoke(messages, **kwargs)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def _ensure_serializable(self, theme: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all values in theme dictionary are msgpack serializable.
        
        Args:
            theme: Theme dictionary potentially containing numpy types
            
        Returns:
            Theme dictionary with all values converted to Python native types
        """
        serializable_theme = {}
        for key, value in theme.items():
            if isinstance(value, np.ndarray):
                serializable_theme[key] = value.tolist()
            elif isinstance(value, (np.integer, np.floating)):
                serializable_theme[key] = float(value)
            elif isinstance(value, np.bool_):
                serializable_theme[key] = bool(value)
            elif isinstance(value, list):
                # Ensure list items are also serializable
                serializable_theme[key] = [
                    float(item) if isinstance(item, (np.integer, np.floating)) else
                    bool(item) if isinstance(item, np.bool_) else
                    item.tolist() if isinstance(item, np.ndarray) else
                    item
                    for item in value
                ]
            else:
                serializable_theme[key] = value
        return serializable_theme

def create_data_analyzer2(llm=None):
    """
    Create DataAnalyzerAgent instance for LangGraph compatibility.
    
    Args:
        llm: Optional LLM instance
        
    Returns:
        DataAnalyzerAgent instance
    """
    return DataAnalyzerAgent(llm=llm)
