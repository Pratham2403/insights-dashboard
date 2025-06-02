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
        self.api_timeout = 60
        self.max_retries = 3
        
        logger.info("GetTools initialized")


@tool
async def get_sprinklr_data(
    query: str, 
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch data from Sprinklr API based on a query and optional filters.

        Args:
            query: The boolean_keyword_query for the Sprinklr API.
            filters: Optional dictionary of filters (currently not implemented in the API call).
            limit: The page_size for the request. If 0 or not provided, defaults to 5.

        Returns:
            A list of hits from the Sprinklr API response, or an empty list if an error occurs.
        """
        import uuid
        import time
        
        # API URL from api-communication.md
        api_url = "https://space-prod0.sprinklr.com/ui/rest/reports/query"
        page_size = limit if limit > 0 else 5  # Default to 5 as per api-communication.md
        
        # Generate unique request ID and key
        request_key = str(uuid.uuid4())
        request_id = f"v3-{uuid.uuid4()}"
        current_timestamp = int(time.time() * 1000)

        # Complete headers from api-communication.md
        headers = {
            'accept': 'application/json; charset=utf-8',
            'accept-language': 'en-GB,en;q=0.8',
            'baggage': 'sentry-environment=prod0,sentry-release=20.4.1-1f07f2b1ffb783e319e5ec41266d2ddd8edbac67,sentry-public_key=24769b1761314c0f814bde1a0576c6f6,sentry-trace_id=702acdd4d40f423b8f5481bc949fef2d',
            'content-type': 'application/json',
            'origin': 'https://space-prod0.sprinklr.com',
            'priority': 'u=1, i',
            'referer': 'https://space-prod0.sprinklr.com/research/insights/listening/dashboard/683982764a55c469871693aa/tab/0?DATE_RANGE_CONFIG=%7B%22dateRange%22%3A%7B%22option%22%3A%22LAST_30_DAYS%22%7D%2C%22timezone%22%3A%22Asia%2FKolkata%22%2C%22previousDateRange%22%3A%7B%22option%22%3A%22PREVIOUS_PERIOD_OPTION%22%7D%7D',
            'sec-ch-ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'sentry-trace': '702acdd4d40f423b8f5481bc949fef2d-8ef01a07c0b35741',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'x-csrf-token': settings.SPRINKLR_CSRF_TOKEN if hasattr(settings, 'SPRINKLR_CSRF_TOKEN') else 'SjFRazB6WE1DcUJ3aEZMM0Q5Qmpy',
            'x-engine': 'LISTENING',
            'x-request-id': request_id,
            'x-requested-at': str(current_timestamp),
            'x-requested-with': 'XMLHttpRequest',
            'x-user-context': settings.SPRINKLR_USER_CONTEXT if hasattr(settings, 'SPRINKLR_USER_CONTEXT') else 'c_9004_1000004509_1000462136'
        }

        # Complex request body structure from api-communication.md
        request_body = {
            "requests": {
                request_key: {
                    "key": request_key,
                    "reportingEngine": "LISTENING",
                    "filters": [
                        {
                            "field": "QUERY",
                            "values": [query]
                        }
                    ],
                    "report": "SPRINKSIGHTS",
                    "timezone": "Asia/Kolkata",
                    "sorts": [],
                    "page": {
                        "page": 0,
                        "size": page_size
                    },
                    "additional": {
                        "STREAM": "true",
                        "dashboardId": settings.SPRINKLR_DASHBOARD_ID if hasattr(settings, 'SPRINKLR_DASHBOARD_ID') else "683982764a55c469871693aa",
                        "widgetId": settings.SPRINKLR_WIDGET_ID if hasattr(settings, 'SPRINKLR_WIDGET_ID') else "683983294a55c4698716b7be",
                        "browserSessionId": str(uuid.uuid4()),
                        "engine": "LISTENING",
                        "moduleType": "LISTENING",
                        "exportInfo": False,
                        "option": "LAST_30_DAYS",
                        "chartType": "STREAM",
                        "dashboardWidget": True
                    }
                }
            }
        }

        # Parse cookies from settings or use default format
        cookies = {}
        if hasattr(settings, 'SPRINKLR_COOKIES') and settings.SPRINKLR_COOKIES:
            if isinstance(settings.SPRINKLR_COOKIES, dict):
                cookies = settings.SPRINKLR_COOKIES
            elif isinstance(settings.SPRINKLR_COOKIES, str):
                # Parse cookie string format
                for cookie in settings.SPRINKLR_COOKIES.split(';'):
                    if '=' in cookie:
                        key, value = cookie.strip().split('=', 1)
                        cookies[key] = value

        logger.info(f"Fetching Sprinklr data for query: {query[:50]}... with page_size: {page_size}")

        async with httpx.AsyncClient(timeout=60, cookies=cookies) as client:
            for attempt in range(3):
                try:
                    response = await client.post(api_url, json=request_body, headers=headers)
                    response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
                    
                    response_data = response.json()

                    # Extract data as per api-communication.md: responses.{key}.{count, hits}
                    responses = response_data.get("responses", {})
                    if request_key in responses:
                        result_data = responses[request_key]
                        hits = result_data.get("hits", [])
                        count = result_data.get("count", 0)
                        
                        logger.info(f"Successfully fetched {len(hits)} hits (total count: {count}) from Sprinklr API.")
                        return hits if isinstance(hits, list) else []
                    else:
                        logger.warning(f"Request key {request_key} not found in response")
                        return []

                except httpx.HTTPStatusError as e:
                    logger.error(f"Sprinklr API request failed with status {e.response.status_code}: {e.response.text[:200]}") # Log snippet of error
                    if attempt == 2:  # max_retries - 1
                        return [] # Return empty list after max retries
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                except httpx.RequestError as e:
                    logger.error(f"Sprinklr API request error: {e}")
                    if attempt == 2:  # max_retries - 1
                        return []
                    await asyncio.sleep(2 ** attempt)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding Sprinklr API JSON response: {e}. Response text: {response.text[:200]}")
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
        self.api_timeout = 60
        self.max_retries = 3
        
        # Reference to the standalone tool function
        self.get_sprinklr_data = get_sprinklr_data
        
        logger.info("GetTools initialized")


# Create global instance for tool usage
get_tools_instance = GetTools()


