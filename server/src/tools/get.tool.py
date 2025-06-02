"""
This module Consists of the List of Functions to Fetch Data from Different APIs, Data Sources, or Databases.

"""

from typing import List, Dict, Any, Optional
from langchain.tools import tool
import logging
import httpx
import json
import asyncio # Added import for asyncio.sleep
import os
import sys
import importlib.util

# Assuming settings are available, e.g., from a config module
def import_module_from_file(filepath, module_name):
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Get path to config directory
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, '..', 'config')
settings_module = import_module_from_file(os.path.join(config_path, 'settings.py'), 'settings')
settings = settings_module.settings

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
        
        logger.info("GetTools initialized")
    
    @tool
    async def get_sprinklr_data(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch data from Sprinklr API based on a query and optional filters.

        Args:
            query: The boolean_keyword_query for the Sprinklr API.
            filters: Optional dictionary of filters (currently not implemented in the API call).
            limit: The page_size for the request. If 0 or not provided, uses SPRINKLR_PAGE_SIZE from settings.

        Returns:
            A list of hits from the Sprinklr API response, or an empty list if an error occurs.
        """
        # Use SPRINKLR_DATA_API_URL and SPRINKLR_PAGE_SIZE from settings
        api_url = settings.SPRINKLR_DATA_API_URL
        page_size = limit if limit > 0 else 5 # Default to 5 as per api-communication.md

        # Headers from api-communication.md
        headers = {
            'accept': 'application/json; charset=utf-8',
            'accept-language': 'en-GB,en;q=0.8',
            'content-type': 'application/json',
        }

        # Request body structure from api-communication.md
        request_body = {
            "boolean_keyword_query": query,
            "page_size": page_size
        }

        # Add cookies from settings if available
        cookies = settings.SPRINKLR_COOKIES

        logger.info(f"Fetching Sprinklr data for query: {query[:50]}... with page_size: {page_size}")

        async with httpx.AsyncClient(timeout=self.api_timeout, cookies=cookies) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(api_url, json=request_body, headers=headers)
                    response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
                    
                    response_data = response.json()

                    # Extracting data as per api-communication.md: "count, hits in the response"
                    hits = response_data.get("hits", []) # Default to empty list if "hits" key is not found
                    count = response_data.get("count", 0) # Get count if available

                    logger.info(f"Successfully fetched {len(hits)} hits (total count: {count}) from Sprinklr API.")
                    return hits if isinstance(hits, list) else [] # Ensure a list is returned

                except httpx.HTTPStatusError as e:
                    logger.error(f"Sprinklr API request failed with status {e.response.status_code}: {e.response.text[:200]}") # Log snippet of error
                    if attempt == self.max_retries - 1:
                        return [] # Return empty list after max retries
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                except httpx.RequestError as e:
                    logger.error(f"Sprinklr API request error: {e}")
                    if attempt == self.max_retries - 1:
                        return []
                    await asyncio.sleep(2 ** attempt)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding Sprinklr API JSON response: {e}. Response text: {response.text[:200]}")
                    return [] # Cannot parse response
                except Exception as e:
                    logger.error(f"An unexpected error occurred while fetching Sprinklr data: {e}")
                    return []
        return [] # Should not be reached if retries are handled correctly

# Create global instance for tool usage
get_tools_instance = GetTools()


