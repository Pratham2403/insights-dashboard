"""
This script sets up the vector database for the application.
It initializes ChromaDB for storing and retrieving embeddings used in RAG.

# Vector Database:
- ChromaDB: For storing document embeddings and metadata
- Supports semantic search and similarity retrieval
- Used for RAG context retrieval

# Collections:
- filters_collection: Stores Sprinklr filter information
- themes_collection: Stores theme examples and patterns
- use_cases_collection: Stores complete use case examples
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import logging
import os

logger = logging.getLogger(__name__)

class VectorDBSetup:
    """
    Sets up and manages ChromaDB vector database for RAG functionality.
    
    Provides methods to create collections, store embeddings, and perform
    semantic search for the knowledge base.
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize the vector database setup.
        
        Args:
            persist_directory: Directory to persist the database
        """
        self.persist_directory = persist_directory
        self.client = None
        self.collections = {}
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client."""
        try:
            # Ensure directory exists
            os.makedirs(self.persist_directory, exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            logger.info(f"Successfully initialized ChromaDB at {self.persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def create_collection(self, collection_name: str, 
                         embedding_function=None) -> chromadb.Collection:
        """
        Create or get a collection in the vector database.
        
        Args:
            collection_name: Name of the collection
            embedding_function: Optional embedding function
            
        Returns:
            ChromaDB collection instance
        """
        try:
            if embedding_function is None:
                # Use default sentence transformer embedding
                from chromadb.utils import embedding_functions
                embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
            
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_function
            )
            
            self.collections[collection_name] = collection
            logger.info(f"Created/retrieved collection: {collection_name}")
            return collection
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise
    
    def add_documents(self, collection_name: str, documents: List[str],
                     metadatas: Optional[List[Dict]] = None,
                     ids: Optional[List[str]] = None):
        """
        Add documents to a collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional IDs for each document
        """
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                collection = self.create_collection(collection_name)
            
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to add documents to {collection_name}: {e}")
            raise
    
    def search_documents(self, collection_name: str, query: str,
                        n_results: int = 5) -> Dict[str, Any]:
        """
        Search for similar documents in a collection.
        
        Args:
            collection_name: Name of the collection to search
            query: Query text
            n_results: Number of results to return
            
        Returns:
            Search results with documents and metadata
        """
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                raise ValueError(f"Collection {collection_name} not found")
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            logger.info(f"Search completed for query in {collection_name}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search in {collection_name}: {e}")
            raise
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection information
        """
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                raise ValueError(f"Collection {collection_name} not found")
            
            count = collection.count()
            return {
                "name": collection_name,
                "count": count
            }
            
        except Exception as e:
            logger.error(f"Failed to get info for {collection_name}: {e}")
            raise

# Global vector DB setup instance
vector_db_setup = VectorDBSetup()

def get_vector_db() -> VectorDBSetup:
    """
    Get the global vector database instance.
    
    Returns:
        VectorDBSetup instance
    """
    return vector_db_setup

def initialize_collections():
    """
    Initialize default collections for the application.
    """
    collections_to_create = [
        "filters_collection",
        "themes_collection", 
        "use_cases_collection",
        "keyword_patterns_collection"
    ]
    
    for collection_name in collections_to_create:
        vector_db_setup.create_collection(collection_name)
        logger.info(f"Initialized collection: {collection_name}")