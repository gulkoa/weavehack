import ast
from typing import List, Dict, Any, Optional
import uvicorn
    
# doc_agent_server.py

import os
import sys
from typing import Dict

import uvicorn
from a2a.server.apps import A2AFastAPIApplication
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

# --- ADK and A2A imports ---
from google.adk.agents import Agent


def validate_python_syntax(self, code: str) -> Dict[str, Any]:
    """Validates Python code syntax and returns validation result."""
    try:
        ast.parse(code)
        return {"valid": True, "error": None}
    except SyntaxError as e:
        return {
            "valid": False, 
            "error": f"Syntax error at line {e.lineno}: {e.msg}"
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


# --- Define the ADK Agent ---
doc_agent = Agent(
    name="doc_agent",
    model="gemini-2.0-flash",
    description="Generates Python MCP tool code from workflow analysis using LLM",
    instruction="""
You are an expert Python developer creating MCP (Model Context Protocol) tools from workflow analysis.

Given the following workflow analysis, create useful MCP tools as Python functions. Each tool should:
1. Be completely synchronous (no async/await)
2. Handle authentication properly using the auth information provided
3. Include comprehensive error handling and retry logic
4. Implement complete workflows by combining multiple API calls
5. Return meaningful results in a structured format
6. Include proper docstrings with parameter descriptions
7. Use only standard libraries (requests, json, time, urllib, etc.)
8. Handle common edge cases (network errors, rate limits, invalid responses)

For each workflow in the analysis, generate corresponding Python functions that implement the complete workflow.

Return a JSON array where each object has:
{{
    "name": "function_name",
    "description": "Brief description of what this tool does",
    "workflow_name": "name of the workflow this implements",
    "python_body": "complete Python function code as a string",
    "complexity": "simple|medium|complex",
    "estimated_api_calls": "number of API calls this function makes"
}}

Guidelines for code generation:
- Create one function per workflow
- Include proper authentication handling in each function
- Add retry logic for network failures
- Handle rate limiting with appropriate delays
- Validate input parameters
- Return structured, useful results
- Include error context in exceptions
- Add logging or status updates for complex workflows
- Use descriptive variable names
- Include examples in docstrings

Make the tools as practical and robust as possible. Focus on real-world usage scenarios.
""",
    tools=[validate_python_syntax],
)

# --- Define AgentSkill and AgentCard for A2A ---
skill = AgentSkill(
            id="generate_mcp_code",
            name="Generate MCP Tools",
            description="Generates Python MCP tool code from workflow analysis",
            tags=["mcp", "python", "code", "generation", "tools"],
            examples=[
                "Generate MCP tools from this workflow analysis",
                "Create Python code for these API workflows",
                "Convert workflow analysis to MCP tools",
            ],
        )

agent_card = AgentCard (
        name="MCP Code Generator Agent",
        description="Generates Python MCP tool code from workflow analysis",
        url=f"http://localhost:10003/",
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
    ),

# --- Expose agent as an A2A FastAPI server ---
server = A2AFastAPIApplication(agent_card=agent_card, http_handler=doc_agent)

if __name__ == "__main__":
    print("Starting doc_agent server at http://localhost:10001/")
    uvicorn.run(server.build(), host="localhost", port=10001)
