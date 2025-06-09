"""
BERTopic-based Data Analyzer Agent exactly mimicking demo-helper-data-analyzer-agent.py

Key features:
- Uses BERTopic for theme identification  
- Uses SentenceTransformers for embeddings
- Uses transformers for summarization
- Processes hits separately from LangGraph state
- Updates themes state as final output
- Throws errors when dependencies are missing or when analysis fails
"""
import logging
from typing import Dict, Any, List, Optional

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import numpy as np

logger = logging.getLogger(__name__)

class DataAnalyzerAgent:
    """
    BERTopic-based Data Analyzer exactly mimicking demo-helper-data-analyzer-agent.py
    
    Processes hits from Sprinklr API and generates themes using BERTopic.
    """
    
    def __init__(self):
        """
        Initialize BERTopic components exactly matching demo helper.
        Throws errors if models cannot be initialized.
        """
        try:
            # Initialize embedding model for topic modeling
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            # Initialize BERTopic with nr_topics
            self.topic_model = BERTopic(embedding_model=self.embedding_model, nr_topics=5)
            # Initialize summarization pipeline
            self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            logger.info("BERTopic models initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize BERTopic models: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def analyze(self, docs: List[str]) -> List[Dict[str, Any]]:
        """
        Main analyze method exactly matching demo helper implementation.
        
        Args:
            docs: List of document strings for analysis
            
        Returns:
            List of themes with name and description
            
        Raises:
            ValueError: If insufficient documents provided
            RuntimeError: If BERTopic analysis fails
        """
        if not docs:
            raise ValueError("No documents provided for analysis")
        
        if len(docs) < 2:
            raise ValueError("At least 2 documents required for BERTopic analysis")
        
        try:
            # Fit the topic model to the data
            topics, probs = self.topic_model.fit_transform(docs)
            
            self.topic_model.update_topics(docs, topics)
            
            # Generate topic labels - BERTopic v0.17.0+ method
            labels = self.topic_model.generate_topic_labels()
            
            # Generate themes with descriptions
            themes = []
            for topic in range(-1, self.topic_model.get_topic_info()["Topic"].max() + 1):
                if topic == -1:
                    continue  # Skip outlier topic
                
                # Find documents belonging to this topic
                topic_docs_idx = [i for i, t in enumerate(topics) if t == topic]
                if not topic_docs_idx:
                    continue
                
                # Find the most representative document
                best_doc_idx = max(topic_docs_idx, key=lambda i: probs[i])
                best_doc = docs[best_doc_idx]
                
                # Summarize the most representative document
                try:
                    # Adjust max_length based on document length to avoid warnings
                    doc_length = len(best_doc.split())
                    max_len = min(150, max(30, doc_length * 2))  # Ensure reasonable limits
                    min_len = min(30, max(10, doc_length // 2))  # Ensure min_len <= max_len
                    
                    summary = self.summarizer(best_doc, max_length=max_len, min_length=min_len, do_sample=False)[0]['summary_text']
                except Exception as e:
                    error_msg = f"Summarization failed for topic {topic}: {e}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg) from e
                
                # Get the topic name
                name = labels[topic] if labels and topic < len(labels) else f"Topic {topic}"
                
                # Add to themes list
                themes.append({"name": name, "description": summary})
            
            # Return the top 10 themes
            themes_result = themes[:10]
            logger.info(f"Generated {len(themes_result)} themes using BERTopic")
            return themes_result
            
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise  # Re-raise our custom errors
            error_msg = f"BERTopic analysis failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    async def analyze_hits_and_state(self, hits: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Method that processes hits and state separately (as per requirement 2).
        
        Args:
            hits: List of hits from Sprinklr API (NOT stored in state)
            state: LangGraph state for context
            
        Returns:
            Dictionary with themes for state update
            
        Raises:
            ValueError: If no hits provided or no documents extracted
            RuntimeError: If analysis fails
        """
        if not hits:
            raise ValueError("No hits provided for analysis")
        
        try:
            logger.info(f"Analyzing {len(hits)} hits with BERTopic")
            
            # Extract text content from hits for analysis
            documents = self._extract_documents_from_hits(hits)
            
            if not documents:
                raise ValueError("No documents could be extracted from hits")
            
            # Use the main analyze method (exactly matching demo helper)
            themes = self.analyze(documents)
            
            return {"themes": themes}
            
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise  # Re-raise our custom errors
            error_msg = f"Error in analyze_hits_and_state: {e}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
    
    def _extract_documents_from_hits(self, hits: List[Dict[str, Any]]) -> List[str]:
        """
        Extract text content from Sprinklr API hits for analysis.
        This method handles nested objects and various field structures.
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
                    # Check for nested data structures
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

# Factory for LangGraph compatibility (backwards compatibility)
def create_data_analyzer():
    """Create data analyzer for LangGraph integration."""
    return DataAnalyzerAgent()
