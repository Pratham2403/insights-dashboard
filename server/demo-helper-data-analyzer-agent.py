from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import numpy as np

class DataAnalyzerAgent:
    def __init__(self):
        # Initialize embedding model for topic modeling
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        # Initialize BERTopic with 10 topics
        self.topic_model = BERTopic(embedding_model=self.embedding_model, nr_topics=10)
        # Initialize summarization pipeline
        self.summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

    def analyze(self, docs):
        # Fit the topic model to the data
        topics, probs = self.topic_model.fit_transform(docs)
        
        # Update topics for better labels
        self.topic_model.update_topics(docs, topics, language="english")
        
        # Get topic labels
        labels = self.topic_model.get_topic_labels()
        
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
            summary = self.summarizer(best_doc, max_length=150, min_length=30, do_sample=False)[0]['summary_text']
            
            # Get the topic name
            name = labels[topic] if labels else f"Topic {topic}"
            
            # Add to themes list
            themes.append({"name": name, "description": summary})
        
        # Return the top 10 themes
        return themes[:10]