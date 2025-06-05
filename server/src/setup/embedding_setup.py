"""
This script sets up the embedding model for the application.
It initializes the embedding model and its components for RAG functionality.

# Embedding Models that will be used:
- HuggingFace SentenceTransformers: For generating embeddings
- Can be extended to use OpenAI embeddings or other providers

# Purpose:
- Generate embeddings for the knowledge base documents
- Support semantic search in RAG pipeline
- Enable similarity search for filters and themes
"""

from sentence_transformers import SentenceTransformer
from typing import List, Optional, Union
import numpy as np
import logging

# Import lazy loader for performance optimization
from src.utils.lazy_model_loader import lazy_loader

logger = logging.getLogger(__name__)

class EmbeddingSetup:
    """
    Sets up and manages embedding models for the application.
    
    Provides methods to generate embeddings for documents and queries
    used in the RAG system.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding setup with lazy loading.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        
        # Register lazy loader instead of immediate initialization
        self._setup_lazy_loading()
        logger.info(f"EmbeddingSetup initialized with lazy loading for model: {self.model_name}")
    
    def _setup_lazy_loading(self):
        """Setup lazy loading for the embedding model."""
        def load_model():
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            return SentenceTransformer(self.model_name)
        
        lazy_loader.register_model(f"embedding_{self.model_name}", load_model)
    
    def _get_model(self):
        """Get the model using lazy loading."""
        if self.model is None:
            self.model = lazy_loader.get_model(f"embedding_{self.model_name}")
        return self.model
    
    def encode_documents(self, documents: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of documents.
        
        Args:
            documents: List of document texts to encode
            
        Returns:
            Numpy array of embeddings
        """
        try:
            model = self._get_model()
            if model is None:
                raise RuntimeError("Failed to load embedding model")
            embeddings = model.encode(documents, convert_to_numpy=True)
            logger.info(f"Generated embeddings for {len(documents)} documents")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to encode documents: {e}")
            raise
    
    def encode_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query.
        
        Args:
            query: Query text to encode
            
        Returns:
            Numpy array embedding for the query
        """
        try:
            model = self._get_model()
            if model is None:
                raise RuntimeError("Failed to load embedding model")
            embedding = model.encode([query], convert_to_numpy=True)[0]
            logger.info(f"Generated embedding for query.")
            return embedding
        except Exception as e:
            logger.error(f"Failed to encode query: {e}")
            raise
    
    def compute_similarity(self, query_embedding: np.ndarray, 
                          doc_embeddings: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity between query and document embeddings.
        
        Args:
            query_embedding: Query embedding vector
            doc_embeddings: Document embedding matrix
            
        Returns:
            Array of similarity scores
        """
        from sklearn.metrics.pairwise import cosine_similarity
        
        similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
        return similarities

# Global embedding setup instance
embedding_setup = EmbeddingSetup()

def get_embedding_model() -> EmbeddingSetup:
    """
    Get the global embedding model instance.
    
    Returns:
        EmbeddingSetup instance
    """
    return embedding_setup

