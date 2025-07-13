#!/usr/bin/env python3
"""Test script to verify the root agent executes multiple steps in workflow."""

import time
from python_a2a import A2AClient

def test_root_agent_workflow():
    """Test that the root agent properly orchestrates all three agents."""
    print("Testing Root Agent Multi-Step Workflow")
    print("=" * 50)
    
    # Connect to the root agent
    root_client = A2AClient("http://localhost:10000")
    
    # Test query that should trigger the full workflow
    test_query = "Create an MCP server for the GitHub API"
    
    print(f"\nSending query: '{test_query}'")
    print("Expected behavior: Root agent should:")
    print("  1. Call document_extractor to get API docs")
    print("  2. Call workflow_generator to analyze the docs")
    print("  3. Call mcp_generator to create the server code")
    print("\nWaiting for response...")
    
    start_time = time.time()
    
    try:
        response = root_client.ask(test_query)
        
        elapsed_time = time.time() - start_time
        
        print(f"\nResponse received in {elapsed_time:.2f} seconds")
        print("-" * 50)
        print(response)
        print("-" * 50)
        
        # Check if the response contains evidence of all three steps
        if "MCP Server Generation Results" in response or "Generated MCP Server Code" in response:
            print("\n✅ SUCCESS: Root agent appears to have completed the workflow!")
        else:
            print("\n⚠️  WARNING: Response may not contain complete workflow results")
        
        # Look for evidence of tool usage
        if "extract_documentation" in response or "Documentation Extracted" in response:
            print("✅ Step 1: Documentation extraction detected")
        else:
            print("❌ Step 1: Documentation extraction NOT detected")
            
        if "generate_workflows" in response or "Workflows Analyzed" in response:
            print("✅ Step 2: Workflow generation detected")
        else:
            print("❌ Step 2: Workflow generation NOT detected")
            
        if "generate_mcp_server" in response or "MCP Server Generated" in response:
            print("✅ Step 3: MCP generation detected")
        else:
            print("❌ Step 3: MCP generation NOT detected")
        
        # Check for actual code generation
        if "```python" in response:
            print("\n✅ Python code block detected in response!")
        else:
            print("\n❌ No Python code block found in response")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nMake sure all agents are running:")
        print("  - Root Agent (port 10000)")
        print("  - Document Extractor (port 10001)")
        print("  - Workflow Generator (port 10002)")
        print("  - MCP Generator (port 10003)")

if __name__ == "__main__":
    test_root_agent_workflow()