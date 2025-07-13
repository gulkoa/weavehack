#!/usr/bin/env python
"""Minimal test using A2AClient"""

from python_a2a import A2AClient
import traceback

def test_direct_doc_agent():
    """Test direct communication with document_extractor using A2AClient"""
    print("\n=== Testing Direct Communication with Document Extractor ===")
    
    try:
        # Create client for document_extractor
        client = A2AClient("http://localhost:10001", google_a2a_compatible=True)
        print("Created A2AClient for document_extractor")
        
        # Send a simple request
        query = "https://docs.pytest.org"
        print(f"Sending query: '{query}'")
        
        response = client.ask(query)
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return False

def test_root_agent():
    """Test communication with root agent using A2AClient"""
    print("\n=== Testing Communication with Root Agent ===")
    
    try:
        # Create client for root agent
        client = A2AClient("http://localhost:10000", google_a2a_compatible=True)
        print("Created A2AClient for root agent")
        
        # Send a documentation request
        query = "Extract documentation for https://docs.pytest.org"
        print(f"Sending query: '{query}'")
        
        response = client.ask(query)
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing A2A communication with A2AClient...")
    print("Make sure agents are running on ports 10000 and 10001")
    
    # Test document_extractor directly
    doc_success = test_direct_doc_agent()
    
    # Test root agent
    root_success = test_root_agent()
    
    print("\n=== Results ===")
    print(f"Document Extractor: {'PASSED' if doc_success else 'FAILED'}")
    print(f"Root Agent: {'PASSED' if root_success else 'FAILED'}")