"""
Initialization script for the Sprinklr Insights Dashboard application.
"""
import os
import sys
import logging
from pathlib import Path


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def initialize_app():
    """
    Initialize the application.
    
    Creates necessary directories and files.
    """
    logger.info("Initializing application...")
    
    # Add the current directory to the path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Create conversation memory directory
    from app.config.settings import settings
    
    memory_path = Path(settings.MEMORY_PATH)
    os.makedirs(memory_path, exist_ok=True)
    logger.info(f"Created memory directory: {memory_path}")
    
    logger.info("Initialization complete!")


if __name__ == "__main__":
    initialize_app()
