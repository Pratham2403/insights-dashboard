"""
Main entry point for the Sprinklr Insights Dashboard application.
"""
import os
import sys
import uvicorn


def main():
    """
    Main entry point for the application.
    """
    # Add the current directory to the path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
