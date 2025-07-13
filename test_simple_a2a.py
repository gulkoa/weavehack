#!/usr/bin/env python
"""Simple test to check A2A connectivity"""

import requests
import json

def test_agent_health(port, name):
    """Test if agent is responding"""
    try:
        # Try a simple HTTP request first
        response = requests.get(f"http://localhost:{port}/health", timeout=5)
        print(f"{name} health check: {response.status_code}")
    except Exception as e:
        print(f"{name} health check failed: {e}")
    
    # Try the A2A endpoint
    try:
        headers = {"Content-Type": "application/json"}
        data = {
            "message": {
                "content": {
                    "type": "text", 
                    "text": "test"
                }
            }
        }
        response = requests.post(f"http://localhost:{port}/", json=data, headers=headers, timeout=5)
        print(f"{name} A2A endpoint: {response.status_code}")
        print(f"{name} Response: {response.text[:200]}...")
    except Exception as e:
        print(f"{name} A2A endpoint failed: {e}")

if __name__ == "__main__":
    print("Testing agent connectivity...")
    
    # Test document_extractor
    test_agent_health(10001, "Document Extractor")
    
    print("\n---\n")
    
    # Test root agent
    test_agent_health(10000, "Root Agent")