#!/usr/bin/env python3
"""
Diagnostic test to identify where the workflow is getting stuck
"""

import asyncio
import logging
import sys
import os
import json
import time
from datetime import datetime

# Add the src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_step_by_step():
    """Test each step individually to identify issues"""
    try:
        logger.info("🔍 Starting Step-by-Step Diagnostic Test")
        
        # Test 1: Import check
        logger.info("1️⃣ Testing imports...")
        try:
            from complete_modern_workflow import ModernSprinklrWorkflow
            logger.info("✅ Imports successful")
        except Exception as e:
            logger.error(f"❌ Import failed: {e}")
            return False
        
        # Test 2: Initialization
        logger.info("2️⃣ Testing workflow initialization...")
        try:
            start_time = time.time()
            workflow = ModernSprinklrWorkflow()
            init_time = time.time() - start_time
            logger.info(f"✅ Initialization successful ({init_time:.2f}s)")
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 3: Simple state creation
        logger.info("3️⃣ Testing state creation...")
        try:
            from helpers.modern_states import ModernDashboardState
            from langchain_core.messages import HumanMessage
            
            test_state = {
                "messages": [HumanMessage(content="test")],
                "conversation_id": "test",
                "user_query": "test query"
            }
            logger.info("✅ State creation successful")
        except Exception as e:
            logger.error(f"❌ State creation failed: {e}")
            return False
        
        # Test 4: Individual agent test
        logger.info("4️⃣ Testing individual agents...")
        try:
            # Test query refiner
            logger.info("   🔍 Testing Query Refiner...")
            result = await workflow.query_refiner({"user_query": "test Samsung query"})
            logger.info(f"   ✅ Query Refiner: {type(result)}")
            
            # Test data collector
            logger.info("   📊 Testing Data Collector...")
            result = await workflow.data_collector({
                "refined_query": "test Samsung query", 
                "query_context": {}
            })
            logger.info(f"   ✅ Data Collector: {type(result)}")
            
        except Exception as e:
            logger.error(f"❌ Agent test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 5: Workflow compilation
        logger.info("5️⃣ Testing workflow compilation...")
        try:
            compiled_workflow = workflow._build_workflow()
            logger.info("✅ Workflow compilation successful")
        except Exception as e:
            logger.error(f"❌ Workflow compilation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        logger.info("🎉 All diagnostic tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Diagnostic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_step_by_step())
    sys.exit(0 if success else 1)
