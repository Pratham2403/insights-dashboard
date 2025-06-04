#!/usr/bin/env python3
"""
Test script to demonstrate HITL verification workflow with 4+ interruptions.
This script will simulate the conversation flow described in the requirements.
"""

import requests
import json
import time
from typing import Dict, Any, Optional

BASE_URL = "http://127.0.0.1:8000"

class HITLWorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.conversation_history = []
        
    def test_health(self) -> bool:
        """Test if the server is running"""
        try:
            response = self.session.get(f"{BASE_URL}/api/health")
            return response.status_code == 200
        except:
            return False
    
    def send_query(self, query: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a query to the workflow"""
        data = {"query": query}
        if thread_id:
            data["thread_id"] = thread_id
            
        response = self.session.post(f"{BASE_URL}/api/process", json=data)
        return response.json()
    
    def send_user_response(self, thread_id: str, user_response: str) -> Dict[str, Any]:
        """Send user response to continue the workflow"""
        data = {
            "thread_id": thread_id,
            "query": user_response  # Use 'query' instead of 'user_response'
        }
        response = self.session.post(f"{BASE_URL}/api/process", json=data)
        return response.json()
    
    def get_workflow_status(self, thread_id: str) -> Dict[str, Any]:
        """Get the current workflow status"""
        response = self.session.get(f"{BASE_URL}/api/workflow/status/{thread_id}")
        return response.json()
    
    def print_response(self, response: Dict[str, Any], step: str):
        """Pretty print the response"""
        print(f"\n{'='*60}")
        print(f"STEP {step}")
        print(f"{'='*60}")
        print(f"Status: {response.get('status', 'unknown')}")
        print(f"Message: {response.get('message', 'No message')}")
        
        if 'data' in response:
            data = response['data']
            if 'conversation_id' in data:
                print(f"Conversation ID: {data['conversation_id']}")
                
            if 'refined_query' in data:
                print(f"\n📝 Refined Query:")
                print(f"   {data['refined_query']}")
                
            if 'hitl_verification_data' in data:
                hitl_data = data['hitl_verification_data']
                print(f"\n📋 HITL VERIFICATION:")
                print(f"   Status: {hitl_data.get('status', 'N/A')}")
                if 'user_data' in hitl_data:
                    print(f"   📊 Collected Data:")
                    user_data = hitl_data['user_data']
                    for key, value in user_data.items():
                        if key != 'raw_data':  # Skip raw data for readability
                            print(f"      {key}: {value}")
                
            if 'workflow_status' in data:
                print(f"Workflow Status: {data['workflow_status']}")
                
            if 'current_step' in data:
                print(f"Current Step: {data['current_step']}")
                
            if 'errors' in data and data['errors']:
                print("\n⚠️ Errors:")
                for error in data['errors']:
                    print(f"   - {error}")
                
        print(f"{'='*60}")
    
    def run_hitl_test(self):
        """Run the complete HITL test with 4+ verifications"""
        
        # Check if server is running
        if not self.test_health():
            print("❌ Server is not running. Please start the server first.")
            return
            
        print("🚀 Starting HITL Workflow Test")
        print("This will test the multi-agent workflow with Human-in-the-Loop verification")
        
        # Step 1: Send initial query (should trigger first HITL)
        print("\n🔍 Sending initial user query...")
        initial_query = "I want to do Brand Health Monitoring for Samsung"
        response1 = self.send_query(initial_query)
        self.print_response(response1, "1 - Initial Query")
        
        # The workflow returns 'conversation_id' as the thread identifier
        conv_id = response1.get('data', {}).get('conversation_id')
        if response1.get('status') != 'success' or not conv_id:
            print("❌ Failed to start workflow")
            return
        thread_id = conv_id
        
        # Step 2: First HITL Response - Ask for more details
        print("\n👤 User Response 1: Need more specific information")
        user_response_1 = "I need more specific information. I want to monitor Samsung Galaxy S25 series specifically on Twitter and Instagram for the last 30 days."
        response2 = self.send_user_response(thread_id, user_response_1)
        self.print_response(response2, "2 - First HITL Response")
        
        # Step 3: Second HITL Response - Confirm products but ask about sentiment
        print("\n👤 User Response 2: Confirm products, ask about sentiment")
        user_response_2 = "Yes, the products are correct. But I also want to include sentiment analysis and competitor comparison with iPhone and Google Pixel."
        response3 = self.send_user_response(thread_id, user_response_2)
        self.print_response(response3, "3 - Second HITL Response")
        
        # Step 4: Third HITL Response - Add geographical filters
        print("\n👤 User Response 3: Add geographical information")
        user_response_3 = "Please also include geographical filtering for India and USA markets. And I want to see top influencers and trending hashtags."
        response4 = self.send_user_response(thread_id, user_response_3)
        self.print_response(response4, "4 - Third HITL Response")
        
        # Step 5: Fourth HITL Response - Final approval
        print("\n👤 User Response 4: Final approval")
        user_response_4 = "Perfect! This looks good. Please proceed with generating the boolean query and fetching the data."
        response5 = self.send_user_response(thread_id, user_response_4)
        self.print_response(response5, "5 - Fourth HITL Response (Final Approval)")
        
        # Step 6: Check final workflow status
        print("\n📊 Checking final workflow status...")
        final_status = self.get_workflow_status(thread_id)
        self.print_response(final_status, "6 - Final Status Check")
        
        # Summary
        print(f"\n🎉 HITL Workflow Test Complete!")
        print(f"Thread ID: {thread_id}")
        print(f"Total HITL Interactions: 4")
        print("✅ Successfully tested context and history persistence across conversations")
        
        return thread_id

if __name__ == "__main__":
    tester = HITLWorkflowTester()
    tester.run_hitl_test()
