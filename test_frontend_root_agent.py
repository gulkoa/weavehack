#!/usr/bin/env python3
"""Test script to verify frontend can communicate with root_agent"""

import requests
import json
import time

def test_root_agent_connection():
    """Test if root_agent is running and accepting A2A requests"""
    
    print("Testing Root Agent connection...")
    
    # Test A2A request
    a2a_request = {
        "message": {
            "content": {
                "text": "Generate an MCP server for the API at https://api.example.com"
            }
        }
    }
    
    try:
        # Send request to root agent
        response = requests.post(
            "http://localhost:10000/tasks",
            json=a2a_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            task_data = response.json()
            task_id = task_data.get("id")
            print(f"✅ Successfully created task: {task_id}")
            print(f"Initial status: {task_data.get('status', {}).get('state')}")
            
            # Poll for completion
            max_attempts = 30  # 60 seconds max
            for i in range(max_attempts):
                time.sleep(2)
                status_response = requests.get(f"http://localhost:10000/tasks/{task_id}")
                
                if status_response.status_code == 200:
                    task_result = status_response.json()
                    state = task_result.get("status", {}).get("state")
                    print(f"Task state: {state}")
                    
                    if state == "completed":
                        print("✅ Task completed successfully!")
                        artifacts = task_result.get("artifacts", [])
                        if artifacts:
                            print("\nResponse from Root Agent:")
                            print("-" * 50)
                            for artifact in artifacts:
                                parts = artifact.get("parts", [])
                                for part in parts:
                                    if part.get("type") == "text":
                                        print(part.get("text", ""))
                        break
                    elif state == "failed":
                        print("❌ Task failed!")
                        error_msg = task_result.get("status", {}).get("message", {}).get("content", {}).get("text", "Unknown error")
                        print(f"Error: {error_msg}")
                        break
                else:
                    print(f"❌ Failed to get task status: {status_response.status_code}")
                    break
            else:
                print("⏱️ Task timed out after 60 seconds")
        else:
            print(f"❌ Failed to create task: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Root Agent at http://localhost:10000")
        print("Please ensure the Root Agent is running with: python agents/root_agent/agent.py")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_root_agent_connection()