import ast
import json
from typing import Any, Dict, List, Optional

# --- ADK and A2A imports ---
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from python_a2a import A2AServer, TaskState, TaskStatus, agent, run_server, skill


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
mcp_agent = Agent(
    name="mcp_generator",
    model="gemini-2.5-pro",
    description="Generates Python MCP tool code from workflow analysis using LLM",
    instruction="""
You are an expert Python developer creating MCP (Model Context Protocol) tools from workflow analysis.
You MUST use FastMCP to develop the MCP tools.

Here is the workflow analysis you will be working with:

Please follow these instructions to create FastMCP tools:

Sample FastMCP code:
```python
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀") # This is the name of the MCP server

@mcp.tool
def add(a: int, b: int) -> int:
    "Add two numbers"
    return a + b

if __name__ == "__main__":
    mcp.run()
```

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
- Use FastMCP to develop the MCP tools. DO NOT USE ANY OTHER MCP LIBRARY.
- Include proper authentication handling in each function
- Add retry logic for network failures
- Handle rate limiting with appropriate delays
- Validate input parameters
- Return structured, useful results
- Include error context in exceptions
- Add logging or status updates for complex workflows
- Use descriptive variable names
- Include examples in docstrings

3. Implement proper FastMCP decorators and structures for each function.

4. Ensure your code follows these additional guidelines:
   a. Add retry logic for network failures
   b. Handle rate limiting with appropriate delays
   c. Validate input parameters
   d. Include error context in exceptions
   e. Add logging or status updates for complex workflows
   f. Use descriptive variable names
   g. Include examples in docstrings

5. After implementing all functions, create a FastMCP server that includes all the tools you've created.

Please provide your complete Python code for the FastMCP server, including all necessary imports, function definitions, and the server setup. Your code should be ready to run and should implement all workflows described in the analysis.

Remember to make your tools as practical and robust as possible, focusing on real-world usage scenarios. Good luck!

""".strip(),
    tools=[validate_python_syntax],
)


@agent(
    name="MCP Code Generator Agent",
    description="Generates Python MCP tool code from workflow analysis using ADK with Gemini",
    version="1.0.0",
)
class MCPCodeGeneratorAgent(A2AServer):

    def __init__(self):
        super().__init__()
        self.adk_agent = mcp_agent

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

    def ask(self, question: str):
        """Ask a question to the Gemini agent using ADK session and runner."""
        session_service = InMemorySessionService()
        session = session_service.create_session_sync(
            app_name="my_app", user_id="user1", session_id="mysession"
        )
        runner = Runner(
            agent=self.adk_agent, app_name="my_app", session_service=session_service
        )
        content = types.Content(role="user", parts=[types.Part(text=question)])

        # 3. Send the question and print the response
        events = runner.run(
            user_id="user1", session_id="mysession", new_message=content
        )
        for event in events:
            if event.is_final_response():
                return event.content.parts[0].text

    @skill(
        name="Generate MCP Tools",
        description="Generates Python MCP tool code from workflow analysis using ADK with Gemini",
        tags=["mcp", "python", "code", "generation", "tools", "adk", "gemini"],
    )
    def generate_mcp_tools(self, workflow_analysis: str) -> str:
        """
        Generate Python MCP tool code from workflow analysis using ADK agent.

        Args:
            workflow_analysis (str): The workflow analysis to generate MCP tools from

        Returns:
            str: Generated MCP tools as JSON string
        """
        try:
            # Use the ADK agent to generate MCP tools
            result = self.ask(
                f"Generate MCP tools from this workflow analysis:\n\n{workflow_analysis}"
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
                    },
                    indent=2,
                )

        except Exception as e:
            return json.dumps(
                {"error": f"Failed to generate MCP tools: {str(e)}", "tools": []}
            )

    def handle_task(self, task):
        """Handle incoming A2A tasks for MCP code generation."""
        try:
            # Extract workflow analysis from the task message
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
                            "text": "Please provide workflow analysis to generate MCP tools from.",
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
                # Generate MCP tools from workflow analysis using ADK
                mcp_tools = self.generate_mcp_tools(text.strip())
                response_text = (
                    f"**Generated MCP Tools (via ADK)**\n\n```json\n{mcp_tools}\n```"
                )

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
                        "text": f"Error generating MCP tools: {str(e)}",
                    },
                },
            )

        return task


if __name__ == "__main__":
    print("Starting MCP Code Generator Agent server at http://localhost:10003/")
    agent = MCPCodeGeneratorAgent()
    run_server(agent, port=10003)
