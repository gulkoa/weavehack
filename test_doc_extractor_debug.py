#!/usr/bin/env python
"""Debug document extractor agent"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.document_extrator.agent import DocumentationAgent

def test_agent_directly():
    """Test the agent methods directly without A2A"""
    print("\n=== Testing DocumentationAgent Directly ===")
    
    # Create agent instance
    agent = DocumentationAgent()
    print(f"Agent created: {agent}")
    
    # Test the extract_documentation method directly
    try:
        result = agent.extract_documentation("https://docs.pytest.org")
        print(f"Direct method call result: {result}")
    except Exception as e:
        print(f"Error calling extract_documentation: {e}")
        import traceback
        traceback.print_exc()
    
    # Test handle_task method with a mock task
    print("\n=== Testing handle_task method ===")
    from python_a2a import Task, TaskStatus, TaskState
    
    # Create a mock task
    task = Task(
        id="test-task-123",
        message={
            "role": "user",
            "content": {
                "type": "text",
                "text": "https://docs.pytest.org"
            }
        },
        status=TaskStatus(state=TaskState.AWAITING_RESULT)
    )
    
    print(f"Created task: {task}")
    
    try:
        result_task = agent.handle_task(task)
        print(f"Result task status: {result_task.status}")
        if hasattr(result_task, 'artifacts'):
            print(f"Result artifacts: {result_task.artifacts}")
    except Exception as e:
        print(f"Error handling task: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_directly()