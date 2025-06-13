"""
Theme Generator Test Module.

This test script simulates the workflow execution for theme generation.
It follows the exact flow in the SprinklrWorkflow class for:
1. Tool execution (_tool_execution_node)
2. Data analysis (_data_analyzer_node)

The test takes in Boolean keyword query, keywords, filters, and refined query as input,
and outputs the generated themes.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('theme_generator_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("theme_generator_test")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components from src
from src.setup.llm_setup import LLMSetup
from src.tools.get_tool import get_sprinklr_data
from src.agents.data_analyzer_agent2 import DataAnalyzerAgent

class ThemeGeneratorTester:
    """Test harness for the theme generation flow in the Sprinklr workflow."""
    
    def __init__(self):
        """Initialize components for testing theme generation."""
        logger.info("Initializing ThemeGeneratorTester...")
        
        # Setup LLM
        llm_setup = LLMSetup()
        self.llm = llm_setup.get_agent_llm("workflow")
        
        # Initialize data analyzer
        self.data_analyzer = DataAnalyzerAgent(self.llm)
        
        # Initialize current hits storage (as in workflow)
        self._current_hits = []
        
        logger.info("Theme generator test components initialized")
    
    async def run_test(self, boolean_query: str, refined_query: str, keywords: List[str], filters: Dict[str, Any]):
        """
        Run the theme generation test pipeline.
        
        Args:
            boolean_query: The boolean keyword query for the Sprinklr API
            refined_query: The refined user query
            keywords: The list of extracted keywords
            filters: The filter configuration
        
        Returns:
            Generated themes
        """
        logger.info(f"Starting theme generation test")
        
        # Create test state (mimicking workflow state)
        state = {
            "refined_query": refined_query,
            "keywords": keywords,
            "filters": filters,
            "boolean_query": boolean_query
        }
        
        logger.info(f"Test state created with refined_query: '{refined_query}'")
        logger.info(f"Keywords: {keywords}")
        logger.info(f"Filters: {json.dumps(filters, default=str)}")
        
        # Step 1: Tool Execution Node - Fetch data from Sprinklr API
        logger.info("Step 1: Executing tool node to fetch data from Sprinklr API")
        try:
            # Use the tool exactly as in workflow
            hits = await get_sprinklr_data.ainvoke({"query": boolean_query, "limit": 100})
            
            # Store hits in workflow instance (NOT in state) as per workflow design
            self._current_hits = hits
            logger.info(f"Tool execution successful: Retrieved {len(hits)} hits from Sprinklr API")
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"error": f"Tool execution failed: {str(e)}"}
        
        # Step 2: Data Analyzer Node - Process hits and generate themes
        logger.info("Step 2: Running Data Analyzer Agent")
        try:
            # Get hits from workflow instance (NOT from state) to prevent memory explosion
            hits = getattr(self, '_current_hits', [])
            
            if not hits:
                logger.warning("No hits found in test instance - returning empty themes")
                return {"themes": []}
            
            logger.info(f"Processing {len(hits)} hits with Data Analyzer Agent...")
            
            # Call data analyzer with hits and state separately (exactly as in workflow)
            themes_result = await self.data_analyzer.analyze_hits_and_state(
                hits=hits,     # Hits passed separately (NOT stored in state)
                state=state    # LangGraph state passed separately
            )
            
            # Extract themes from result
            themes = themes_result.get("themes", [])
            
            # Clear hits from test instance to free memory
            if hasattr(self, '_current_hits'):
                delattr(self, '_current_hits')
            
            logger.info(f"Data analysis successful: Generated {len(themes)} themes")
            return {"themes": themes}
            
        except Exception as e:
            logger.error(f"Data analyzer failed: {e}")
            # Clear hits from test instance even on error
            if hasattr(self, '_current_hits'):
                delattr(self, '_current_hits')
            return {"error": f"Theme generation failed: {str(e)}"}

def get_user_input():
    """Get user input for the theme generator test."""
    print("\n" + "="*80)
    print("THEME GENERATOR TEST - Interactive Mode")
    print("="*80)
    
    # Get boolean query
    print("\nStep 1: Boolean Query")
    boolean_query = input("Enter your boolean keyword query: ").strip()
    if not boolean_query:
        print("No boolean query provided. Using default query.")
        boolean_query = '("product quality" OR "quality issues" OR defect OR malfunction) AND (complaint OR issue OR problem OR dissatisfied) AND (Twitter OR tweet)'
    
    # Get refined query
    print("\nStep 2: Refined Query")
    refined_query = input("Enter your refined query: ").strip()
    if not refined_query:
        print("No refined query provided. Using default query.")
        refined_query = "Analyze customer complaints about product quality on Twitter"
    
    # Get keywords
    print("\nStep 3: Keywords")
    keywords_input = input("Enter keywords (comma-separated): ").strip()
    if not keywords_input:
        print("No keywords provided. Using default keywords.")
        keywords = ["product quality", "complaint", "Twitter", "issue", "defect"]
    else:
        keywords = [kw.strip() for kw in keywords_input.split(",")]
    
    # Get filters
    print("\nStep 4: Filters")
    print("Enter filter information (press Enter to skip and use defaults):")
    
    time_period = input("Time period (e.g., 'last 30 days'): ").strip()
    if not time_period:
        time_period = "last 30 days"
    
    sources_input = input("Sources (comma-separated, e.g., 'Twitter,Facebook'): ").strip()
    if not sources_input:
        sources = ["Twitter"]
    else:
        sources = [src.strip() for src in sources_input.split(",")]
    
    sentiment = input("Sentiment filter (positive/negative/neutral): ").strip()
    if not sentiment:
        sentiment = "negative"
    
    filters = {
        "time_period": time_period,
        "sources": sources,
        "sentiment": sentiment
    }
    
    # Display inputs
    print(f"\n{'='*60}")
    print("INPUT SUMMARY:")
    print(f"{'='*60}")
    print(f"Boolean Query: {boolean_query}")
    print(f"Refined Query: {refined_query}")
    print(f"Keywords: {keywords}")
    print(f"Filters: {json.dumps(filters, indent=2)}")
    print(f"{'='*60}")
    
    return boolean_query, refined_query, keywords, filters

async def main():
    """Run the theme generator test."""
    tester = ThemeGeneratorTester()
    
    try:
        # Get user inputs
        boolean_query, refined_query, keywords, filters = get_user_input()
        
        print(f"\n{'='*80}")
        print("EXECUTING THEME GENERATION WORKFLOW")
        print(f"{'='*80}")
        
        # Run test with user inputs
        result = await tester.run_test(boolean_query, refined_query, keywords, filters)
        
        # Display results
        print(f"\n{'='*80}")
        print("FINAL RESULTS")
        print(f"{'='*80}")
        
        if "error" in result:
            print(f"❌ Test failed: {result['error']}")
            logger.error(f"Test failed: {result['error']}")
        else:
            themes = result.get("themes", [])
            print(f"✅ Successfully generated {len(themes)} themes:")
            
            for i, theme in enumerate(themes, 1):
                print(f"\n--- Theme {i} ---")
                print(f"Name: {theme.get('name', 'Unknown')}")
                print(f"Description: {theme.get('description', 'No description')}")
                if "boolean_query" in theme:
                    print(f"Boolean Query: {theme.get('boolean_query', 'No query')}")
                if "confidence_score" in theme:
                    print(f"Confidence Score: {theme.get('confidence_score', 0)}")
            
            # Log final output
            logger.info("FINAL OUTPUT:")
            logger.info(f"Generated {len(themes)} themes")
            for i, theme in enumerate(themes, 1):
                logger.info(f"Theme {i}: {theme.get('name', 'Unknown')} - {theme.get('description', 'No description')}")
        
        print(f"{'='*80}")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        logger.info("Test interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())