#!/usr/bin/env python3
"""
Quick test to verify the data flow fix between Query Refiner and Data Collector
"""

import asyncio
import logging
import sys
import os

# Add the src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_data_flow():
    """Test the basic data flow between agents"""
    try:
        logger.info("🚀 Testing data flow fix...")
        
        # Import after path setup
        from complete_modern_workflow import ModernSprinklrWorkflow
        
        # Initialize workflow
        logger.info("🔧 Initializing workflow...")
        workflow = ModernSprinklrWorkflow()
        
        # Test basic query processing
        test_query = "Show me Samsung Galaxy mentions"
        conversation_id = "test_flow_fix"
        
        logger.info(f"📤 Processing query: {test_query}")
        logger.info(f"💬 Conversation ID: {conversation_id}")
        
        # Process the request
        result = await workflow.process_dashboard_request(test_query, conversation_id)
        
        logger.info(f"📥 Result received: {type(result)}")
        if hasattr(result, 'get'):
            logger.info(f"📊 Messages count: {len(result.get('messages', []))}")
            logger.info(f"🔍 Has refined_query: {'refined_query' in result}")
            logger.info(f"📋 Has keywords: {'keywords' in result}")
            logger.info(f"🎯 Current stage: {result.get('current_stage', 'unknown')}")
        
        logger.info("✅ Basic flow test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_data_flow())
    sys.exit(0 if success else 1)
