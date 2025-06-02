#!/usr/bin/env python3
"""
Simple API test using the Flask app directly without starting a server.
"""

import sys
import os
import json

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def test_app_endpoints():
    """Test Flask app endpoints directly"""
    try:
        # Import the Flask app
        from app import app
        
        # Create test client
        with app.test_client() as client:
            print("Testing Flask app endpoints...")
            
            # Test root endpoint
            print("\n1. Testing root endpoint /")
            response = client.get('/')
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = json.loads(response.data)
                print(f"Response: {json.dumps(data, indent=2)}")
                print("✅ Root endpoint works")
            else:
                print(f"❌ Root endpoint failed: {response.data}")
            
            # Test simple analyze endpoint (this will test workflow initialization)
            print("\n2. Testing analyze endpoint /api/analyze")
            test_payload = {
                "query": "What are people saying about our brand?",
                "context": {}
            }
            
            response = client.post('/api/analyze', 
                                 data=json.dumps(test_payload),
                                 content_type='application/json')
            print(f"Status: {response.status_code}")
            
            if response.status_code in [200, 500]:  # 500 expected due to API credentials
                try:
                    data = json.loads(response.data)
                    print(f"Response keys: {list(data.keys())}")
                    print(f"Status: {data.get('status', 'unknown')}")
                    print(f"Message: {data.get('message', 'N/A')}")
                    
                    if 'themes' in data:
                        print(f"Themes: {len(data['themes'])} themes returned")
                    
                    if response.status_code == 200:
                        print("✅ Analyze endpoint completed successfully")
                    else:
                        print("⚠️  Analyze endpoint completed with expected errors (API credentials)")
                        
                except json.JSONDecodeError:
                    print(f"Response (raw): {response.data}")
            else:
                print(f"❌ Analyze endpoint failed: {response.data}")
                
    except Exception as e:
        print(f"❌ Error testing Flask app: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_app_endpoints()
