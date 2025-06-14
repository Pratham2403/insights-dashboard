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
- Combines unsupervised clustering with supervised refinement for higher accuracyClus
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
            
            # Enhanced scoring parameters for high-quality theme generation
            self.min_confidence_score = 0.65  # Higher threshold for quality themes
            self.max_themes_output = 10
            self.min_themes_output = 1  # Allow minimum 1 high-quality theme
            
            logger.info("DataAnalyzerAgent initialized successfully with hybrid capabilities")
            
        except Exception as e:
            error_msg = f"Failed to initialize DataAnalyzerAgent: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def _generate_potential_themes_with_llm(self, state: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Enhanced multi-shot theme generation using iterative LLM refinement.
        
        Args:
            state: LangGraph state containing refined_query, keywords, filters
            
        Returns:
            List of potential themes with names and descriptions
            
        Raises:
            RuntimeError: If LLM response is invalid
        """
        try:
            refined_query = state.get("refined_query", "")
            boolean_query = state.get("boolean_query", "")
            keywords = state.get("keywords", [])
            entities = state.get("entities", [])
            industry = state.get("industry", "")
            sub_vertical = state.get("sub_vertical", "")
            use_case = state.get("use_case", "")
            
            if not refined_query:
                raise ValueError("Refined query is required for theme generation")

            # Step 1: Initial theme brainstorming
            initial_themes = await self._generate_initial_themes(
                refined_query, keywords, entities, boolean_query, industry, sub_vertical, use_case
            )
            
            # Step 2: Theme quality enhancement and refinement
            refined_themes = await self._refine_theme_quality(initial_themes, state)
            
            return refined_themes
            
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            error_msg = f"Error generating potential themes with LLM: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def _generate_initial_themes(
        self, 
        refined_query: str,
        keywords: List[str],
        entities: List[str], 
        boolean_query: str,
        industry: str,
        sub_vertical: str,
        use_case: str
    ) -> List[Dict[str, str]]:
        """Generate initial set of themes using enhanced prompt engineering."""
        
        system_prompt = """
        You are an expert business intelligence analyst with deep expertise in thematic analysis for enterprise dashboards.

        Your task is to generate 15-20 DISTINCT analytical themes that will serve as lenses for exploring business data.
        
        CONTEXT ANALYSIS:
        - Refined Query: {refined_query}
        - Keywords: {keywords}
        - Entities: {entities}
        - Boolean Query: {boolean_query}
        - Industry: {industry}
        - Sub-Vertical: {sub_vertical}
        - Use Case: {use_case}

        THEME GENERATION REQUIREMENTS:
        1. Generate themes that are MUTUALLY EXCLUSIVE and COLLECTIVELY EXHAUSTIVE
        2. Focus on ACTIONABLE BUSINESS INSIGHTS rather than simple categorization
        3. Each theme should represent a unique analytical perspective on the data
        4. Themes must be industry-agnostic and entity-neutral (no brand names)
        5. Consider multiple dimensions: sentiment, risk, opportunity, operational, strategic
        6. Ensure themes can generate meaningful boolean queries for data filtering

        OUTPUT FORMAT:
        Return exactly a JSON array of objects with "name" and "description" fields.
        Each description should be 1-2 sentences explaining the analytical value.
        """

        human_prompt = system_prompt.format(
            refined_query=refined_query,
            keywords=', '.join(keywords) if keywords else 'None',
            entities=', '.join(entities) if entities else 'None',
            boolean_query=boolean_query,
            industry=industry,
            sub_vertical=sub_vertical,
            use_case=use_case
        )

        messages = [HumanMessage(content=human_prompt)]
        response = await self._safe_llm_call(messages)
        
        if not response:
            raise RuntimeError("LLM failed to generate initial themes")
        
        return self._parse_theme_response(response)

    async def _refine_theme_quality(
        self, 
        initial_themes: List[Dict[str, str]], 
        state: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Refine theme quality through iterative LLM enhancement."""
        
        refinement_prompt = f"""
        You are a quality control expert for business intelligence themes. 
        
        Review these {len(initial_themes)} themes and enhance them for maximum analytical value:

        ORIGINAL THEMES:
        {json.dumps(initial_themes, indent=2)}

        ENHANCEMENT CRITERIA:
        1. Eliminate redundant or overlapping themes
        2. Ensure each theme offers unique analytical insight
        3. Improve theme names for clarity and business relevance
        4. Enhance descriptions for better boolean query generation
        5. Prioritize themes with highest business impact potential
        6. Maintain 10-15 highest quality themes

        Return the ENHANCED themes as JSON array with same structure.
        Focus on QUALITY over quantity - select only the most valuable analytical lenses.
        """

        messages = [HumanMessage(content=refinement_prompt)]
        response = await self._safe_llm_call(messages)
        
        if not response:
            logger.warning("Theme refinement failed, using initial themes")
            return initial_themes
        
        try:
            refined_themes = self._parse_theme_response(response)
            logger.info(f"Enhanced Themes : {json.dumps(refined_themes, indent=2)}")
            return refined_themes
        except Exception as e:
            logger.warning(f"Theme refinement parsing failed: {e}, using initial themes")
            return initial_themes

    def _parse_theme_response(self, response: str) -> List[Dict[str, str]]:
        """Parse and validate LLM theme response."""
        try:
            # Clean the response by removing markdown code blocks and extra whitespace
            cleaned_response = response.strip()
            
            # Handle various markdown code block formats
            if "```json" in cleaned_response:
                start_idx = cleaned_response.find("```json") + 7
                end_idx = cleaned_response.find("```", start_idx)
                if end_idx != -1:
                    cleaned_response = cleaned_response[start_idx:end_idx].strip()
            elif cleaned_response.startswith("```") and cleaned_response.endswith("```"):
                lines = cleaned_response.split("\n")
                if len(lines) > 2:
                    cleaned_response = "\n".join(lines[1:-1]).strip()
            
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
            
            logger.info(f"Parsed {len(validated_themes)} valid themes from LLM response")
            return validated_themes
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse LLM response as JSON: {e}"
            logger.error(f"{error_msg}. Cleaned response was: {cleaned_response[:500]}...")
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
            
            if isinstance(hit, dict) and "text" in hit and hit["text"]:
                text_content = str(hit["text"]).strip()

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

        except IndexError as e:
            # Handle BERTopic clustering failure when no topics can be found
            logger.warning(f"BERTopic could not find meaningful topics in the documents: {e}")
            logger.info("Creating fallback clustering with single topic assignment")

            # Create fallback clustering where all documents belong to topic 0
            fallback_topics = [0] * len(docs)
            fallback_probs = np.ones((len(docs),)) * 0.5  # Moderate confidence

            # Create a new topic model instance for consistency
            fallback_model = BERTopic(
                embedding_model=self.embedding_model,
                nr_topics=1,  # Force single topic
                min_topic_size=1
            )

            return fallback_topics, fallback_probs, fallback_model

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
        Refine clusters using LLM-generated theme labels with enhanced quality thresholds.
        
        Args:
            docs: Original document list
            potential_themes: LLM-generated potential themes
            initial_topics: Initial topic assignments
            initial_probs: Initial topic probabilities
            
        Returns:
            List of refined themes with document associations
        """
        try:
            logger.info("Refining clusters with LLM-generated labels using enhanced quality thresholds")
            
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
                
                # Enhanced quality threshold based on distribution analysis (RELAXED)
                percentile_90 = np.percentile(theme_similarities, 90)
                percentile_75 = np.percentile(theme_similarities, 75)
                percentile_50 = np.percentile(theme_similarities, 50)
                mean_sim = np.mean(theme_similarities)
                
                # Less strict threshold approach to allow more themes
                if max_sim >= 0.6:  # High-confidence theme (lowered from 0.7)
                    quality_threshold = max(0.35, percentile_75 * 0.8)  # Reduced threshold
                elif max_sim >= 0.4:  # Medium-confidence theme (lowered from 0.5)
                    quality_threshold = max(0.25, percentile_50 * 0.8)  # Reduced threshold
                else:  # Lower-confidence theme
                    quality_threshold = max(0.2, mean_sim * 0.8)  # Reduced threshold
                
                logger.info(f"Theme '{theme['name']}': max_sim={max_sim:.3f}, "
                           f"threshold={quality_threshold:.3f}")
                
                # Find unassigned documents above threshold
                candidate_docs = [
                    j for j, sim in enumerate(theme_similarities) 
                    if sim >= quality_threshold and j not in assigned_docs
                ]
                
                if candidate_docs:
                    # Sort by similarity and apply quality controls
                    candidate_docs.sort(key=lambda x: theme_similarities[x], reverse=True)
                    
                    # Quality-based document count requirements (RELAXED)
                    min_docs = max(1, int(len(docs) * 0.01))  # At least 1% of documents (reduced from 2%)
                    max_docs = min(int(len(docs) * 0.3), 1000)  # At most 30% of documents or 1000 docs (increased)

                    # Take top documents for this theme
                    selected_docs = candidate_docs[:max_docs]
                    
                    if len(selected_docs) >= min_docs:
                        # Mark documents as assigned
                        assigned_docs.update(selected_docs)
                        
                        avg_similarity = np.mean([theme_similarities[j] for j in selected_docs])
                        
                        # Memory optimization: store only document indices and count
                        refined_themes.append({
                            "name": theme["name"],
                            "description": theme["description"],
                            "document_indices": selected_docs,
                            "document_count": len(selected_docs),
                            "avg_similarity": float(avg_similarity),
                            "similarity_threshold": float(quality_threshold),
                            "max_similarity": float(max_sim)
                        })
                        
                        logger.info(f"Theme '{theme['name']}' assigned {len(selected_docs)} docs with avg similarity {avg_similarity:.3f}")
                    else:
                        logger.info(f"Theme '{theme['name']}' had {len(candidate_docs)} candidates but needed min {min_docs} docs")
                else:
                    logger.info(f"Theme '{theme['name']}' had no unassigned documents above threshold {quality_threshold:.3f}")
            
            logger.info(f"Refined clustering complete: {len(refined_themes)} themes with enhanced quality control")
            
            if not refined_themes:
                raise RuntimeError("No themes met enhanced quality thresholds - documents may be too homogeneous or themes too specific")
            
            return refined_themes
            
        except Exception as e:
            logger.error(f"Error in cluster refinement: {e}")
            raise RuntimeError(f"Cluster refinement failed: {e}") from e


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
                
                # 2. Document quality score (15% weight - reduced from 20%)
                # More balanced approach: wider acceptable range
                doc_count = theme["document_count"]
                total_docs = len(docs)
                
                # More lenient optimal range: 2% to 35% of total documents (expanded range)
                optimal_min = max(2, int(total_docs * 0.02))  # Reduced minimum
                optimal_max = int(total_docs * 0.35)  # Increased maximum
                
                if doc_count < optimal_min:
                    # Too few documents - but less penalized
                    quality_score = float(doc_count / optimal_min * 0.8)  # Increased from 0.7
                elif doc_count > optimal_max:
                    # Too many documents - less penalized
                    excess_ratio = (doc_count - optimal_max) / total_docs
                    quality_score = float(max(0.5, 1.0 - excess_ratio * 1.5))  # Reduced penalty
                else:
                    # In optimal range - high confidence
                    quality_score = 1.0
                
                confidence_components.append(float(quality_score * 0.15))  # Reduced weight
                
                # 3. Keyword alignment score (25% weight - increased to compensate)
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
                confidence_components.append(float(keyword_score * 0.25))  # Increased weight
                
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
                if "similarity_threshold" in theme and theme["similarity_threshold"] > 0.3:  # Lowered from 0.5
                    base_confidence += 0.08  # Increased bonus for high-threshold themes (from 0.05)
                
                theme["confidence_score"] = float(min(1.0, base_confidence))  # Cap at 1.0 and ensure Python float
                
                logger.info(f"Theme '{theme['name']}': similarity={similarity_score:.3f}, quality={quality_score:.3f}, "
                           f"keywords={keyword_score:.3f}, query={query_score:.3f}, final={theme['confidence_score']:.3f}")
            
            # Sort by confidence score and select top themes
            themes.sort(key=lambda x: x["confidence_score"], reverse=True)
            
            # Adjust minimum confidence threshold based on available themes (MORE LENIENT)
            if themes:
                max_confidence = float(themes[0]["confidence_score"])
                # More lenient dynamic threshold: at least 50% of the best theme's confidence (reduced from 60%)
                dynamic_threshold = float(max(0.25, max_confidence * 0.5))  # Lowered minimum threshold
                self.min_confidence_score = float(min(self.min_confidence_score, dynamic_threshold))
            
            # Filter by minimum confidence and select appropriate number
            high_confidence_themes = [t for t in themes if t["confidence_score"] >= self.min_confidence_score]
            
            if len(high_confidence_themes) >= self.min_themes_output:
                selected_themes = high_confidence_themes[:self.max_themes_output]
            else:
                # More lenient fallback - accept themes with lower confidence
                min_acceptable_confidence = 0.15  # Further reduced absolute minimum (from 0.2)
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
                    # Generate boolean query for this theme
                    boolean_query_result = await self.query_generator._generate_boolean_query(
                        refined_query=theme["description"],
                        keywords=state.get("keywords", []),
                        filters=[],
                        entities=[],
                        industry=state.get("industry", ""),
                        sub_vertical=state.get("sub_vertical", ""),
                        use_case=theme["name"],
                        defaults_applied={}
                    )
                    
                    # Memory optimization: create clean theme without full document text
                    theme_copy = {
                        "name": theme["name"],
                        "description": theme["description"],
                        "document_count": theme["document_count"],
                        "avg_similarity": theme["avg_similarity"],
                        "confidence_score": theme["confidence_score"],
                        "boolean_query": boolean_query_result if boolean_query_result else "",
                    }
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
            
            # Step 2: Generate potential themes from state using LLM
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
                        "analysis_method": "hybrid_bertopic_llm",
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
                    "analysis_method": "hybrid_bertopic_llm"
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
