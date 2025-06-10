"""
MongoDB Checkpointer for LangGraph Persistence

This module provides MongoDB-based persistence for conversation history across
multiple server runs using LangGraph's built-in MongoDB checkpointing capabilities.

Features:
- Thread-based conversation persistence  
- Cross-server-restart durability
- Built-in state serialization/deserialization
- Configuration-driven setup
- Enhanced conversation history management
- Async-first design for production use

Based on: https://langchain-ai.github.io/langgraph/concepts/persistence/
Guidelines: Modern MongoDB integration with LangGraph built-ins
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import asyncio

from langgraph.checkpoint.mongodb import AsyncMongoDBSaver
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage

from src.config.settings import settings
from src.helpers.states import DashboardState

logger = logging.getLogger(__name__)

class MongoDBPersistenceManager:
    """
    Enhanced MongoDB-based persistence manager for LangGraph workflows.
    
    Provides conversation history persistence across server restarts,
    thread management, state history retrieval, and conversation analytics.
    
    Features:
    - Thread-based conversation isolation
    - Message history tracking
    - State checkpointing with MongoDB
    - Conversation analytics and insights
    - Production-ready error handling
    """
    
    def __init__(self, mongodb_uri: str = None, database_name: str = None):
        """
        Initialize MongoDB persistence manager.
        
        Args:
            mongodb_uri: MongoDB connection URI (defaults to environment variable)
            database_name: Database name (defaults to environment variable)
        """
        self.mongodb_uri = mongodb_uri or settings.MONGODB_URI
        self.database_name = database_name or settings.MONGODB_DATABASE
        self.collection_name = settings.MONGODB_COLLECTION
        
        # Initialize the MongoDB checkpointer
        self._checkpointer: Optional[AsyncMongoDBSaver] = None
        self._context_manager = None
        self._is_connected = False
        
        logger.info(f"MongoDB Persistence Manager initialized")
        logger.info(f"URI: {self.mongodb_uri}")
        logger.info(f"Database: {self.database_name}")
        logger.info(f"Collection: {self.collection_name}")
    
    @property
    def checkpointer(self) -> AsyncMongoDBSaver:
        """
        Get the MongoDB checkpointer instance, initializing if needed.
        
        Returns:
            AsyncMongoDBSaver instance for LangGraph persistence
        """
        if self._checkpointer is None:
            self._initialize_checkpointer()
        return self._checkpointer
    
    def _initialize_checkpointer(self) -> None:
        """Initialize the MongoDB checkpointer with connection details."""
        try:
            logger.info("Initializing MongoDB checkpointer...")
            
            # Create MongoDB checkpointer using LangGraph's built-in implementation
            # Note: from_conn_string returns a context manager, so we need to enter it
            checkpointer_cm = AsyncMongoDBSaver.from_conn_string(
                conn_string=self.mongodb_uri,
                database_name=self.database_name,
                collection_name=self.collection_name
            )
            
            # Enter the context manager to get the actual checkpointer
            self._checkpointer = checkpointer_cm.__enter__()
            self._context_manager = checkpointer_cm
            
            self._is_connected = True
            logger.info("✅ MongoDB checkpointer initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB checkpointer: {e}")
            raise ConnectionError(f"MongoDB connection failed: {e}")
    
    async def async_initialize(self) -> None:
        """Async initialization for production environments."""
        try:
            await asyncio.to_thread(self._initialize_checkpointer)
            logger.info("✅ Async MongoDB checkpointer initialization completed")
        except Exception as e:
            logger.error(f"❌ Async initialization failed: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Check if MongoDB connection is active."""
        return self._is_connected and self._checkpointer is not None
    
    def close(self) -> None:
        """Close MongoDB connection and cleanup resources."""
        try:
            if self._context_manager:
                self._context_manager.__exit__(None, None, None)
                self._context_manager = None
            self._checkpointer = None
            self._is_connected = False
            logger.info("✅ MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
    
    def __del__(self):
        """Cleanup on object destruction."""
        self.close()
    
    def get_thread_config(self, thread_id: str, checkpoint_ns: str = "") -> RunnableConfig:
        """
        Get LangGraph configuration for a specific thread.
        
        Args:
            thread_id: Conversation thread identifier
            checkpoint_ns: Checkpoint namespace for advanced use cases
            
        Returns:
            RunnableConfig for LangGraph workflows
        """
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
            }
        }
    
    def create_conversation_thread(self, user_id: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        Create a new conversation thread with optional metadata.
        
        Args:
            user_id: Optional user identifier
            metadata: Additional thread metadata
            
        Returns:
            Unique thread identifier
        """
        thread_id = f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(datetime.now()) % 10000}"
        
        if user_id:
            thread_id = f"{user_id}_{thread_id}"
        
        # Initialize thread with metadata
        if metadata:
            logger.info(f"Created conversation thread: {thread_id} with metadata")
        else:
            logger.info(f"Created conversation thread: {thread_id}")
            
        return thread_id
    
    def get_thread_state(self, thread_id: str) -> Optional[DashboardState]:
        """
        Get the current state for a specific thread.
        
        Args:
            thread_id: Conversation thread identifier
            
        Returns:
            Current thread state or None if not found
        """
        try:
            config = self.get_thread_config(thread_id)
            
            # Get state using checkpointer's get method
            checkpoint_tuple = self.checkpointer.get(config)
            
            if checkpoint_tuple and checkpoint_tuple.checkpoint:
                channel_values = checkpoint_tuple.checkpoint.get("channel_values", {})
                logger.info(f"Retrieved state for thread: {thread_id}")
                return channel_values
            else:
                logger.info(f"No state found for thread: {thread_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving thread state for {thread_id}: {e}")
            return None
    
    def get_conversation_messages(self, thread_id: str, limit: int = 50) -> List[BaseMessage]:
        """
        Get conversation messages for a specific thread.
        
        Args:
            thread_id: Conversation thread identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation messages
        """
        try:
            state = self.get_thread_state(thread_id)
            if state and "messages" in state:
                messages = state["messages"]
                # Return latest messages first, limited by the limit parameter
                return messages[-limit:] if len(messages) > limit else messages
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving messages for thread {thread_id}: {e}")
            return []
    
    def get_thread_history(self, thread_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get conversation history for a specific thread with enhanced details.
        
        Args:
            thread_id: Conversation thread identifier
            limit: Maximum number of history entries to retrieve
            
        Returns:
            List of conversation history entries with timestamps and metadata
        """
        try:
            config = self.get_thread_config(thread_id)
            
            # Get history using checkpointer's list method
            history_generator = self.checkpointer.list(config, limit=limit)
            
            history = []
            for checkpoint_tuple in history_generator:
                if checkpoint_tuple and checkpoint_tuple.checkpoint:
                    # Extract comprehensive checkpoint information
                    channel_values = checkpoint_tuple.checkpoint.get("channel_values", {})
                    
                    entry = {
                        "checkpoint_id": checkpoint_tuple.config.get("configurable", {}).get("checkpoint_id"),
                        "created_at": checkpoint_tuple.checkpoint.get("ts"),
                        "thread_id": thread_id,
                        "values": channel_values,
                        "metadata": checkpoint_tuple.metadata or {},
                        "messages_count": len(channel_values.get("messages", [])),
                        "current_stage": channel_values.get("current_stage"),
                        "workflow_status": channel_values.get("workflow_status"),
                        "query_history": channel_values.get("query", [])
                    }
                    history.append(entry)
            
            logger.info(f"Retrieved {len(history)} history entries for thread: {thread_id}")
            return history
            
        except Exception as e:
            logger.error(f"Error retrieving thread history for {thread_id}: {e}")
            return []
    
    def get_conversation_summary(self, thread_id: str) -> Dict[str, Any]:
        """
        Get a summary of the conversation for analytics and monitoring.
        
        Args:
            thread_id: Conversation thread identifier
            
        Returns:
            Conversation summary with key metrics
        """
        try:
            state = self.get_thread_state(thread_id)
            messages = self.get_conversation_messages(thread_id)
            history = self.get_thread_history(thread_id, limit=10)
            
            if not state:
                return {"thread_id": thread_id, "status": "not_found"}
            
            summary = {
                "thread_id": thread_id,
                "status": "active",
                "total_messages": len(messages),
                "query_count": len(state.get("query", [])),
                "current_stage": state.get("current_stage"),
                "workflow_status": state.get("workflow_status"),
                "last_activity": history[0].get("created_at") if history else None,
                "total_checkpoints": len(history),
                "has_refined_query": bool(state.get("refined_query")),
                "keywords_extracted": len(state.get("keywords", [])),
                "themes_generated": len(state.get("themes", [])),
                "hitl_step": state.get("hitl_step"),
                "created_at": datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating conversation summary for {thread_id}: {e}")
            return {"thread_id": thread_id, "status": "error", "error": str(e)}
    
    def list_threads(self, limit: int = 100) -> List[str]:
        """
        List all active conversation threads.
        
        Args:
            limit: Maximum number of threads to retrieve
            
        Returns:
            List of thread IDs
        """
        try:
            # This is a simplified implementation
            # In a production system, you might want to query MongoDB directly
            # to get a list of distinct thread_ids
            logger.info("Listing threads not fully implemented - use thread_id directly")
            return []
            
        except Exception as e:
            logger.error(f"Error listing threads: {e}")
            return []
    
    def delete_thread(self, thread_id: str) -> bool:
        """
        Delete all data for a specific thread.
        
        Args:
            thread_id: Conversation thread identifier
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Note: AsyncMongoDBSaver doesn't have a built-in delete method
            # This would require direct MongoDB operations
            logger.warning("Thread deletion not implemented - use MongoDB operations directly")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting thread: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the MongoDB connection.
        
        Returns:
            Health check results
        """
        try:
            # Try to perform a simple operation
            test_config = self.get_thread_config("health_check_test")
            
            # Attempt to get state (will return None for non-existent thread)
            self.checkpointer.get(test_config)
            
            return {
                "status": "healthy",
                "connected": True,
                "database": self.database_name,
                "collection": self.collection_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global instance for application use
mongodb_persistence = MongoDBPersistenceManager()

def get_mongodb_checkpointer() -> AsyncMongoDBSaver:
    """
    Get the global MongoDB checkpointer instance.
    
    Returns:
        AsyncMongoDBSaver instance for use with LangGraph workflows
    """
    return mongodb_persistence.checkpointer

def get_persistence_manager() -> MongoDBPersistenceManager:
    """
    Get the global persistence manager instance.
    
    Returns:
        MongoDBPersistenceManager instance
    """
    return mongodb_persistence

_async_checkpointer_instance = None
_async_context_manager = None

async def get_async_mongodb_checkpointer():
    """
    Get or create a singleton AsyncMongoDBSaver instance for use with LangGraph workflows.
    Returns:
        AsyncMongoDBSaver instance
    """
    global _async_checkpointer_instance, _async_context_manager
    if _async_checkpointer_instance is None:
        # Use your MongoDB URI and collection name
        DB_URI = "mongodb://localhost:27017"
        DB_NAME = "langgraph"
        COLLECTION = "workflow_state"
        
        # Create MongoDB checkpointer using LangGraph's built-in implementation
        # Note: from_conn_string returns a context manager, so we need to enter it
        checkpointer_cm = AsyncMongoDBSaver.from_conn_string(
            conn_string=DB_URI,
            database_name=DB_NAME,
            collection_name=COLLECTION
        )
        
        # Enter the context manager to get the actual checkpointer
        _async_context_manager = checkpointer_cm
        _async_checkpointer_instance = await checkpointer_cm.__aenter__()
            
    return _async_checkpointer_instance

async def cleanup_async_mongodb_checkpointer():
    """
    Cleanup the async MongoDB checkpointer and close connections.
    Should be called during application shutdown.
    """
    global _async_checkpointer_instance, _async_context_manager
    
    if _async_context_manager is not None:
        try:
            await _async_context_manager.__aexit__(None, None, None)
            logger.info("✅ Async MongoDB checkpointer cleaned up successfully")
        except Exception as e:
            logger.error(f"❌ Error cleaning up async MongoDB checkpointer: {e}")
        finally:
            _async_context_manager = None
            _async_checkpointer_instance = None
