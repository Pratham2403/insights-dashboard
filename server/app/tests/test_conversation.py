"""
Test script for the Sprinklr Insights Dashboard application.
"""
import asyncio
import json
import sys
import os
from uuid import uuid4
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.workflows.insights_dashboard_workflow import process_message, create_or_load_conversation
from app.utils.state_manager import get_state_manager


async def test_conversation():
    """
    Test the conversation workflow.
    """
    print("Starting test conversation...")
    
    # Create a new conversation
    conversation_id = str(uuid4())
    state_manager = get_state_manager()
    
    # Define test messages
    test_messages = [
        "I am the owner of Samsung and I want to know about the Customer Insights about my products.",
        "Generate for Samsung s25 ultra, s25plus",
        "I want to know about the Twitter and Facebook channels.",
        "I want to increase Brand Awareness and Customer Satisfaction.",
        "I want to know about the last 6 months.",
        "Yes, I want to focus on customer feedback and sentiment analysis.",
        "Yes, I am sure."
    ]
    
    # Process each message
    for message in test_messages:
        print(f"\nUser: {message}")
        
        # Process the message
        result = await process_message(conversation_id, message)
        
        # Extract assistant response
        state = result["state"]
        messages = state.get("messages", [])
        
        if messages:
            # Filter for AI messages (properly handle both formats)
            assistant_messages = []
            for msg in messages:
                if isinstance(msg, AIMessage):
                    assistant_messages.append(msg)
                elif isinstance(msg, dict) and msg.get("role") == "assistant":
                    # Handle old format for compatibility
                    assistant_messages.append(msg)
            
            if assistant_messages:
                latest_response = assistant_messages[-1]
                if isinstance(latest_response, AIMessage):
                    print(f"Assistant: {latest_response.content}")
                else:
                    print(f"Assistant: {latest_response['content']}")
        
        # Print current state summary
        print("\nCurrent State:")
        print(f"- Step: {state.get('current_step', 'unknown')}")
        print(f"- User Requirements: {json.dumps(state.get('user_requirements', {}), indent=2)}")
        
        if state.get("query_batches"):
            print(f"- Query Batches: {len(state.get('query_batches', []))}")
        
        if state.get("themes"):
            print(f"- Themes: {len(state.get('themes', []))}")
            for theme in state.get("themes", [])[:3]:  # Show top 3 themes
                print(f"  - {theme['name']} (score: {theme['relevance_score']:.2f})")
    
    print("\nTest conversation completed!")


if __name__ == "__main__":
    asyncio.run(test_conversation())
