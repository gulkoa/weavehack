import ast
import json
from typing import Any, Dict, List, Optional

# --- ADK and A2A imports ---
from google.adk.agents import Agent
from python_a2a import A2AServer, TaskState, TaskStatus, agent, run_server, skill
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

def validate_python_syntax(code: str) -> Dict[str, Any]:
    """Validates Python code syntax and returns validation result."""
    try:
        ast.parse(code)
        return {"valid": True, "error": None}
    except SyntaxError as e:
        return {"valid": False, "error": f"Syntax error at line {e.lineno}: {e.msg}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


# --- Define the ADK Agent ---
workflow_agent = Agent(
    name="workflow_generator",
    model="gemini-2.0-flash",
    description="Analyzes REST API descriptions and generates logical workflows",
    instruction="""
You are an expert API workflow analyst. Analyze the following REST API description and identify:

1. All available endpoints and their HTTP methods
2. Required and optional parameters for each endpoint
3. Authentication requirements
4. Data formats and response types
5. Logical workflows that combine multiple endpoints for common use cases
6. Dependencies between endpoints (e.g., create before update, authenticate before action)
7. Error handling patterns and edge cases
8. Rate limiting or special considerations

Focus heavily on identifying USEFUL WORKFLOWS that solve real problems by combining multiple API calls.

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


@agent(
    name="Workflow Generator Agent",
    description="Analyzes REST API descriptions and generates logical workflows using ADK with Gemini",
    version="1.0.0",
)
class WorkflowGeneratorAgent(A2AServer):

    def __init__(self):
        super().__init__()
        self.adk_agent = workflow_agent

    @skill(
        name="Validate Python Syntax",
        description="Validates Python code syntax and returns validation result",
        tags=["python", "validation", "syntax", "ast"],
    )
    def validate_python_syntax(self, code: str) -> Dict[str, Any]:
        """Validates Python code syntax and returns validation result."""
        try:
            ast.parse(code)
            return {"valid": True, "error": None}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax error at line {e.lineno}: {e.msg}",
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    @skill(
        name="Generate API Workflows",
        description="Analyzes REST API descriptions and identifies useful workflows using ADK with Gemini",
        tags=["api", "workflow", "analysis", "rest", "adk", "gemini"],
    )
    def generate_workflows(self, api_description: str) -> str:
        """
        Analyze REST API description and generate logical workflows using ADK agent.

        Args:
            api_description (str): The REST API description to analyze

        Returns:
            str: Generated workflow analysis as JSON string
        """
        try:
            # Use the ADK agent to analyze the API description and generate workflows
            result = self.ask(
                f"Analyze this REST API description and generate workflows:\n\n{api_description}"
            )

            # Try to parse as JSON to validate format
            try:
                parsed = json.loads(str(result))
                return json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                # If not valid JSON, wrap in a structured response
                return json.dumps(
                    {
                        "generated_content": str(result),
                        "note": "Generated by ADK agent - may need formatting adjustment",
                        "source": "gemini-2.0-flash",
                        "api_description": (
                            api_description[:200] + "..."
                            if len(api_description) > 200
                            else api_description
                        ),
                    },
                    indent=2,
                )

        except Exception as e:
            return json.dumps(
                {"error": f"Failed to generate workflows: {str(e)}", "workflows": []}
            )

    def handle_task(self, task):
        """Handle incoming A2A tasks for workflow generation."""
        try:
            # Extract API description from the task message
            message_data = task.message or {}
            content = message_data.get("content", {})

            if isinstance(content, dict):
                text = content.get("text", "")
            else:
                text = str(content)

            if not text.strip():
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={
                        "role": "agent",
                        "content": {
                            "type": "text",
                            "text": "Please provide a REST API description to analyze and generate workflows from.",
                        },
                    },
                )
                return task

            # Check if the input looks like a request for syntax validation
            if text.strip().startswith("validate:"):
                code_to_validate = text.strip()[9:].strip()
                validation_result = self.validate_python_syntax(code_to_validate)

                if validation_result["valid"]:
                    response_text = "✅ **Python Code Validation: PASSED**\n\nThe provided code has valid Python syntax."
                else:
                    response_text = f"❌ **Python Code Validation: FAILED**\n\nError: {validation_result['error']}"

            else:
                # Generate workflows from API description using ADK
                workflows = self.generate_workflows(text.strip())
                response_text = f"**Generated API Workflows (via ADK)**\n\n```json\n{workflows}\n```"

            # Create response
            task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
            task.status = TaskStatus(state=TaskState.COMPLETED)

        except Exception as e:
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent",
                    "content": {
                        "type": "text",
                        "text": f"Error generating workflows: {str(e)}",
                    },
                },
            )

        return task
    
    def ask(self, question: str):
        """Ask a question to the Gemini agent using ADK session and runner."""
        session_service = InMemorySessionService()
        session = session_service.create_session_sync(
            app_name="my_app",
            user_id="user1",
            session_id="mysession"
        )
        runner = Runner(agent=self.adk_agent, app_name="my_app", session_service=session_service)
        content = types.Content(role='user', parts=[types.Part(text=question)])

        # 3. Send the question and print the response
        events = runner.run(user_id="user1", session_id="mysession", new_message=content)
        for event in events:
            if event.is_final_response():
                return event.content.parts[0].text


if __name__ == "__main__":
    print("Starting Workflow Generator Agent server at http://localhost:10002/")
    agent = WorkflowGeneratorAgent()
    run_server(agent, port=10002)
