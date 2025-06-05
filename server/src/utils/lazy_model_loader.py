"""
Lazy Model Loader for Performance Optimization

This module provides lazy loading for heavy ML models to improve startup performance.
Models are only loaded when first accessed, significantly reducing initialization time.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
import weakref

logger = logging.getLogger(__name__)

class LazyModelLoader:
    """
    Singleton class for managing lazy loading of ML models.
    
    Provides thread-safe lazy initialization of expensive models like:
    - Embedding models (SentenceTransformers)
    - Classification models (HuggingFace pipelines)
    - Vector databases
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._models: Dict[str, Any] = {}
            self._loaders: Dict[str, Callable] = {}
            self._loading_locks: Dict[str, threading.Lock] = {}
            self._initialized = True
            logger.info("LazyModelLoader initialized")
    
    def register_model(self, name: str, loader_func: Callable, force_reload: bool = False):
        """
        Register a model with its loader function.
        
        Args:
            name: Unique model name
            loader_func: Function that loads and returns the model
            force_reload: Whether to force reload if model exists
        """
        if force_reload or name not in self._loaders:
            self._loaders[name] = loader_func
            self._loading_locks[name] = threading.Lock()
            if name in self._models:
                del self._models[name]  # Clear existing model
            logger.info(f"Registered lazy loader for model: {name}")
    
    def get_model(self, name: str) -> Optional[Any]:
        """
        Get a model, loading it lazily if needed.
        
        Args:
            name: Model name
            
        Returns:
            Loaded model instance or None if not found
        """
        if name not in self._loaders:
            logger.warning(f"No loader registered for model: {name}")
            return None
        
        # Check if model is already loaded
        if name in self._models:
            return self._models[name]
        
        # Load model with thread safety
        with self._loading_locks[name]:
            # Double-check pattern
            if name in self._models:
                return self._models[name]
            
            try:
                logger.info(f"Loading model lazily: {name}")
                start_time = time.time()
                
                model = self._loaders[name]()
                self._models[name] = model
                
                load_time = time.time() - start_time
                logger.info(f"Model '{name}' loaded successfully in {load_time:.2f}s")
                
                return model
                
            except Exception as e:
                logger.error(f"Failed to load model '{name}': {e}")
                return None
    
    def is_loaded(self, name: str) -> bool:
        """Check if a model is currently loaded."""
        return name in self._models
    
    def unload_model(self, name: str):
        """Unload a specific model to free memory."""
        if name in self._models:
            del self._models[name]
            logger.info(f"Unloaded model: {name}")
    
    def clear_all(self):
        """Clear all loaded models."""
        self._models.clear()
        logger.info("Cleared all loaded models")
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return {
            "loaded_models": list(self._models.keys()),
            "registered_loaders": list(self._loaders.keys()),
            "total_loaded": len(self._models)
        }


def lazy_model(model_name: str):
    """
    Decorator for lazy model loading.
    
    Args:
        model_name: Name of the model to load lazily
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            loader = LazyModelLoader()
            model = loader.get_model(model_name)
            if model is None:
                raise RuntimeError(f"Failed to load model: {model_name}")
            return func(model, *args, **kwargs)
        return wrapper
    return decorator


# Global instance
lazy_loader = LazyModelLoader()


def setup_embedding_model_lazy():
    """Setup lazy loading for embedding model."""
    def load_embedding_model():
        from sentence_transformers import SentenceTransformer
        logger.info("Loading SentenceTransformer model...")
        return SentenceTransformer("all-MiniLM-L6-v2")
    
    lazy_loader.register_model("embedding", load_embedding_model)


def setup_classification_model_lazy():
    """Setup lazy loading for classification model."""
    def load_classification_model():
        from transformers import pipeline
        logger.info("Loading zero-shot classification model...")
        return pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1  # Use CPU for compatibility
        )
    
    lazy_loader.register_model("classifier", load_classification_model)


def setup_all_lazy_models():
    """Setup all lazy model loaders."""
    setup_embedding_model_lazy()
    setup_classification_model_lazy()
    logger.info("All lazy model loaders configured")


# Initialize lazy loaders when module is imported
setup_all_lazy_models()
