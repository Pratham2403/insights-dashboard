"""
RAG (Retrieval-Augmented Generation) system for Sprinklr filters.

This module implements the RAG functionality for retrieving relevant filter
information and context to help agents make better decisions about user queries.

# Purpose:
- Load and index Sprinklr filter information
- Support query refinement with contextual filter suggestions
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.utils.files_helper import import_module_from_file
from src.config.settings import settings

logger = logging.getLogger(__name__)

class FiltersRAG:
    """
    RAG system for Sprinklr filters and related context.
    
    Manages the loading, indexing, and retrieval of filter information
    to provide context for query refinement and data collection.
    """
    
    def __init__(self):
        """Initialize the filters RAG system."""
        # Import here to avoid circular imports
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            setup_dir = os.path.join(current_dir, '..', 'setup')
            
            vector_db_path = os.path.join(setup_dir, 'vector_db_setup.py')
            embedding_path = os.path.join(setup_dir, 'embedding_setup.py')
            
            vector_db_module = import_module_from_file(vector_db_path, 'vector_db_setup')
            
            self.vector_db = vector_db_module.get_vector_db()
            
            # Try to get embedding model, but it's optional
            try:
                embedding_module = import_module_from_file(embedding_path, 'embedding_setup')
                self.embedding_model = embedding_module.get_embedding_model()
            except Exception as e:
                logger.warning(f"Could not load embedding model: {e}")
                self.embedding_model = None
                
            logger.info("Successfully initialized vector database for RAG")
            
        except Exception as e:
            logger.error(f"Error importing setup modules: {e}")
            # Don't silently fail - raise the error so we can fix it
            raise RuntimeError(f"Failed to initialize vector database: {e}")
        
        self.knowledge_base_path = Path(__file__).parent.parent / "knowledge_base"
        
        # Collection names
        self.themes_collection = "themes_collection"
        self.patterns_collection = "keyword_patterns_collection"
        self.use_cases_collection = "use_cases_collection"
        
        # Initialize collections after vector_db is set up
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize and populate collections with knowledge base data."""
        try:
            # Check if vector_db is available
            if self.vector_db is None:
                raise RuntimeError("Vector database not available, cannot initialize collections")
            
            # Create collections if they don't exist
            self.vector_db.create_collection(self.themes_collection)
            self.vector_db.create_collection(self.patterns_collection)
            self.vector_db.create_collection(self.use_cases_collection)
            
            # Load and index data
            self._load_themes_data()
            self._load_keyword_patterns()
            self._load_use_cases()
            
            logger.info("Successfully initialized all RAG collections")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG collections: {e}")
            # Re-raise the error so calling code knows initialization failed
            raise
    


    



    def _load_themes_data(self):
        """Load and index themes data from themes.json file."""
        if self.vector_db is None:
            raise RuntimeError("Vector database not available, cannot load themes data")
            
        try:
            # Load themes from themes.json file
            themes_file = self.knowledge_base_path / "themes.json"
            
            if not themes_file.exists():
                raise FileNotFoundError(f"Themes file not found at: {themes_file}")
                
            with open(themes_file, 'r', encoding='utf-8') as f:
                themes_data = json.load(f)
            
            # Extract themes from the JSON structure
            if not isinstance(themes_data, dict) or "themes" not in themes_data:
                raise ValueError("Invalid themes.json structure: expected 'themes' key at root level")
                
            themes_list = themes_data["themes"]
            if not isinstance(themes_list, list):
                raise ValueError("Invalid themes.json structure: 'themes' should be a list")
                
            if not themes_list:
                raise ValueError("No themes found in themes.json file")
            
            documents = []
            metadatas = []
            ids = []
            
            for i, theme in enumerate(themes_list):
                # Validate theme structure
                if not isinstance(theme, dict) or "name" not in theme or "description" not in theme:
                    logger.warning(f"Skipping invalid theme at index {i}: missing name or description")
                    continue
                
                # Extract keywords, handling both list and missing keywords
                keywords = theme.get("keywords", [])
                if not isinstance(keywords, list):
                    keywords = []
                
                # Extract related_filters, handling both list and missing filters
                related_filters = theme.get("related_filters", [])
                if not isinstance(related_filters, list):
                    related_filters = []
                
                # Extract related_topics for additional context if available
                related_topics = theme.get("related_topics", [])
                if not isinstance(related_topics, list):
                    related_topics = []
                
                # Create comprehensive document text for semantic search
                doc_text = f"{theme['name']}: {theme['description']}"
                
                # Add keywords to document text if available
                if keywords:
                    doc_text += f" Keywords: {', '.join(keywords)}"
                
                # Add related filters to document text if available
                if related_filters:
                    doc_text += f" Related Filters: {', '.join(related_filters)}"
                
                # Add related topics to document text if available and not empty
                if related_topics:
                    # Extract topic names/descriptions for searchable text
                    topic_text = []
                    for topic in related_topics:
                        if isinstance(topic, dict):
                            if "name" in topic:
                                topic_text.append(topic["name"])
                            if "description" in topic:
                                topic_text.append(topic["description"])
                        elif isinstance(topic, str):
                            topic_text.append(topic)
                    
                    if topic_text:
                        doc_text += f" Related Topics: {', '.join(topic_text)}"
                
                documents.append(doc_text)
                
                # Convert lists to strings for ChromaDB compatibility
                metadata = {
                    "name": theme["name"],
                    "description": theme["description"],
                    "keywords": ", ".join(keywords) if keywords else "",
                    "related_filters": ", ".join(related_filters) if related_filters else "",
                    "related_topics": json.dumps(related_topics) if related_topics else "[]"
                }
                metadatas.append(metadata)
                ids.append(f"theme_{i}")
            
            if not documents:
                raise ValueError("No valid themes found in themes.json file")
            
            self.vector_db.add_documents(
                self.themes_collection,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Loaded {len(documents)} theme items from themes.json")
            
        except Exception as e:
            logger.error(f"Failed to load themes data: {e}")
            raise
    
    def _load_keyword_patterns(self):
        """Load and index keyword query patterns."""
        if self.vector_db is None:
            raise RuntimeError("Vector database not available, cannot load keyword patterns")
            
        try:
            patterns_file = self.knowledge_base_path / "keyword_query_patterns.json"
            
            with open(patterns_file, 'r') as f:
                patterns_data = json.load(f)
            
            documents = []
            metadatas = []
            ids = []
            
            # Add syntax keywords
            for i, keyword in enumerate(patterns_data.get("syntax_keywords", [])):
                doc_text = f"Boolean syntax keyword: {keyword}"
                documents.append(doc_text)
                metadatas.append({"type": "syntax", "keyword": keyword})
                ids.append(f"syntax_{i}")
            
            # Add example queries
            for i, query in enumerate(patterns_data.get("example_queries", [])):
                doc_text = f"Example boolean query: {query}"
                documents.append(doc_text)
                metadatas.append({"type": "example", "query": query})
                ids.append(f"example_{i}")
            
            self.vector_db.add_documents(
                self.patterns_collection,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Loaded {len(documents)} keyword pattern items")
            
        except Exception as e:
            logger.error(f"Failed to load keyword patterns: {e}")
            raise
    
    def _load_use_cases(self):
        """Load and index complete use cases from JSON file."""
        if self.vector_db is None:
            logger.warning("Vector database not available, skipping use cases loading")
            return
            
        try:
            # Load use cases from JSON file using settings configuration
            use_case_file_path = Path(settings.USE_CASE_FILE_PATH)
            
            # Handle relative path resolution
            if not use_case_file_path.is_absolute():
                # Resolve relative to the project root
                current_dir = Path(__file__).parent.parent.parent
                use_case_file_path = current_dir / use_case_file_path
            
            if not use_case_file_path.exists():
                logger.error(f"Use case file not found at: {use_case_file_path}")
                return
                
            with open(use_case_file_path, 'r', encoding='utf-8') as f:
                use_cases_data = json.load(f)
            
            if not isinstance(use_cases_data, list):
                logger.error("Use cases data should be a list")
                return
            
            documents = []
            metadatas = []
            ids = []
            
            for use_case in use_cases_data:
                # Create searchable document text from the use case data
                doc_text = f"{use_case.get('category', '')}: {use_case.get('description', '')}"
                
                # Add features to the document text if they exist
                if 'features' in use_case and use_case['features']:
                    features_text = " ".join([
                        f"{feature.get('name', '')}: {feature.get('description', '')}" 
                        for feature in use_case['features'] 
                        if isinstance(feature, dict) and ('name' in feature or 'description' in feature)
                    ])
                    if features_text:
                        doc_text += f" Features: {features_text}"
                
                documents.append(doc_text)
                
                # Store complete metadata preserving the original structure
                metadata = {
                    "id": use_case.get("id"),
                    "category": use_case.get("category", ""),
                    "description": use_case.get("description", ""),
                    "features": json.dumps(use_case.get("features", [])) if use_case.get("features") else "[]"
                }
                metadatas.append(metadata)
                ids.append(f"use_case_{use_case.get('id', len(ids))}")
            
            # Add documents to vector database
            self.vector_db.add_documents(
                self.use_cases_collection,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Loaded {len(documents)} use case items from {use_case_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load use cases: {e}")
            raise







    def search_themes(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for relevant themes based on query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of relevant theme information
        """
        if self.vector_db is None:
            logger.warning("Vector database not available, returning empty search results")
            return []
            
        try:
            results = self.vector_db.search_documents(
                self.themes_collection,
                query=query,
                n_results=n_results
            )
            
            return results.get("metadatas", [[]])[0]
            
        except Exception as e:
            logger.error(f"Failed to search themes: {e}")
            return []
    
    def search_relevant_themes(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for relevant themes based on query (alias for search_themes).
        
        This method provides backward compatibility for existing code that expects
        search_relevant_themes method name.
        
        Args:
            query: Search query
            top_k: Number of results to return (alias for n_results)
            
        Returns:
            List of relevant theme information
        """
        return self.search_themes(query, n_results=top_k)
    
    def search_keyword_patterns(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for relevant keyword patterns based on query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of relevant keyword pattern information
        """
        if self.vector_db is None:
            logger.warning("Vector database not available, returning empty search results")
            return []
            
        try:
            results = self.vector_db.search_documents(
                self.patterns_collection,
                query=query,
                n_results=n_results
            )
            
            return results.get("metadatas", [[]])[0]
            
        except Exception as e:
            logger.error(f"Failed to search keyword patterns: {e}")
            return []
    
    def search_use_cases(self, query: str, n_results: int = 2) -> List[Dict[str, Any]]:
        """
        Search for relevant use cases based on query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of relevant use case information
        """
        if self.vector_db is None:
            logger.warning("Vector database not available, returning empty search results")
            return []
            
        try:
            results = self.vector_db.search_documents(
                self.use_cases_collection,
                query=query,
                n_results=n_results
            )
            
            return results.get("metadatas", [[]])[0]
            
        except Exception as e:
            logger.error(f"Failed to search use cases: {e}")
            return []
    
    def get_context_for_query(self, query: str) -> Dict[str, Any]:
        """
        Get comprehensive context for a user query.
        
        Args:
            query: User query
            
        Returns:
            Dictionary containing relevant context from all collections
        """
        try:
            context = {
                "themes": self.search_themes(query),
                "keyword_patterns": self.search_keyword_patterns(query),
                "use_cases": self.search_use_cases(query)
            }
            
            logger.info(f"Retrieved context for query: {query}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to get context for query: {e}")
            return {}

# Global RAG instance (lazily initialized)
_filters_rag_instance = None

def get_filters_rag() -> FiltersRAG:
    """
    Get the global filters RAG instance.
    
    Returns:
        FiltersRAG instance
    """
    global _filters_rag_instance
    if _filters_rag_instance is None:
        _filters_rag_instance = FiltersRAG()
    return _filters_rag_instance