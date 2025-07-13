from typing import Dict

# --- ADK and A2A imports ---
from google.adk.agents import Agent
from python_a2a import A2AServer, TaskState, TaskStatus, agent, run_server, skill

from agents.document_extrator.temp import (
    extract_documentation as original_extract_documentation,
)


# --- ADK-compatible wrapper ---
def extract_documentation(query: str) -> Dict:
    """
    ADK-compatible wrapper for the original extract_documentation function.

    Args:
        query (str): The website, API name, or service.

    Returns:
        dict: Structured response with status, documentation, and errors.
    """
    try:
        result = original_extract_documentation(query)
        return {
            "status": "success",
            "documentation": str(result),
            "source": f"Documentation extracted for: {query}",
            "query": query,
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to extract documentation: {str(e)}",
            "query": query,
        }


# --- Define the ADK Agent ---
root_adk_agent = Agent(
    name="root_agent",
    model="gemini-2.5-pro",
    description="Main coordination agent that can route requests to other specialized agents and provide general assistance",
    instruction="""You are a root coordination agent that helps users with various tasks. You can:

1. Extract documentation for websites and APIs using the extract_documentation tool
2. Provide general assistance and guidance
3. Route users to appropriate specialized agents when needed
4. Coordinate complex multi-step workflows

When a user asks for documentation extraction, use the extract_documentation tool.
When a user asks about workflows, guide them to the Workflow Generator Agent.
When a user asks about MCP tools or code generation, guide them to the MCP Code Generator Agent.
For general questions, provide helpful responses using your knowledge.""",
    tools=[extract_documentation],
)


@agent(
    name="Root Agent",
    description="Main coordination agent that can route requests to other specialized agents using ADK with Gemini",
    version="1.0.0",
)
class RootAgent(A2AServer):

    def __init__(self):
        super().__init__()
        self.adk_agent = root_adk_agent

    @skill(
        name="Extract Documentation",
        description="Extracts API documentation for websites and services using CrewAI",
        tags=["documentation", "api", "extraction"],
    )
    def extract_documentation(self, query: str) -> Dict:
        """
        Extract documentation using the documentation extractor.

        Args:
            query (str): The website, API name, or service to extract documentation from

        Returns:
            dict: Structured response with documentation
        """
        try:
            result = original_extract_documentation(query)
            return {
                "status": "success",
                "documentation": str(result),
                "source": f"Documentation extracted for: {query}",
                "query": query,
                "agent": "root_agent",
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Failed to extract documentation: {str(e)}",
                "query": query,
                "agent": "root_agent",
            }

    @skill(
        name="Agent Coordination",
        description="Coordinates requests between different specialized agents using ADK with Gemini",
        tags=["coordination", "routing", "orchestration", "adk", "gemini"],
    )
    def coordinate_request(self, request: str, agent_type: str = "auto") -> Dict:
        """
        Coordinate requests to appropriate specialized agents using ADK.

        Args:
            request (str): The request to process
            agent_type (str): Type of agent to route to ("doc", "workflow", "mcp", "auto")

        Returns:
            dict: Response from the appropriate agent or routing information
        """
        try:
            # Use ADK agent to process the request intelligently
            if agent_type == "auto":
                # Let the ADK agent determine how to handle the request
                result = self.adk_agent.ask(f"Please help with this request: {request}")

                return {
                    "status": "success",
                    "response": str(result),
                    "request": request,
                    "agent": "root_agent",
                    "processing_method": "adk_direct",
                }

            # Simple routing logic based on keywords for explicit routing
            request_lower = request.lower()

            if agent_type == "doc" or any(
                keyword in request_lower
                for keyword in ["documentation", "api", "docs", "extract"]
            ):
                return self.extract_documentation(request)
            elif agent_type == "workflow" or any(
                keyword in request_lower
                for keyword in ["workflow", "analyze", "endpoint"]
            ):
                return {
                    "status": "redirect",
                    "message": f"Request should be sent to Workflow Generator Agent at port 10002",
                    "request": request,
                    "suggested_agent": "workflow_generator",
                    "agent": "root_agent",
                }
            elif agent_type == "mcp" or any(
                keyword in request_lower
                for keyword in ["mcp", "tool", "generate", "code"]
            ):
                return {
                    "status": "redirect",
                    "message": f"Request should be sent to MCP Code Generator Agent at port 10003",
                    "request": request,
                    "suggested_agent": "mcp_generator",
                    "agent": "root_agent",
                }
            else:
                # Use ADK agent for general assistance
                result = self.adk_agent.ask(request)
                return {
                    "status": "success",
                    "response": str(result),
                    "request": request,
                    "agent": "root_agent",
                    "processing_method": "adk_general",
                }

        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Failed to coordinate request: {str(e)}",
                "request": request,
                "agent": "root_agent",
            }

    def handle_task(self, task):
        """Handle incoming A2A tasks with intelligent routing using ADK."""
        try:
            # Extract request from the task message
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
                            "text": "Please provide a request to process. I can help with documentation extraction, general assistance, or route you to specialized agents for workflow generation or MCP tool creation.",
                        },
                    },
                )
                return task

            # Check if the request specifies a specific agent type
            agent_type = "auto"
            if text.strip().startswith("@"):
                parts = text.strip().split(" ", 1)
                if len(parts) > 1:
                    agent_type = parts[0][1:]  # Remove @ symbol
                    text = parts[1]

            # Coordinate the request using ADK
            result = self.coordinate_request(text.strip(), agent_type)

            # Format response based on result
            if result["status"] == "success":
                if (
                    result.get("processing_method") == "adk_direct"
                    or result.get("processing_method") == "adk_general"
                ):
                    response_text = (
                        f"**Root Agent Response (via ADK)**\n\n{result['response']}"
                    )
                else:
                    response_text = f"**Documentation Extraction Result**\n\n{result['documentation']}"
            elif result["status"] == "redirect":
                response_text = f"**Request Routing**\n\n{result['message']}\n\nOriginal request: {result['request']}"
            else:
                response_text = f"**Error**\n\n{result['error_message']}"

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
                        "text": f"Error processing request: {str(e)}",
                    },
                },
            )

        return task


if __name__ == "__main__":
    print("Starting Root Agent server at http://localhost:10000/")
    agent = RootAgent()
    run_server(agent, port=10000)
