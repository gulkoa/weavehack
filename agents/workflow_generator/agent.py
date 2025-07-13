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
    name="workflow_generator",
    model="gemini-2.0-flash",
    description="Analyzes REST API descriptions and generates logical workflows",
    instruction="""
"You are an expert API workflow analyst. Analyze the following REST API description and identify:

1. All available endpoints and their HTTP methods
2. Required and optional parameters for each endpoint
3. Authentication requirements
4. Data formats and response types
5. Logical workflows that combine multiple endpoints for common use cases
6. Dependencies between endpoints (e.g., create before update, authenticate before action)
7. Error handling patterns and edge cases
8. Rate limiting or special considerations

Focus heavily on identifying USEFUL WORKFLOWS that solve real problems by combining multiple API calls.

API Description:
{api_description}

Return your analysis as a JSON object with this structure:
{{
    "endpoints": [
        {{
            "method": "GET|POST|PUT|DELETE|PATCH",
            "path": "/endpoint/path",
            "description": "What this endpoint does",
            "parameters": [
                {{"name": "param_name", "type": "string|number|boolean|object", "required": true|false, "description": "param description"}}
            ],
            "auth_required": true|false,
            "response_type": "json|text|binary|etc",
            "depends_on": ["endpoint_ids that must be called first"],
            "error_codes": ["common error codes and meanings"]
        }}
    ],
    "auth": {{
        "type": "bearer|api_key|basic|oauth",
        "header_name": "Authorization|X-API-Key|etc",
        "description": "How to authenticate",
        "endpoint": "/auth/endpoint if applicable"
    }},
    "workflows": [
        {{
            "name": "workflow_name",
            "description": "What this workflow accomplishes and why it's useful",
            "steps": [
                {{
                    "step": 1,
                    "endpoint": "/endpoint/path",
                    "method": "GET|POST|etc",
                    "description": "What this step does",
                    "requires_data_from": ["previous step numbers"],
                    "error_handling": "How to handle errors in this step"
                }}
            ],
            "use_case": "Detailed description of when and why to use this workflow",
            "complexity": "simple|medium|complex",
            "estimated_duration": "How long this workflow typically takes"
        }}
    ],
    "base_url": "https://api.example.com",
    "considerations": [
        "rate limits",
        "async operations", 
        "file uploads",
        "pagination",
        "error retry strategies",
        "data validation requirements"
    ],
    "common_patterns": [
        {{
            "pattern": "CRUD operations",
            "description": "Standard create, read, update, delete patterns",
            "applicable_workflows": ["workflow names that use this pattern"]
        }}
    ]
}}

Be extremely thorough in identifying workflows. Think about:
- Complete user journeys (sign up, configure, use, delete)
- Data processing pipelines (upload, process, download results)
- Batch operations (bulk create, bulk update, bulk delete)
- Monitoring and reporting workflows
- Integration scenarios
- Error recovery workflows
""",
    tools=[validate_python_syntax],
)

# --- Define AgentSkill and AgentCard for A2A ---
skill = AgentSkill(
                id="generate_workflows",
                name="Generate API Workflows",
                description="Analyzes REST API descriptions and identifies useful workflows",
                tags=["api", "workflow", "analysis", "rest"],
                examples=[
                    "Analyze this API and generate workflows",
                    "What workflows can I create with this REST API?",
                    "Generate useful workflows from this API documentation",
                ],
            )

agent_card = AgentCard (
        name="Workflow Generator Agent",
        description="Analyzes REST API descriptions and generates logical workflows",
        url=f"http://localhost:10002/",
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
    ),

# --- Expose agent as an A2A FastAPI server ---
server = A2AFastAPIApplication(agent_card=agent_card, http_handler=doc_agent)

if __name__ == "__main__":
    print("Starting doc_agent server at http://localhost:10002/")
    uvicorn.run(server.build(), host="localhost", port=10001)
