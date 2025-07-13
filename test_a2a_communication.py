#!/usr/bin/env python
"""Test A2A communication between root agent and document_extractor agent"""

import time
from python_a2a import A2AClient

def test_document_extractor():
    """Test direct communication with document_extractor agent"""
    print("\n=== Testing Document Extractor Agent ===")
    
    # Create client for document_extractor
    doc_client = A2AClient("http://localhost:10001", google_a2a_compatible=True)
    
    # Test with a simple query
    test_query = "https://docs.pytest.org"
    print(f"Sending query to document_extractor: '{test_query}'")
    
    try:
        response = doc_client.ask(test_query)
        print(f"Response from document_extractor: {response}")
        return True
    except Exception as e:
        print(f"Error communicating with document_extractor: {e}")
        return False

def test_root_to_doc_communication():
    """Test root agent forwarding to document_extractor"""
    print("\n=== Testing Root Agent to Document Extractor Communication ===")
    
    # Create client for root agent
    root_client = A2AClient("http://localhost:10000", google_a2a_compatible=True)
    
    # Test with a documentation request
    test_query = "Extract documentation for https://docs.pytest.org"
    print(f"Sending query to root agent: '{test_query}'")
    
    try:
        response = root_client.ask(test_query)
        print(f"Response from root agent: {response}")
        return True
    except Exception as e:
        print(f"Error communicating with root agent: {e}")
        return False

if __name__ == "__main__":
    print("Starting A2A communication tests...")
    print("Make sure both root agent (port 10000) and document_extractor agent (port 10001) are running!")
    
    # Give servers time to start
    time.sleep(2)
    
    # Test direct communication
    doc_test_passed = test_document_extractor()
    
    # Test root to doc communication
    root_test_passed = test_root_to_doc_communication()
    
    print("\n=== Test Results ===")
    print(f"Document Extractor Direct Test: {'PASSED' if doc_test_passed else 'FAILED'}")
    print(f"Root to Document Extractor Test: {'PASSED' if root_test_passed else 'FAILED'}")