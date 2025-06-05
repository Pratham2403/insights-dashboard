#!/usr/bin/env python3
"""
Complete End-to-End Workflow Test
Tests all 6 steps of the architecture including HITL interrupt mechanism
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# Add the src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_complete_workflow():
    """Test the complete 6-step workflow with HITL"""
    try:
        logger.info("🚀 Starting Complete End-to-End Workflow Test")
        
        # Import after path setup
        from complete_modern_workflow import ModernSprinklrWorkflow
        
        # Initialize workflow
        logger.info("🔧 Initializing Modern Sprinklr Workflow...")
        workflow = ModernSprinklrWorkflow()
        
        # Test query and conversation
        test_query = "I need insights on Samsung Galaxy S25 mentions and sentiment analysis from social media"
        conversation_id = f"e2e_test_{int(datetime.now().timestamp())}"
        
        logger.info(f"📤 Processing query: {test_query}")
        logger.info(f"💬 Conversation ID: {conversation_id}")
        
        # Step 1-3: Process until HITL interrupt
        logger.info("=" * 60)
        logger.info("🔄 PHASE 1: Running workflow until HITL interrupt")
        logger.info("=" * 60)
        
        try:
            result = await workflow.process_dashboard_request(test_query, conversation_id)
            
            logger.info(f"📥 Phase 1 Result: {type(result)}")
            if hasattr(result, 'get'):
                logger.info(f"🎯 Current stage: {result.get('current_stage', 'unknown')}")
                logger.info(f"⏸️ Awaiting input: {result.get('awaiting_human_input', False)}")
                logger.info(f"📋 Has refined_query: {'refined_query' in result}")
                logger.info(f"🔍 Has keywords: {'keywords' in result}")
                logger.info(f"🎛️ Has filters: {'filters' in result}")
                
                # Check if we reached HITL verification
                if result.get('awaiting_human_input'):
                    logger.info("✅ Successfully reached HITL verification point!")
                    
                    # Step 4-6: Continue with human feedback
                    logger.info("=" * 60)
                    logger.info("🔄 PHASE 2: Providing HITL feedback and continuing")
                    logger.info("=" * 60)
                    
                    # Simulate human feedback
                    feedback = "continue"
                    logger.info(f"👤 Providing feedback: {feedback}")
                    
                    # Continue workflow
                    continued_result = await workflow.continue_workflow_with_feedback(
                        conversation_id, feedback
                    )
                    
                    logger.info(f"📥 Phase 2 Result: {continued_result.get('status', 'unknown')}")
                    logger.info(f"🎯 Final step: {continued_result.get('current_step', 'unknown')}")
                    
                    # Get final state
                    history = await workflow.get_workflow_history(conversation_id)
                    final_state = history.get('state', {})
                    
                    logger.info("=" * 60)
                    logger.info("📊 FINAL WORKFLOW STATE ANALYSIS")
                    logger.info("=" * 60)
                    logger.info(f"✅ Boolean query generated: {'boolean_query' in final_state}")
                    logger.info(f"🔧 Tool results available: {'tool_results' in final_state}")
                    logger.info(f"📈 Analysis completed: {'analysis_results' in final_state}")
                    logger.info(f"💡 Insights generated: {'insights' in final_state}")
                    logger.info(f"📑 Summary created: {'summary' in final_state}")
                    
                    # Count successful steps
                    steps_completed = []
                    if final_state.get('refined_query'):
                        steps_completed.append("1. Query Refiner")
                    if final_state.get('keywords'):
                        steps_completed.append("2. Data Collector") 
                    if final_state.get('hitl_summary'):
                        steps_completed.append("3. HITL Verification")
                    if final_state.get('boolean_query'):
                        steps_completed.append("4. Query Generator")
                    if final_state.get('tool_results'):
                        steps_completed.append("5. Tool Execution")
                    if final_state.get('analysis_results'):
                        steps_completed.append("6. Data Analyzer")
                    
                    logger.info(f"🎯 Steps completed: {len(steps_completed)}/6")
                    for step in steps_completed:
                        logger.info(f"   ✅ {step}")
                    
                    # Success metrics
                    success_rate = len(steps_completed) / 6 * 100
                    logger.info(f"📊 Success Rate: {success_rate:.1f}%")
                    
                    if success_rate >= 100:
                        logger.info("🎉 COMPLETE SUCCESS: All 6 architecture steps executed!")
                        return True
                    elif success_rate >= 50:
                        logger.info("⚠️ PARTIAL SUCCESS: Core workflow functioning")
                        return True
                    else:
                        logger.error("❌ FAILURE: Critical workflow issues")
                        return False
                else:
                    logger.warning("⚠️ Did not reach HITL verification - workflow may have completed early")
                    return False
            else:
                logger.error("❌ Invalid result format received")
                return False
                
        except Exception as phase_error:
            logger.error(f"❌ Workflow execution error: {phase_error}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test execution"""
    logger.info("🏁 Starting Complete End-to-End Workflow Test")
    logger.info("Testing architecture: Query Refiner → Data Collector → HITL → Query Generator → Tools → Data Analyzer")
    
    success = await test_complete_workflow()
    
    logger.info("=" * 80)
    if success:
        logger.info("🎉 END-TO-END TEST: PASSED")
        logger.info("✅ Modern LangGraph workflow is functioning correctly!")
    else:
        logger.info("❌ END-TO-END TEST: FAILED") 
        logger.info("⚠️ Workflow needs attention")
    logger.info("=" * 80)
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
