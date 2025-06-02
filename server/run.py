#!/usr/bin/env python3
"""
Sprinklr Listening Dashboard - Terminal Runner

This script provides an easy way to run and test the Sprinklr Listening Dashboard
from the terminal with various modes and options.

Usage:
    python run.py --web                        # Start web server
    python run.py --help                       # Show help (will be minimal)
"""

import argparse # Keep argparse for --web and --help
import sys
import os
import logging

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Import the Flask app instance directly for the web server mode
# This assumes app.py defines an `app` variable that is the Flask instance.
from app import app # Import the 'app' instance from app.py

def setup_logging(verbose: bool = False): # Verbose flag might not be used anymore
    """Setup logging configuration"""
    # level = logging.DEBUG if verbose else logging.INFO # Debug level might be removed
    level = logging.INFO # Default to INFO, remove verbose option for simplicity
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('sprinklr_dashboard_web.log') # Changed log file name
        ]
    )

logger = logging.getLogger(__name__) # Create a logger for this module

# Removed SprinklrDashboardRunner class and its methods (run_interactive_mode, run_single_query, etc.)
# as they are related to CLI/mock/test modes.

def run_web_server(host: str = "0.0.0.0", port: int = 8000):
    """Starts the Flask web server."""
    logger.info(f"Starting web server on http://{host}:{port}")
    try:
        # The Flask app is run from app.py's __main__ block if executed directly.
        # Here, we are providing an alternative way to start it via run.py --web.
        # This means app.py should ideally not auto-run its server if imported as a module.
        # A common pattern is to have app.run() inside `if __name__ == '__main__':` in app.py.
        # If app.py is structured that way, importing `app` here is safe.
        # We will use the app instance imported from app.py.
        app.run(host=host, port=port, debug=False) # debug=False for production-like behavior
    except Exception as e:
        logger.critical(f"Failed to start web server: {e}", exc_info=True)
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Sprinklr Listening Dashboard - Web Server Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python run.py --web         # Start the web server
        """
    )

    parser.add_argument(
        "--web",
        action="store_true",
        help="Start the web server."
    )
    # Removed other arguments like --query, --demo, --test, --status, --verbose
    # Keep --host and --port for web server configuration if needed, or rely on app.py's env vars.
    # For simplicity, let run_web_server use defaults or app.py's env var handling.

    args = parser.parse_args()

    # Setup logging (call it once)
    # verbose_logging = getattr(args, 'verbose', False) # verbose removed
    setup_logging() 

    if args.web:
        # Host and port can be fetched from .env or defaults within app.py or run_web_server
        # For now, let run_web_server handle its defaults or env vars from app.py
        run_web_server() # host/port will be handled by app.py or its defaults
    else:
        # If no arguments (or only --help which is handled by argparse), show help.
        logger.info("No specific mode selected. Showing help. Use --web to start the server.")
        parser.print_help()

if __name__ == "__main__":
    main()
