#!/usr/bin/env python3
"""
FastAPI Server Startup Script
Provides development and production startup options for the Sprinklr Insights Dashboard API
"""
import os
import sys
import logging
import uvicorn


def main():
    """Main startup function"""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Get configuration from environment
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    reload = os.getenv('AUTO_RELOAD', 'True').lower() == 'true'
    
    logger.info("🚀 Starting Sprinklr Insights Dashboard API with FastAPI")
    logger.info(f"🌐 Server: http://{host}:{port}")
    logger.info(f"📚 API Docs: http://{host}:{port}/docs")
    logger.info(f"🔧 Debug mode: {debug}")
    logger.info(f"🔄 Auto-reload: {reload}")
    
    try:
        uvicorn.run(
            "app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info" if not debug else "debug",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested")
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
