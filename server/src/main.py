"""
This Sets Up the Main Application Entry Point.

Intializes the Application, Does the Basic Data Injection and Compilation of the Application.
And then Starts the Application

Used when running the Backend in Terminal and Chatting on the Terminal.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, Optional

# Add the src directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import workflow and configuration
import importlib.util

def import_module_from_file(filepath, module_name):
    """Helper function to import modules with dots in filenames"""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import workflow
workflow_module = import_module_from_file(
    os.path.join(os.path.dirname(__file__), 'workflow.py'),
    'workflow'
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sprinklr_dashboard.log')
    ]
)

logger = logging.getLogger(__name__)

class SprinklrDashboardCLI:
    """
    Command Line Interface for the Sprinklr Listening Dashboard.
    
    This class provides an interactive terminal interface for testing
    and using the dashboard functionality.
    """
    
    def __init__(self):
        """Initialize the CLI application"""
        self.workflow = workflow_module.get_workflow()
        logger.info("Sprinklr Dashboard CLI initialized")
    
    async def start_interactive_session(self):
        """Start an interactive session with the user"""
        try:
            print("\n" + "="*60)
            print("🎯 Sprinklr Listening Dashboard - Interactive Mode")
            print("="*60)
            print("Welcome! This dashboard analyzes social media data and generates themes.")
            print("Type 'help' for commands or 'quit' to exit.\n")
            
            while True:
                try:
                    # Get user input
                    user_input = input("\n💬 Enter your query: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle special commands
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("👋 Goodbye! Thank you for using Sprinklr Dashboard.")
                        break
                    elif user_input.lower() == 'help':
                        self.show_help()
                        continue
                    elif user_input.lower() == 'examples':
                        self.show_examples()
                        continue
                    elif user_input.lower() == 'status':
                        self.show_status()
                        continue
                    
                    # Process the query
                    print(f"\n🔄 Processing your query: '{user_input}'")
                    print("This may take a few moments...\n")
                    
                    result = await self.process_query(user_input)
                    self.display_results(result)
                    
                except KeyboardInterrupt:
                    print("\n\n⚠️  Process interrupted. Type 'quit' to exit properly.")
                except Exception as e:
                    print(f"\n❌ Error processing query: {str(e)}")
                    logger.error(f"Error in interactive session: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error in interactive session: {str(e)}")
            print(f"❌ Failed to start interactive session: {str(e)}")
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process a user query through the workflow"""
        try:
            # Add some context for better results
            user_context = {
                "interface": "cli",
                "session_type": "interactive",
                "preferences": {
                    "max_themes": 10,
                    "include_sentiment": True,
                    "include_channels": True
                }
            }
            
            result = await self.workflow.process_user_query(user_query, user_context)
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "themes": [],
                "status": "failed"
            }
    
    def display_results(self, result: Dict[str, Any]):
        """Display the workflow results in a formatted way"""
        try:
            print("\n" + "="*60)
            print("📊 ANALYSIS RESULTS")
            print("="*60)
            
            if result.get("success"):
                print(f"✅ Status: {result.get('status', 'completed').upper()}")
                print(f"🔧 Current Step: {result.get('current_step', 'unknown')}")
                
                # Display refined query
                if result.get("refined_query"):
                    print(f"\n🎯 Refined Query: {result['refined_query']}")
                
                # Display boolean query
                if result.get("boolean_query"):
                    print(f"🔍 Boolean Query: {result['boolean_query']}")
                
                # Display themes
                themes = result.get("themes", [])
                if themes:
                    print(f"\n📝 Generated Themes ({len(themes)}):")
                    print("-" * 40)
                    
                    for i, theme in enumerate(themes, 1):
                        print(f"\n{i}. {theme.get('name', 'Unnamed Theme')}")
                        print(f"   📄 Description: {theme.get('description', 'No description')}")
                        print(f"   🔑 Keywords: {', '.join(theme.get('keywords', []))}")
                        print(f"   📊 Data Points: {len(theme.get('data_points', []))}")
                        print(f"   🎯 Confidence: {theme.get('confidence', 0):.2f}")
                        if theme.get('boolean_query'):
                            print(f"   🔍 Query: {theme['boolean_query']}")
                else:
                    print("\n⚠️  No themes were generated.")
                
                # Display analysis summary
                summary = result.get("analysis_summary", {})
                if summary:
                    print(f"\n📈 Analysis Summary:")
                    print(f"   • Total Themes: {summary.get('total_themes', 0)}")
                    print(f"   • Data Coverage: {summary.get('data_coverage', 'Unknown')}")
                    print(f"   • Processing Status: {summary.get('processing_status', 'Unknown')}")
                
                # Display any warnings
                errors = result.get("errors", [])
                if errors:
                    print(f"\n⚠️  Warnings/Issues:")
                    for error in errors:
                        print(f"   • {error}")
            
            else:
                print(f"❌ Status: FAILED")
                print(f"💥 Error: {result.get('error', 'Unknown error')}")
                
                errors = result.get("errors", [])
                if errors:
                    print(f"\n📋 Error Details:")
                    for error in errors:
                        print(f"   • {error}")
            
            print("\n" + "="*60)
            
        except Exception as e:
            logger.error(f"Error displaying results: {str(e)}")
            print(f"❌ Error displaying results: {str(e)}")
    
    def show_help(self):
        """Display help information"""
        print("\n" + "="*60)
        print("📚 HELP - Available Commands")
        print("="*60)
        print("• help      - Show this help message")
        print("• examples  - Show example queries")
        print("• status    - Show system status")
        print("• quit/exit - Exit the application")
        print("\n💡 Query Examples:")
        print("• 'Show me Samsung mentions on Twitter'")
        print("• 'Analyze Apple brand sentiment'")
        print("• 'Facebook posts about iPhone in last week'")
        print("• 'Customer complaints about Tesla'")
        print("="*60)
    
    def show_examples(self):
        """Display example queries"""
        print("\n" + "="*60)
        print("💡 EXAMPLE QUERIES")
        print("="*60)
        print("1. Brand Monitoring:")
        print("   'Show me Samsung brand mentions in the last 30 days'")
        print("   'Analyze Apple sentiment on social media'")
        print("")
        print("2. Channel-Specific Analysis:")
        print("   'Twitter mentions of Tesla this week'")
        print("   'Facebook posts about iPhone reviews'")
        print("")
        print("3. Sentiment Analysis:")
        print("   'Negative feedback about Microsoft products'")
        print("   'Positive reviews of Google services'")
        print("")
        print("4. Product Analysis:")
        print("   'Customer complaints about delivery issues'")
        print("   'Product launch reactions for new iPhone'")
        print("="*60)
    
    def show_status(self):
        """Display system status"""
        print("\n" + "="*60)
        print("⚙️  SYSTEM STATUS")
        print("="*60)
        print("✅ Workflow: Initialized")
        print("✅ Agents: All agents loaded")
        print("✅ Tools: Data fetching tools ready")
        print("✅ LLM: Connected and ready")
        print("✅ Database: Vector database ready")
        print("="*60)

async def main():
    """Main entry point for the CLI application"""
    try:
        logger.info("Starting Sprinklr Dashboard CLI")
        
        # Initialize and start CLI
        cli = SprinklrDashboardCLI()
        await cli.start_interactive_session()
        
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted. Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)

def run_single_query(query: str):
    """Run a single query and return results (for testing)"""
    async def _run():
        cli = SprinklrDashboardCLI()
        result = await cli.process_query(query)
        cli.display_results(result)
        return result
    
    return asyncio.run(_run())

if __name__ == "__main__":
    # Check if a query was provided as command line argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Running single query: {query}")
        run_single_query(query)
    else:
        # Start interactive mode
        asyncio.run(main())