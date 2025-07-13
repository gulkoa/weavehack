import json
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional
from wsgiref import types

# --- CrewAI and A2A imports ---
from crewai import LLM
from crewai import Agent as CrewAIAgent
from crewai import Crew, Task
from crewai.tools import tool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from python_a2a import (
    A2AClient,
    A2AServer,
    AgentNetwork,
    AIAgentRouter,
    TaskState,
    TaskStatus,
    agent,
    run_server,
    skill,
)

# Create an agent network
network = AgentNetwork(name="MCP Development Network")

# Add agents to the network
network.add("document_extractor", "http://localhost:10001")
network.add("workflow_generator", "http://localhost:10002")
network.add("mcp_generator", "http://localhost:10003")


def ask_agent(agent_type: str, question: str) -> str:
    # Get the agent from the network
    agent = network.get_agent(agent_type)
    if not agent:
        raise Exception(f"Agent {agent_type} not available")
    return agent.ask(question)


@tool("extract_documentation")
def extract_documentation(question: str) -> str:
    """Extracts API documentation from a given URL or query"""
    return ask_agent("document_extractor", question)


@tool("generate_workflows")
def generate_workflows(question: str) -> str:
    """Generates workflows from a given API documentation"""
    return ask_agent("workflow_generator", question)


@tool("generate_mcp")
def generate_mcp(question: str) -> str:
    """Generates MCP server code from a given workflow"""
    return ask_agent("mcp_generator", question)


llm = LLM(
    model="openrouter/anthropic/claude-sonnet-4",
    timeout=10000,
    api_base="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Create the CrewAI agent
crewai_agent = CrewAIAgent(
    role="Root Agent",
    goal="Return python code for an MCP server for a given API using tools",
    backstory="""You are a root coordination agent that helps users create MCP servers through a multi-step process. You have access to three specialized agents as tools:

- Document Extractor Agent: Extracts API documentation
- Workflow Generator Agent: Analyzes APIs and generates workflow descriptions  
- MCP Generator Agent: Creates MCP server implementations

You can also engage in general conversation with users who want to chat. For technical requests, you'll coordinate between the specialized agents to accomplish tasks through these steps:

1. Documentation Extraction: Extract and understand API documentation
2. Workflow Analysis: Analyze the API to identify key workflows and patterns  
3. MCP Server Generation: Generate the MCP server code based on the analysis
4. Integration: Help users integrate and test the generated server

Please note that the Documentation Extractor Agent is expensive to use, so please use it sparingly.

NOTE:
1. Document Extractor Agent does not need context from previous steps or other agents.
2. Workflow Generator Agent does ALWAYS needs context from the Document Extractor Agent.
3. MCP Generator Agent does ALWAYS needs context from the Workflow Generator Agent.

DO NOT CALL THE AGENTS WITHOUT PROPER CONTEXT.


""",
    tools=[extract_documentation, generate_workflows, generate_mcp],
    verbose=True,
    llm=llm
)


@agent(
    name="Root Agent",
    description="Main coordination agent that orchestrates the MCP server generation process",
    version="1.0.0",
)
class RootAgent(A2AServer):
    def __init__(self):
        super().__init__()
        self.adk_agent = crewai_agent

    @skill(
        name="Agent Coordination",
        description="Coordinates the MCP server generation process across specialized agents",
        tags=["coordination", "routing", "orchestration", "crewai"],
    )
    def coordinate_request(self, request: str, query: str) -> Dict:
        """
        Coordinate requests across specialized agents to generate MCP servers.

        Args:
            request (str): The user's request
            query (str): The query to the agent

        Returns:
            dict: Response from the appropriate agent with next steps
        """
        try:
            # Use the ADK agent to process the query
            result = self.ask(request)

            return {
                "status": "success",
                "response": str(result),
                "query": query,
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Failed to process request: {str(e)}",
                "query": query,
            }

    def handle_task(self, task):
        """Handle incoming A2A tasks with intelligent routing using CrewAI."""
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
                            "text": "Please provide a request. I can help you create an MCP server by coordinating documentation extraction, workflow analysis, and code generation.",
                        },
                    },
                )
                return task

            # Use the CrewAI agent to process the request
            result = self.coordinate_request(text.strip(), text.strip())

            # Format response based on result status
            if result["status"] == "success":
                response_text = f"""**MCP Server Generation Request**

**Query:** {result['query']}

**Response:**
{result['response']}

**Next Steps:** You can continue the conversation or ask for specific help with documentation extraction, workflow generation, or MCP server creation."""
            else:
                response_text = f"""**❌ Error Processing Request**

**Query:** {result['query']}
**Error:** {result['error_message']}

**Suggestion:** Please try rephrasing your request or ask for help with a specific aspect of MCP server generation."""

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

    def ask(self, question: str):
        """Ask a question to the Gemini agent using ADK session and runner."""
        task = Task(
            description="Answer the question: {user_input}",
            expected_output="A response to the question",
            agent=self.adk_agent,
        )
        crew = Crew(
            agents=[self.adk_agent],
            tasks=[task],
            verbose=True,
        )
        return crew.kickoff({"user_input": question})


if __name__ == "__main__":
    print("Starting Root Agent server at http://localhost:10000/")
    agent = RootAgent()
    run_server(agent, port=10000)
