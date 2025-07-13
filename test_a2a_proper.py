#!/usr/bin/env python
"""Test A2A communication with proper message format"""

import requests
import json

def send_a2a_message(port, name, message_text):
    """Send a properly formatted A2A message"""
    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        # Proper A2A message format
        data = {
            "id": "test-123",
            "agent": {
                "name": "test-client",
                "version": "1.0.0"
            },
            "status": {
                "state": "awaiting_result"
            },
            "message": {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": message_text
                }
            }
        }
        
        print(f"\nSending to {name} on port {port}:")
        print(f"Message: '{message_text}'")
        
        response = requests.post(
            f"http://localhost:{port}/", 
            json=data, 
            headers=headers, 
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Extract the actual response text if available
            if "artifacts" in result and result["artifacts"]:
                for artifact in result["artifacts"]:
                    if "parts" in artifact:
                        for part in artifact["parts"]:
                            if part.get("type") == "text":
                                print(f"\nExtracted response text:\n{part.get('text', 'No text found')}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"{name} request failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing A2A communication with proper message format...")
    
    # Test document_extractor directly
    send_a2a_message(10001, "Document Extractor", "https://docs.pytest.org")
    
    print("\n" + "="*80 + "\n")
    
    # Test root agent
    send_a2a_message(10000, "Root Agent", "Extract documentation for https://docs.pytest.org")