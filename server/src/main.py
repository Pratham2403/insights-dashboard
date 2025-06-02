"""
This Sets Up the Main Application Entry Point.

Intializes the Application, Does the Basic Data Injection and Compilation of the Application.
And then Starts the Application

Used when running the Backend in Terminal and Chatting on the Terminal.
"""

import sys
import os
import importlib.util
import logging
import asyncio

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("src/main.py executed directly, but CLI functionality has been removed. "
                "To run the web server, use 'python run.py --web' or execute 'app.py'.")