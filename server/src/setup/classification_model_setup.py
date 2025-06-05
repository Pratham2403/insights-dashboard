"""
This module is used to Initialize and Set Up the Classification Model for the Application.

The Classification Model is Used by the Data Analyzer Agent to Classify the Data into Different Themes (Buckets) based on the User Query and the Data Collected from the Sprinklr API.

# Functionality:
- This Module Provides the Functinality to Initialize and Set Up the Classification Model.
- Functinns to Take in the List of Data and the Refined User Prompt and Classify  and Return the Data into Different Themes (Buckets) based on the User Query.
- The Classification Model can be a Pre-trained Model or a Custom Model that is Trained on the Data Collected from the Sprinklr API.
- The Classification Model can be a Zero-Shot Classification Model, Clustering Model, or any other Model that can be used to classify the data into different themes.
- You can use the Hugging Face Transformers Library to Load and Use the Pre-trained Models for Zero-Shot Classification or any other Classification Task like the "facebook/bart-large-mnli".

"""

import logging
from typing import List, Dict, Any, Optional
import os
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Import lazy loader for performance optimization
from src.utils.lazy_model_loader import lazy_loader

logger = logging.getLogger(__name__)

class ClassificationModelSetup:
    """
    Setup and manage classification models for data analysis.
    
    This class provides functionality to initialize various classification models
    including zero-shot classification, clustering, and custom models.
    """
    
    def __init__(self):
        """Initialize the classification model setup with lazy loading"""
        self.zero_shot_classifier = None
        self.clustering_model = None
        self.vectorizer = None
        self.model_cache = {}
        
        # Setup lazy loading for common models
        self._setup_lazy_loading()
        
        logger.info("ClassificationModelSetup initialized with lazy loading")
    
    def _setup_lazy_loading(self):
        """Setup lazy loading for classification models."""
        def load_zero_shot_classifier():
            logger.info("Loading zero-shot classification model...")
            return pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1  # Use CPU for compatibility
            )
        
        def load_clustering_model():
            logger.info("Loading clustering model...")
            return KMeans(n_clusters=5, random_state=42, n_init=10)
        
        def load_vectorizer():
            logger.info("Loading TF-IDF vectorizer...")
            return TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
        
        # Register all models for lazy loading
        lazy_loader.register_model("zero_shot_classifier", load_zero_shot_classifier)
        lazy_loader.register_model("clustering_model", load_clustering_model)
        lazy_loader.register_model("tfidf_vectorizer", load_vectorizer)

    def get_zero_shot_classifier(self, model_name: str = "facebook/bart-large-mnli"):
        """
        Get or initialize zero-shot classification model using lazy loading.
        
        Args:
            model_name: Hugging Face model name for zero-shot classification
            
        Returns:
            Zero-shot classification pipeline
        """
        try:
            if model_name == "facebook/bart-large-mnli":
                # Use lazy loading for the default model
                classifier = lazy_loader.get_model("zero_shot_classifier")
                if classifier:
                    return classifier
            
            # Fallback for custom models or if lazy loading fails
            if model_name not in self.model_cache:
                logger.info(f"Loading zero-shot classifier: {model_name}")
                self.model_cache[model_name] = pipeline(
                    "zero-shot-classification",
                    model=model_name,
                    device=-1  # Use CPU for compatibility
                )
            
            return self.model_cache[model_name]
            
        except Exception as e:
            logger.error(f"Error loading zero-shot classifier: {str(e)}")
            # Return a mock classifier for development
            return self._get_mock_classifier()
    
    def get_clustering_model(self, n_clusters: int = 5, **kwargs):
        """
        Get or initialize clustering model.
        
        Args:
            n_clusters: Number of clusters
            **kwargs: Additional parameters for KMeans
            
        Returns:
            Configured KMeans clustering model
        """
        try:
            if not self.clustering_model or self.clustering_model.n_clusters != n_clusters:
                logger.info(f"Initializing clustering model with {n_clusters} clusters")
                self.clustering_model = KMeans(
                    n_clusters=n_clusters,
                    random_state=42,
                    **kwargs
                )
            
            return self.clustering_model
            
        except Exception as e:
            logger.error(f"Error initializing clustering model: {str(e)}")
            return None
    
    def get_text_vectorizer(self, max_features: int = 1000, **kwargs):
        """
        Get or initialize text vectorizer for clustering.
        
        Args:
            max_features: Maximum number of features
            **kwargs: Additional parameters for TfidfVectorizer
            
        Returns:
            Configured TfidfVectorizer
        """
        try:
            if not self.vectorizer:
                logger.info("Initializing text vectorizer")
                self.vectorizer = TfidfVectorizer(
                    max_features=max_features,
                    stop_words='english',
                    ngram_range=(1, 2),
                    **kwargs
                )
            
            return self.vectorizer
            
        except Exception as e:
            logger.error(f"Error initializing text vectorizer: {str(e)}")
            return None
    
    def classify_text_zero_shot(
        self, 
        texts: List[str], 
        candidate_labels: List[str],
        model_name: str = "facebook/bart-large-mnli"
    ) -> List[Dict[str, Any]]:
        """
        Classify texts using zero-shot classification.
        
        Args:
            texts: List of texts to classify
            candidate_labels: List of possible labels/themes
            model_name: Model to use for classification
            
        Returns:
            List of classification results
        """
        try:
            classifier = self.get_zero_shot_classifier(model_name)
            results = []
            
            for text in texts:
                result = classifier(text, candidate_labels)
                results.append({
                    "text": text,
                    "labels": result["labels"],
                    "scores": result["scores"],
                    "predicted_label": result["labels"][0],
                    "confidence": result["scores"][0]
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in zero-shot classification: {str(e)}")
            return []
    
    def cluster_texts(
        self, 
        texts: List[str], 
        n_clusters: int = 5
    ) -> Dict[str, Any]:
        """
        Cluster texts using TF-IDF and KMeans.
        
        Args:
            texts: List of texts to cluster
            n_clusters: Number of clusters
            
        Returns:
            Dictionary containing cluster results
        """
        try:
            # Vectorize texts
            vectorizer = self.get_text_vectorizer()
            text_vectors = vectorizer.fit_transform(texts)
            
            # Perform clustering
            clustering_model = self.get_clustering_model(n_clusters)
            cluster_labels = clustering_model.fit_predict(text_vectors)
            
            # Organize results
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append({
                    "text": texts[i],
                    "index": i
                })
            
            # Get cluster centers and keywords
            feature_names = vectorizer.get_feature_names_out()
            cluster_keywords = {}
            
            for cluster_id in range(n_clusters):
                center = clustering_model.cluster_centers_[cluster_id]
                top_indices = center.argsort()[-10:][::-1]
                cluster_keywords[cluster_id] = [feature_names[i] for i in top_indices]
            
            return {
                "clusters": clusters,
                "cluster_labels": cluster_labels.tolist(),
                "cluster_keywords": cluster_keywords,
                "n_clusters": n_clusters,
                "vectorizer": vectorizer,
                "model": clustering_model
            }
            
        except Exception as e:
            logger.error(f"Error in text clustering: {str(e)}")
            return {}
    
    def _get_mock_classifier(self):
        """Return a mock classifier for development/testing"""
        class MockClassifier:
            def __call__(self, text, candidate_labels):
                import random
                # Return mock results
                scores = [random.random() for _ in candidate_labels]
                scores.sort(reverse=True)
                labels = candidate_labels.copy()
                random.shuffle(labels)
                
                return {
                    "labels": labels,
                    "scores": scores
                }
        
        logger.warning("Using mock classifier - install transformers for real classification")
        return MockClassifier()
    
    def cleanup(self):
        """Cleanup loaded models and free memory"""
        try:
            self.model_cache.clear()
            self.zero_shot_classifier = None
            self.clustering_model = None
            self.vectorizer = None
            logger.info("Classification models cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")