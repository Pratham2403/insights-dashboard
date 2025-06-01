
"""
This module Consists of the List of Functions to Fetch Data from Different APIs, Data Sources, or Databases.

"""

import logging
import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
from langchain.tools import tool

logger = logging.getLogger(__name__)

class GetTools:
    """
    Collection of tools for fetching data from various sources including Sprinklr API.
    
    This class provides methods to fetch social media data, mentions, and other
    relevant information for analysis and theme generation.
    """
    
    def __init__(self):
        """Initialize the GetTools with configuration"""
        self.api_timeout = 30
        self.max_retries = 3
        self.default_limit = 3000
        
        logger.info("GetTools initialized")
    
    @tool
    async def get_sprinklr_data(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 3000
    ) -> List[Dict[str, Any]]:
        """
        Fetch data from Sprinklr API using boolean keyword query.
        
        Args:
            query: Boolean keyword query string
            filters: Additional filters like date range, channels, etc.
            limit: Maximum number of results to fetch
            
        Returns:
            List of social media data objects
        """
        try:
            logger.info(f"Fetching Sprinklr data with query: {query[:100]}...")
            
            # For development, return mock data
            # In production, this would make actual API calls to Sprinklr
            mock_data = await self._generate_mock_sprinklr_data(query, filters, limit)
            
            logger.info(f"Successfully fetched {len(mock_data)} data points")
            return mock_data
            
        except Exception as e:
            logger.error(f"Error fetching Sprinklr data: {str(e)}")
            return []
    
    async def get_elastic_data(self, api: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch data from the provided API in the magnitude of 2000-3000 documents.

        Args:
            api: The API endpoint of some Elasticsearch database.
            query: A Boolean Keyword Query to filter and fetch the data.

        Returns:
            A list of documents matching the query.
        """
        try:
            logger.info(f"Fetching data from Elasticsearch API: {api}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.api_timeout)) as session:
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                
                # Prepare the Elasticsearch query
                es_query = {
                    "query": query,
                    "size": self.default_limit,
                    "sort": [{"timestamp": {"order": "desc"}}]
                }
                
                async with session.post(f"{api}/_search", json=es_query, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        documents = [hit["_source"] for hit in result.get("hits", {}).get("hits", [])]
                        logger.info(f"Successfully fetched {len(documents)} documents")
                        return documents
                    else:
                        logger.error(f"Elasticsearch API returned status {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching Elasticsearch data: {str(e)}")
            return []
    
    async def get_social_media_data(
        self, 
        platforms: List[str], 
        keywords: List[str],
        date_range: Dict[str, str],
        limit: int = 2000
    ) -> List[Dict[str, Any]]:
        """
        Fetch social media data from multiple platforms.
        
        Args:
            platforms: List of social media platforms (twitter, facebook, instagram, etc.)
            keywords: List of keywords to search for
            date_range: Dictionary with 'start' and 'end' date strings
            limit: Maximum number of results per platform
            
        Returns:
            Aggregated list of social media posts/mentions
        """
        try:
            logger.info(f"Fetching social media data from {len(platforms)} platforms")
            
            all_data = []
            
            for platform in platforms:
                platform_data = await self._fetch_platform_data(platform, keywords, date_range, limit)
                all_data.extend(platform_data)
            
            logger.info(f"Successfully fetched {len(all_data)} social media data points")
            return all_data
            
        except Exception as e:
            logger.error(f"Error fetching social media data: {str(e)}")
            return []
    
    async def get_brand_mentions(
        self, 
        brand_name: str,
        sentiment_filter: Optional[str] = None,
        channels: Optional[List[str]] = None,
        limit: int = 2500
    ) -> List[Dict[str, Any]]:
        """
        Fetch brand mentions across various channels.
        
        Args:
            brand_name: Name of the brand to search for
            sentiment_filter: Filter by sentiment (positive, negative, neutral)
            channels: List of channels to search in
            limit: Maximum number of mentions to fetch
            
        Returns:
            List of brand mention data
        """
        try:
            logger.info(f"Fetching brand mentions for: {brand_name}")
            
            # Build search query
            search_terms = [brand_name.lower()]
            filters = {
                "sentiment": sentiment_filter,
                "channels": channels or ["twitter", "facebook", "instagram", "linkedin"],
                "limit": limit
            }
            
            # For development, return mock data
            mentions = await self._generate_mock_brand_mentions(brand_name, filters)
            
            logger.info(f"Successfully fetched {len(mentions)} brand mentions")
            return mentions
            
        except Exception as e:
            logger.error(f"Error fetching brand mentions: {str(e)}")
            return []
    
    # Mock data generation methods for development
    async def _generate_mock_sprinklr_data(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 3000
    ) -> List[Dict[str, Any]]:
        """Generate mock Sprinklr data for development"""
        try:
            mock_data = []
            channels = ["twitter", "facebook", "instagram", "linkedin", "youtube"]
            sentiments = ["positive", "negative", "neutral"]
            
            # Extract keywords from query for content generation
            query_words = query.replace('"', '').replace('(', '').replace(')', '').replace('AND', '').replace('OR', '').split()
            query_words = [word.strip() for word in query_words if len(word) > 2]
            
            for i in range(min(limit, 3000)):
                # Generate content based on query words
                content_templates = [
                    f"Just tried the new {random.choice(query_words)} product - {self._get_sentiment_text(random.choice(sentiments))}!",
                    f"Has anyone used {random.choice(query_words)} recently? Looking for reviews.",
                    f"Great customer service from {random.choice(query_words)} team today!",
                    f"Not impressed with {random.choice(query_words)} latest update.",
                    f"Love the new features in {random.choice(query_words)}!"
                ]
                
                sentiment = random.choice(sentiments)
                channel = random.choice(channels)
                
                mock_item = {
                    "id": f"mock_{i+1}",
                    "content": random.choice(content_templates),
                    "channel": channel,
                    "date": self._generate_random_date(),
                    "author": f"user_{random.randint(1000, 9999)}",
                    "sentiment": sentiment,
                    "engagement": {
                        "likes": random.randint(0, 500),
                        "shares": random.randint(0, 100),
                        "comments": random.randint(0, 50)
                    },
                    "metadata": {
                        "language": "en",
                        "location": random.choice(["US", "UK", "CA", "AU", "IN"]),
                        "device": random.choice(["mobile", "desktop", "tablet"]),
                        "source_query": query
                    }
                }
                
                mock_data.append(mock_item)
            
            return mock_data
            
        except Exception as e:
            logger.error(f"Error generating mock Sprinklr data: {str(e)}")
            return []
    
    async def _fetch_platform_data(
        self, 
        platform: str, 
        keywords: List[str],
        date_range: Dict[str, str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch data from a specific platform"""
        try:
            # Mock implementation - in production, this would use platform-specific APIs
            await asyncio.sleep(0.1)  # Simulate API call delay
            
            platform_data = []
            for i in range(min(limit // len(keywords), 500)):
                item = {
                    "id": f"{platform}_{i+1}",
                    "content": f"Mock content about {random.choice(keywords)} on {platform}",
                    "platform": platform,
                    "date": self._generate_random_date(date_range),
                    "author": f"{platform}_user_{random.randint(100, 999)}",
                    "engagement": {
                        "likes": random.randint(0, 1000),
                        "shares": random.randint(0, 200)
                    }
                }
                platform_data.append(item)
            
            return platform_data
            
        except Exception as e:
            logger.error(f"Error fetching {platform} data: {str(e)}")
            return []
    
    async def _generate_mock_brand_mentions(
        self, 
        brand_name: str, 
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate mock brand mentions"""
        try:
            mentions = []
            channels = filters.get("channels", ["twitter", "facebook", "instagram"])
            sentiment_filter = filters.get("sentiment")
            limit = filters.get("limit", 2500)
            
            for i in range(min(limit, 2500)):
                sentiment = sentiment_filter if sentiment_filter else random.choice(["positive", "negative", "neutral"])
                channel = random.choice(channels)
                
                mention = {
                    "id": f"mention_{i+1}",
                    "content": f"Mention of {brand_name} - {self._get_brand_mention_text(brand_name, sentiment)}",
                    "channel": channel,
                    "date": self._generate_random_date(),
                    "author": f"user_{random.randint(1000, 9999)}",
                    "sentiment": sentiment,
                    "brand": brand_name,
                    "mention_type": random.choice(["direct", "indirect", "hashtag"]),
                    "reach": random.randint(100, 10000),
                    "engagement": {
                        "likes": random.randint(0, 500),
                        "shares": random.randint(0, 100),
                        "comments": random.randint(0, 50)
                    }
                }
                
                mentions.append(mention)
            
            return mentions
            
        except Exception as e:
            logger.error(f"Error generating mock brand mentions: {str(e)}")
            return []
    
    def _get_sentiment_text(self, sentiment: str) -> str:
        """Get appropriate text for sentiment"""
        sentiment_texts = {
            "positive": random.choice(["amazing", "great", "love it", "excellent", "fantastic"]),
            "negative": random.choice(["disappointing", "terrible", "not good", "hate it", "awful"]),
            "neutral": random.choice(["okay", "decent", "it's fine", "average", "not bad"])
        }
        return sentiment_texts.get(sentiment, "interesting")
    
    def _get_brand_mention_text(self, brand_name: str, sentiment: str) -> str:
        """Generate brand mention text based on sentiment"""
        if sentiment == "positive":
            templates = [
                f"Really happy with {brand_name} service!",
                f"{brand_name} exceeded my expectations",
                f"Recommend {brand_name} to everyone"
            ]
        elif sentiment == "negative":
            templates = [
                f"Had issues with {brand_name} support",
                f"{brand_name} needs to improve",
                f"Not satisfied with {brand_name}"
            ]
        else:
            templates = [
                f"Using {brand_name} for my project",
                f"Checking out {brand_name} products",
                f"{brand_name} has some interesting features"
            ]
        
        return random.choice(templates)
    
    def _generate_random_date(self, date_range: Optional[Dict[str, str]] = None) -> str:
        """Generate a random date within the specified range"""
        try:
            if date_range:
                start_date = datetime.fromisoformat(date_range.get("start", "2024-01-01"))
                end_date = datetime.fromisoformat(date_range.get("end", "2024-12-31"))
            else:
                # Default to last 30 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
            
            # Generate random date between start and end
            time_between = end_date - start_date
            random_seconds = random.randint(0, int(time_between.total_seconds()))
            random_date = start_date + timedelta(seconds=random_seconds)
            
            return random_date.isoformat()
            
        except Exception as e:
            logger.error(f"Error generating random date: {str(e)}")
            return datetime.now().isoformat()

# Create global instance for tool usage
get_tools_instance = GetTools()


