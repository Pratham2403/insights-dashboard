"""
Boolean query generator tests.

This test script simulates the workflow execution for query generation.
It follows the exact flow in the SprinklrWorkflow class:
1. Query Refiner Agent
2. Data Collector Agent
3. HITL Verification
4. Query Generator Agent

The test outputs the final Boolean query.
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
        logging.FileHandler('query_generator_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("query_generator_test")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components from src
from src.setup.llm_setup import LLMSetup
from src.agents.query_refiner_agent import QueryRefinerAgent
from src.agents.data_collector_agent import DataCollectorAgent
from src.agents.query_generator_agent import QueryGeneratorAgent
from src.helpers.states import create_initial_state
from src.utils.hitl_detection import detect_approval_intent

class QueryGeneratorTester:
    """Test harness for the query generation flow in the Sprinklr workflow."""
    
    def __init__(self):
        """Initialize components for testing query generation."""
        logger.info("Initializing QueryGeneratorTester...")
        
        # Setup LLM
        llm_setup = LLMSetup()
        self.llm = llm_setup.get_agent_llm("workflow")
        
        # Initialize agents
        self.query_refiner = QueryRefinerAgent(self.llm)
        self.data_collector = DataCollectorAgent(self.llm)
        self.query_generator = QueryGeneratorAgent(self.llm)
        
        logger.info("Query generator test components initialized")
    
    async def run_test(self, user_query: str, simulated_user_response: str = "yes"):
        """
        Run the query generation test pipeline.
        
        Args:
            user_query: The initial user query
            simulated_user_response: The simulated user response during HITL verification
        
        Returns:
            Final state with boolean query
        """
        logger.info(f"Starting query generation test with query: '{user_query}'")
        
        # Create initial state
        state = create_initial_state(user_query)
        logger.info(f"Initial state created")
        
        # Step 1: Query Refiner
        logger.info("Step 1: Running Query Refiner Agent")
        refined_result = await self.query_refiner(state)
        refined_result = refined_result.get("query_refinement", {})
        state.update(refined_result)
        logger.info(f"Query refinement complete. Refined query: '{refined_result.get('refined_query', '')}'")
        
        # Step 2: Data Collector
        logger.info("Step 2: Running Data Collector Agent")
        collector_result = await self.data_collector(state)
        state.update(collector_result)
        logger.info(f"Data collection complete. Found {len(state.get('keywords', []))} keywords and {len(state.get('filters', {}))} filters")
        
        # Step 3: HITL Verification (simulated)
        logger.info(f"Step 3: Simulating HITL verification with response: '{simulated_user_response}'")
        
        # Analyze simulated response
        approval_analysis = detect_approval_intent(simulated_user_response)
        logger.info(f"HITL analysis result: {approval_analysis}")
        
        # Handle HITL iterations exactly as in workflow
        max_iterations = 3
        iteration = 0
        
        while not approval_analysis["is_approval"] and iteration < max_iterations:
            iteration += 1
            logger.info(f"HITL iteration {iteration}: User feedback received, updating query")
            
            # Update the query based on feedback (simplified for testing)
            state["query"] = [simulated_user_response]
            
            # Rerun Query Refiner
            logger.info(f"HITL iteration {iteration}: Rerunning Query Refiner")
            refined_result = await self.query_refiner(state)
            state.update(refined_result)
            
            # Rerun Data Collector
            logger.info(f"HITL iteration {iteration}: Rerunning Data Collector")
            collector_result = await self.data_collector(state)
            state.update(collector_result)
            
            # For testing, assume approval after first iteration
            approval_analysis = {"is_approval": True, "confidence": 0.9}
            logger.info(f"HITL iteration {iteration}: Assuming approval for test completion")
        
        # Step 4: Query Generator
        logger.info("Step 4: Running Query Generator Agent")
        generator_result = await self.query_generator(state)
        state.update(generator_result)
        
        boolean_query = state.get("boolean_query", "")
        logger.info(f"Query generation complete. Boolean query: '{boolean_query}'")
        
        return state

def get_user_input():
    """Get user input for the query generator test."""
    print("\n" + "="*80)
    print("QUERY GENERATOR TEST - Interactive Mode")
    print("="*80)
    
    # Get user query
    user_query = input("\nEnter your natural language query (or 'quit' to exit): ").strip()
    if user_query.lower() == 'quit':
        return user_query, ""
    
    if not user_query:
        print("No query provided. Using default query.")
        user_query = "Show me customer complaints about product quality on Twitter in the last month"
    
    print(f"\nUser Query: {user_query}")
    
    # Get HITL simulation preference
    print("\nHITL (Human-in-the-Loop) Verification Options:")
    print("1. Auto-approve (simulate 'yes')")
    print("2. Provide custom response")
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "2":
        hitl_response = input("\nEnter your HITL response (approval/feedback): ").strip()
        if not hitl_response:
            hitl_response = "yes"
    else:
        hitl_response = "yes"
    
    print(f"HITL Response: {hitl_response}")
    
    return user_query, hitl_response

async def main():
    """Run the query generator test in an infinite loop until user quits."""
    print("\n" + "="*80)
    print("QUERY GENERATOR TEST - Interactive Mode (Infinite Loop)")
    print("Type 'quit' or press Ctrl+C to exit the program")
    print("="*80)
    
    # Initialize components once
    tester = QueryGeneratorTester()
    logger.info("Test harness initialized and ready for infinite loop")
    
    # Run in infinite loop until user quits
    running = True
    while running:
        try:
            # Get user inputs
            user_query, hitl_response = get_user_input()
            
            # Check if user wants to quit
            if user_query.lower() == 'quit':
                print("\nExiting program as requested.")
                logger.info("User requested exit with 'quit' command")
                running = False
                break
            
            print(f"\n{'='*80}")
            print("EXECUTING QUERY GENERATION WORKFLOW")
            print(f"{'='*80}")
            
            # Run test with user inputs
            final_state = await tester.run_test(user_query, hitl_response)
            
            # Display results
            print(f"\n{'='*80}")
            print("FINAL RESULTS")
            print(f"{'='*80}")
            print(f"Initial Query: {user_query}")
            print(f"Refined Query: {final_state.get('refined_query', '')}")
            print(f"Industry: {final_state.get('industry', '')}")
            print(f"Sub-Vertical: {final_state.get('sub_vertical', '')}")
            print(f"Entities: {final_state.get('entities', [])}")
            print(f"Use Case: {final_state.get('use_case', 'General Use Case')}")
            print(f"Defaults: {final_state.get('defaults_applied', [])}")
            print(f"Keywords: {final_state.get('keywords', [])}")
            print(f"Filters: {json.dumps(final_state.get('filters', {}), indent=2)}")
            print(f"FINAL BOOLEAN QUERY: {final_state.get('boolean_query', '')}")
            print(f"{'='*80}")
            
            # Log final output
            logger.info("FINAL OUTPUT:")
            logger.info(f"Boolean Query: {final_state.get('boolean_query', '')}")
            
            print("\nReady for next query. Type 'quit' to exit.")
            
        except KeyboardInterrupt:
            print("\nTest interrupted by user.")
            logger.info("Test interrupted by user")
            running = False
            break
        except Exception as e:
            print(f"\nTest failed with error: {e}")
            logger.error(f"Test failed: {e}")
            print("You can try again with a different query or type 'quit' to exit.")

if __name__ == "__main__":
    asyncio.run(main())