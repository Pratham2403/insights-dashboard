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
from src.utils.files_helper import import_module_from_file

# Get path to config directory
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, '..', 'config')
settings_module = import_module_from_file(os.path.join(config_path, 'settings.py'), 'settings')
settings = settings_module.settings

logger = logging.getLogger(__name__)

@tool("Get Sprinklr Data")
async def get_sprinklr_data(
    query: str, 
    limit: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch data from Sprinklr API based on a query and optional filters.

        Args:
            query: The boolean_keyword_query for the Sprinklr API.
            limit: The page_size for the request. If 0 or not provided, defaults to 10.

        Returns:
            A list of hits from the Sprinklr API response, or an empty list if an error occurs.
        """
        
        # API URL from api-communication.md
        api_url = "https://space-p0-lst-poc.sprinklr.com/ui/rest/chatgpt/stream/get-mentions/9004/MESSAGE_STREAM_SUMMARIZATION_STREAM"
        numberOfMessages = limit if limit > 0 else 500  # Default to 10 as per api-communication.md
        
        # Generate unique request ID and key
        request_key = "25fac0b8-b533-4959-9434-c8d230eb539d"
        logger.info(f"DEBUG: Baggage : {settings.SPRINKLR_BAGGAGE}")
        # Hardcoded headers as per api-communication.md - DO NOT CHANGE
        headers = {
            'accept': 'text/event-stream',
            'accept-language': 'en-US,en;q=0.9',
            'baggage': settings.SPRINKLR_BAGGAGE,
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://space-p0-lst-poc.sprinklr.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://space-p0-lst-poc.sprinklr.com/research/insights/listening/dashboard/6837f747ace369431e594a71/tab/17?DATE_RANGE_CONFIG=%7B%22dateRange%22%3A%7B%22option%22%3A%22LAST_30_DAYS%22%7D%2C%22timezone%22%3A%22Asia%2FKolkata%22%2C%22previousDateRange%22%3A%7B%22option%22%3A%22PREVIOUS_PERIOD_OPTION%22%7D%7D',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sentry-trace': settings.SPRINKLR_SENTRY_TRACE,
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'x-csrf-token': settings.SPRINKLR_X_CSRF_TOKEN,
            'x-request-id': settings.SPRINKLR_X_REQUEST_ID,
            'x-user-context': settings.SPRINKLR_X_USER_CONTEXT
        }

        request_body = {
            "filters": [
                {
                    "field": "QUERY",
                    "values": [
                        query
                    ]
                }
            ],
            "report": "SPRINKSIGHTS",
            "reportingEngine": "LISTENING",
            "fromTime": 1746988200000,
            "uptoTime": 1749580199999,
            "applyAccessibilityFilters": True,
            "key": request_key,
            "timezone": "Asia/Kolkata",
            "tzOffset": -19800000,
            "generateDescriptiveSummary": False,
            "numberOfMessages": numberOfMessages,
            "bucketMessageCount": f"{int(numberOfMessages / 10)}",
        }

        # Parse cookies from settings
        cookies = {}
        if settings.SPRINKLR_COOKIES:
            # Parse cookie string format
            for cookie in settings.SPRINKLR_COOKIES.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value

        logger.info(f"Fetching Sprinklr data for query: {query} and with numberOfMessages: {numberOfMessages}")

        async with httpx.AsyncClient(timeout=90, cookies=cookies) as client:
            for attempt in range(3):
                try:
                    response = await client.post(api_url, json=request_body, headers=headers)
                    response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

                    # Parse JSON response
                    response_data = response.json()
                    
                    # The response is an array of objects as per api-communication.md
                    hits = response_data if isinstance(response_data, list) else []

                    logger.info(f"Successfully fetched {len(hits)} hits from Sprinklr API.")
                    return hits

                except httpx.HTTPStatusError as e:
                    logger.error(f"Sprinklr API request failed with status {e.response.status_code}: {e.response.text}") # Log snippet of error
                    if attempt == 2:  # max_retries - 1
                        return [] # Return empty list after max retries
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                except httpx.RequestError as e:
                    logger.error(f"Sprinklr API request error: {e}")
                    if attempt == 2:  # max_retries - 1
                        return []
                    await asyncio.sleep(2 ** attempt)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding Sprinklr API JSON response: {e}. Response text: {response.text}")
                    return [] # Cannot parse response
                except Exception as e:
                    logger.error(f"An unexpected error occurred while fetching Sprinklr data: {e}")
                    return []
        return [] # Should not be reached if retries are handled correctly


class GetTools:
    """
    Collection of tools for fetching data from various sources including Sprinklr API.
    
    This class provides methods to fetch social media data, mentions, and other
    relevant information for analysis and theme generation.
    """
    
    def __init__(self):
        """Initialize the GetTools with configuration"""
        
        # Reference to the standalone tool function
        self.get_sprinklr_data = get_sprinklr_data
        
        logger.info("GetTools initialized")


# Create global instance for tool usage
get_tools_instance = GetTools()


