"""
Data Processing Agent for the Sprinklr Insights Dashboard.
"""
from typing import Dict, List, Any, Optional, Union
import json
import logging
import httpx
import asyncio
from datetime import datetime
from collections import Counter, defaultdict
import re
import math
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config.settings import settings
from app.models.state import SearchResult, Theme
from uuid import uuid4


logger = logging.getLogger(__name__)


# Define system prompt for the Data Processing agent
DATA_PROC_SYSTEM_PROMPT = """You are an expert in analyzing social media and news data.
Your task is to process search results and extract meaningful themes and insights.

You must follow these rules when extracting themes:
1. Focus on key topics and trends in the data
2. Identify recurring patterns and themes
3. Prioritize themes relevant to the user's goals
4. Extract both positive and negative sentiment themes
5. Rank themes by relevance and frequency
6. Provide specific examples for each theme
7. Be objective and data-driven in your analysis

A good theme:
- Has a clear, concise name
- Is supported by multiple data points
- Is directly relevant to the products and goals
- Provides actionable insights
- Captures a significant trend or pattern
"""


class DataProcessingAgent:
    """
    Agent responsible for processing search results and extracting themes.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the Data Processing agent.
        
        Args:
            model_name: The name of the language model to use.
        """
        self.model_name = model_name or settings.DEFAULT_MODEL_NAME
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0.2,
            # max_tokens=2000,
            google_api_key=settings.GEMINI_API_KEY
        )
        self.external_api_url = settings.EXTERNAL_API_URL
        self.external_api_key = settings.EXTERNAL_API_KEY
    
    async def process_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process search results and extract themes.
        
        Args:
            state: The current state of the conversation.
            
        Returns:
            Updated state with extracted themes.
        """
        # Initialize search_results and themes if not present
        if "search_results" not in state:
            state["search_results"] = []
        
        if "themes" not in state:
            state["themes"] = []
        
        # Check if there are query batches to process
        if not state.get("query_batches"):
            logger.warning("No query batches found in state")
            
            # Add a message to the state
            state["messages"].append({
                "role": "system",
                "content": "No query batches found to process"
            })
            
            return state
        
        # Get the latest query batch
        latest_batch = state["query_batches"][-1]
        
        # Fetch search results for each query in the batch
        search_results = []
        for query in latest_batch["queries"]:
            results = await self._fetch_search_results(query)
            search_results.extend(results)
        
        # Add search results to state
        state["search_results"] = search_results
        
        # Extract themes from search results
        if search_results:
            themes = await self._extract_themes(search_results, state["user_requirements"])
            
            # Add themes to state
            state["themes"] = [theme.dict() for theme in themes]
        
        # Update current step
        state["current_step"] = "DATA_PROCESSING"
        
        return state
    
    async def _fetch_search_results(self, query: str) -> List[Dict[str, Any]]:
        """
        Fetch search results from the external API.
        
        Args:
            query: The Boolean keyword query.
            
        Returns:
            List of search results.
        """
        # In a real implementation, this would call an external API
        # For this example, we'll simulate results
        
        # Check if we have real API settings
        if self.external_api_url and self.external_api_key:
            try:
                async with httpx.AsyncClient(timeout=settings.EXTERNAL_API_TIMEOUT) as client:
                    headers = {
                        "Authorization": f"Bearer {self.external_api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "query": query,
                        "limit": 50  # Number of results to retrieve
                    }
                    response = await client.post(
                        self.external_api_url,
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Convert API response to SearchResult format
                    return [
                        SearchResult(
                            id=item.get("id", str(uuid4())),
                            content=item.get("content", ""),
                            source=item.get("source", "unknown"),
                            timestamp=datetime.fromisoformat(item.get("timestamp", datetime.now().isoformat())),
                            metadata=item.get("metadata", {})
                        ).dict()
                        for item in data.get("results", [])
                    ]
            except Exception as e:
                logger.error(f"Error fetching search results: {e}")
                # Return simulated results on error
                return self._simulate_search_results(query)
        else:
            # No API configured, return simulated results
            return self._simulate_search_results(query)
    
    def _simulate_search_results(self, query: str) -> List[Dict[str, Any]]:
        """
        Simulate search results for testing.
        
        Args:
            query: The Boolean keyword query.
            
        Returns:
            List of simulated search results.
        """
        # Extract key terms from the query to use in simulated results
        terms = re.findall(r'\"([^\"]+)\"|\w+', query)
        terms = [term for term in terms if term.lower() not in ["and", "or", "not", "near", "onear"]]
        
        # Generate random number of results (5-15)
        import random
        num_results = random.randint(5, 15)
        
        results = []
        sources = ["Twitter", "Facebook", "News", "Blogs"]
        sentiments = ["positive", "negative", "neutral"]
        
        for i in range(num_results):
            # Generate a random timestamp in the last 6 months
            from datetime import datetime, timedelta
            days_ago = random.randint(1, 180)
            timestamp = datetime.now() - timedelta(days=days_ago)
            
            # Generate a random piece of content using the terms
            random_terms = random.sample(terms, min(3, len(terms)))
            adjectives = ["great", "terrible", "amazing", "disappointing", "innovative", "outdated"]
            random_adj = random.choice(adjectives)
            content = f"I think the {random_terms[0]} is {random_adj}. "
            
            if len(random_terms) > 1:
                content += f"The {random_terms[1]} feature is impressive. "
            
            if len(random_terms) > 2:
                content += f"But I'm not sure about the {random_terms[2]}."
            
            # Create a search result
            result = SearchResult(
                id=f"simulated-{i}-{uuid4()}",
                content=content,
                source=random.choice(sources),
                timestamp=timestamp,
                metadata={
                    "sentiment": random.choice(sentiments),
                    "likes": random.randint(0, 1000),
                    "shares": random.randint(0, 500),
                    "author": f"user{random.randint(1000, 9999)}"
                }
            )
            
            results.append(result.dict())
        
        return results
    
    async def _extract_themes(
        self, 
        search_results: List[Dict[str, Any]], 
        user_requirements: Dict[str, Any]
    ) -> List[Theme]:
        """
        Extract themes from search results using TF-IDF and LLM analysis.
        
        Args:
            search_results: List of search results.
            user_requirements: User requirements for context.
            
        Returns:
            List of extracted themes.
        """
        # Extract content from search results
        documents = [result["content"] for result in search_results]
        
        # Apply TF-IDF for keyword extraction
        themes_from_tfidf = await self._extract_themes_tfidf(documents)
        
        # Apply LLM for semantic theme extraction
        themes_from_llm = await self._extract_themes_llm(search_results, user_requirements)
        
        # Combine and deduplicate themes
        all_themes = themes_from_tfidf + themes_from_llm
        
        # Deduplicate themes based on similarity of names and keywords
        deduplicated_themes = self._deduplicate_themes(all_themes)
        
        # Sort themes by relevance score
        sorted_themes = sorted(deduplicated_themes, key=lambda x: x.relevance_score, reverse=True)
        
        # Take top 10 themes
        return sorted_themes[:10]
    
    async def _extract_themes_tfidf(self, documents: List[str]) -> List[Theme]:
        """
        Extract themes using a custom TF-IDF implementation.
        
        Args:
            documents: List of document texts.
            
        Returns:
            List of themes extracted using TF-IDF.
        """
        if not documents:
            return []
        
        try:
            # Custom TF-IDF implementation
            # Tokenize documents
            import re
            import string
            from collections import Counter, defaultdict
            
            # Define English stop words
            stop_words = {
                "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
                "which", "this", "that", "these", "those", "then", "just", "so", "than",
                "such", "when", "while", "where", "why", "how", "all", "any", "both",
                "each", "few", "more", "most", "other", "some", "such", "no", "nor", 
                "not", "only", "own", "same", "too", "very", "s", "t", "can", "will",
                "don", "don't", "should", "now", "i", "me", "my", "myself", "we", "our", 
                "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves",
                "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", 
                "its", "itself", "they", "them", "their", "theirs", "themselves", "am",
                "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", 
                "having", "do", "does", "did", "doing", "would", "could", "should"
            }
            
            # Tokenize function for documents
            def tokenize(text):
                # Convert to lowercase and remove punctuation
                text = text.lower()
                text = re.sub(f'[{re.escape(string.punctuation)}]', ' ', text)
                
                # Split into words
                words = text.split()
                
                # Remove stop words
                words = [word for word in words if word not in stop_words and len(word) > 2]
                
                # Generate unigrams and bigrams
                tokens = words.copy()  # Add unigrams
                
                # Add bigrams
                for i in range(len(words) - 1):
                    tokens.append(f"{words[i]} {words[i+1]}")
                
                return tokens
            
            # Tokenize all documents
            tokenized_docs = [tokenize(doc) for doc in documents]
            
            # Calculate document frequencies
            doc_freq = defaultdict(int)
            for doc_tokens in tokenized_docs:
                # Count each token only once per document
                for token in set(doc_tokens):
                    doc_freq[token] += 1
            
            # Filter tokens by document frequency
            max_df = 0.7 * len(documents)  # Ignore terms in more than 70% of docs
            min_df = 2  # Ignore terms in fewer than 2 docs
            
            valid_tokens = {token for token, freq in doc_freq.items() 
                           if min_df <= freq <= max_df}
            
            # Calculate TF-IDF for each token in each document
            tfidf_scores = defaultdict(float)
            
            for doc_tokens in tokenized_docs:
                # Count token frequencies in this document
                token_freq = Counter(doc_tokens)
                
                # Calculate TF-IDF for each valid token
                for token in valid_tokens:
                    if token in token_freq:
                        # Term frequency in this document
                        tf = token_freq[token] / len(doc_tokens)
                        
                        # Inverse document frequency
                        idf = math.log(len(documents) / doc_freq[token])
                        
                        # Add to the token's total TF-IDF score
                        tfidf_scores[token] += tf * idf
            
            # Get top tokens by TF-IDF score
            top_terms = sorted([(token, score) for token, score in tfidf_scores.items()],
                              key=lambda x: x[1], reverse=True)[:20]  # Top 20 terms
            
            # Group related terms into themes
            themes = []
            used_terms = set()
            
            for term, score in top_terms:
                if term in used_terms:
                    continue
                
                # Find related terms based on co-occurrence
                related_terms = [term]
                for other_term, other_score in top_terms:
                    if other_term != term and other_term not in used_terms:
                        # Check co-occurrence in documents
                        term_docs = set([i for i, doc in enumerate(documents) if term in doc.lower()])
                        other_docs = set([i for i, doc in enumerate(documents) if other_term in doc.lower()])
                        
                        # If terms co-occur in at least 50% of documents, consider them related
                        if len(term_docs.intersection(other_docs)) >= 0.5 * min(len(term_docs), len(other_docs)):
                            related_terms.append(other_term)
                            used_terms.add(other_term)
                
                used_terms.add(term)
                
                # Create a theme
                theme_name = term.title() if len(related_terms) == 1 else f"{term.title()} & Related"
                
                # Calculate relevance score (average TF-IDF score of related terms)
                relevance_score = sum([score for t, score in top_terms if t in related_terms]) / len(related_terms)
                
                # Calculate frequency (number of documents containing any related term)
                docs_with_terms = set()
                for t in related_terms:
                    docs_with_terms.update([i for i, doc in enumerate(documents) if t in doc.lower()])
                frequency = len(docs_with_terms)
                
                # Get sample posts
                sample_indices = list(docs_with_terms)[:3]  # Take up to 3 samples
                sample_posts = [documents[i] for i in sample_indices]
                
                theme = Theme(
                    id=uuid4(),
                    name=theme_name,
                    keywords=related_terms,
                    relevance_score=float(relevance_score),
                    frequency=frequency,
                    sample_posts=sample_posts,
                    metadata={"extraction_method": "tfidf"}
                )
                
                themes.append(theme)
            
            return themes
            
        except Exception as e:
            logger.error(f"Error in TF-IDF theme extraction: {e}")
            return []
    
    async def _extract_themes_llm(
        self, 
        search_results: List[Dict[str, Any]], 
        user_requirements: Dict[str, Any]
    ) -> List[Theme]:
        """
        Extract themes using LLM analysis.
        
        Args:
            search_results: List of search results.
            user_requirements: User requirements for context.
            
        Returns:
            List of themes extracted using LLM.
        """
        # Limit the number of results to process to avoid token limits
        max_results = 50
        limited_results = search_results[:max_results]
        
        # Construct prompt for theme extraction
        prompt_template = """
        Analyze the following social media posts and extract the main themes:
        
        USER REQUIREMENTS:
        Products: {products}
        Goals: {goals}
        Focus Areas: {focus_areas}
        
        POSTS:
        {posts}
        
        Extract 5-10 key themes from these posts. For each theme:
        1. Provide a clear, concise name
        2. List 3-5 keywords associated with the theme
        3. Rate its relevance to the user's goals (0.0 to 1.0)
        4. Indicate how frequently it appears (number of posts)
        5. Provide 1-3 example posts that represent this theme
        
        Return your analysis as a JSON array with objects containing:
        - name: Theme name
        - keywords: Array of keywords
        - relevance_score: Number between 0.0 and 1.0
        - frequency: Integer representing frequency
        - sample_posts: Array of example posts (up to 3)
        """
        
        # Format posts for prompt
        posts_text = ""
        for i, result in enumerate(limited_results):
            posts_text += f"{i+1}. [{result['source']}] {result['content']}\n\n"
        
        # Format prompt with user requirements
        products = ", ".join(user_requirements.get("products", []))
        goals = ", ".join(user_requirements.get("goals", []))
        focus_areas = ", ".join(user_requirements.get("focus_areas", [])) if user_requirements.get("focus_areas") else "N/A"
        
        prompt = prompt_template.format(
            products=products,
            goals=goals,
            focus_areas=focus_areas,
            posts=posts_text
        )
        
        # Create messages for the LLM
        messages = [
            SystemMessage(content=DATA_PROC_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        # Generate themes
        response = await self.llm.ainvoke(messages)
        
        try:
            # Parse the JSON response
            # Extract JSON from response if needed
            content = response.content
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                # Try to find JSON array between square brackets
                json_match = re.search(r'(\[.*\])', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            
            themes_data = json.loads(content)
            
            # Convert to Theme objects
            themes = []
            for theme_data in themes_data:
                theme = Theme(
                    id=uuid4(),
                    name=theme_data["name"],
                    keywords=theme_data["keywords"],
                    relevance_score=float(theme_data["relevance_score"]),
                    frequency=int(theme_data["frequency"]),
                    sample_posts=theme_data["sample_posts"][:3],
                    metadata={"extraction_method": "llm"}
                )
                themes.append(theme)
            
            return themes
            
        except Exception as e:
            logger.error(f"Error parsing LLM theme extraction response: {e}")
            return []
    
    def _deduplicate_themes(self, themes: List[Theme]) -> List[Theme]:
        """
        Deduplicate themes based on similarity of names and keywords.
        
        Args:
            themes: List of themes to deduplicate.
            
        Returns:
            Deduplicated list of themes.
        """
        if not themes:
            return []
        
        # Sort themes by relevance score
        sorted_themes = sorted(themes, key=lambda x: x.relevance_score, reverse=True)
        
        # Deduplicate based on similarity
        deduplicated = []
        used_indices = set()
        
        for i, theme in enumerate(sorted_themes):
            if i in used_indices:
                continue
            
            # Find similar themes
            similar_indices = []
            for j, other_theme in enumerate(sorted_themes):
                if j == i or j in used_indices:
                    continue
                
                # Check name similarity
                name_similarity = self._calculate_text_similarity(theme.name.lower(), other_theme.name.lower())
                
                # Check keyword similarity
                keyword_similarity = self._calculate_list_similarity(
                    [k.lower() for k in theme.keywords],
                    [k.lower() for k in other_theme.keywords]
                )
                
                # If either similarity is high, consider them duplicates
                if name_similarity > 0.7 or keyword_similarity > 0.5:
                    similar_indices.append(j)
            
            # Merge similar themes
            if similar_indices:
                merged_theme = self._merge_themes([theme] + [sorted_themes[j] for j in similar_indices])
                deduplicated.append(merged_theme)
                used_indices.update(similar_indices)
                used_indices.add(i)
            else:
                deduplicated.append(theme)
                used_indices.add(i)
        
        return deduplicated
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.
        
        Args:
            text1: First text string.
            text2: Second text string.
            
        Returns:
            Similarity score between 0.0 and 1.0.
        """
        # Simple Jaccard similarity for words
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_list_similarity(self, list1: List[str], list2: List[str]) -> float:
        """
        Calculate similarity between two lists of strings.
        
        Args:
            list1: First list of strings.
            list2: Second list of strings.
            
        Returns:
            Similarity score between 0.0 and 1.0.
        """
        # Jaccard similarity for lists
        set1 = set(list1)
        set2 = set(list2)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _merge_themes(self, themes: List[Theme]) -> Theme:
        """
        Merge similar themes into a single theme.
        
        Args:
            themes: List of themes to merge.
            
        Returns:
            Merged theme.
        """
        # Use the name of the theme with highest relevance score
        primary_theme = max(themes, key=lambda x: x.relevance_score)
        
        # Merge keywords
        all_keywords = []
        for theme in themes:
            all_keywords.extend(theme.keywords)
        
        # Count keyword frequencies
        keyword_counts = Counter(all_keywords)
        
        # Take top 10 keywords
        merged_keywords = [k for k, _ in keyword_counts.most_common(10)]
        
        # Merge sample posts
        all_samples = []
        for theme in themes:
            all_samples.extend(theme.sample_posts)
        
        # Remove duplicates and take top 3
        unique_samples = list(dict.fromkeys(all_samples))[:3]
        
        # Calculate average relevance score
        avg_relevance = sum(theme.relevance_score for theme in themes) / len(themes)
        
        # Sum frequencies
        total_frequency = sum(theme.frequency for theme in themes)
        
        return Theme(
            id=uuid4(),
            name=primary_theme.name,
            keywords=merged_keywords,
            relevance_score=avg_relevance,
            frequency=total_frequency,
            sample_posts=unique_samples,
            metadata={"extraction_method": "merged", "merged_from": len(themes)}
        )
