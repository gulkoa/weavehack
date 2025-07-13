import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from contextlib import redirect_stdout
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

from pydantic import BaseModel, Field


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


@tool("save_code")
def save_code(code: str) -> str:
    """Saves the code to a file"""

    fly_toml = f"""
app = 'mcp-boilerplate-{str(uuid.uuid4())[:8]}'
primary_region = 'sjc'

[build]

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = 'stop'
  auto_start_machines = true
  min_machines_running = 0
  processes = ['app']

[[vm]]
  memory = '1gb'
  cpu_kind = 'shared'
  cpus = 1
""".strip()

    # Use context manager for temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create the mcp_boilerplate directory path
            mcp_dir = os.path.join(temp_dir, "mcp_boilerplate")

            # Copy mcp_boilerplate to temp dir
            shutil.copytree("mcp_boilerplate", mcp_dir)

            # Write main.py in the mcp_boilerplate directory
            main_path = os.path.join(mcp_dir, "main.py")
            with open(main_path, "w") as f:
                f.write(code + "\n")

            # Write fly.toml in the mcp_boilerplate directory
            fly_path = os.path.join(mcp_dir, "fly.toml")
            with open(fly_path, "w") as f:
                f.write(fly_toml + "\n")

            # Create deploy log path
            deploy_log_path = os.path.join(temp_dir, "deploy.log")

            # Run the "fly deploy" command from the mcp_boilerplate directory
            with open(deploy_log_path, "w") as f:
                result = subprocess.run(
                    ["fly", "launch", "-y"],
                    cwd=mcp_dir,  # Run from the mcp_boilerplate directory
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

            # Read the deploy output from the file
            with open(deploy_log_path, "r") as f:
                output = f.read()

            print("--------------------------------")
            print(output)

            # Write the deploy output to the current working directory
            with open(os.path.join(os.getcwd(), "deploy.log"), "w") as f:
                f.write(output)

            # Extract the URL from the output
            if "Visit your newly deployed app at" in output:
                url = output.split("Visit your newly deployed app at")[1].strip()
                return url
            else:
                return f"Error deploying: {output}"

        except Exception as e:
            return f"Error saving code: {str(e)}"


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
    backstory="""

You are a root coordination agent responsible for helping users create MCP servers through a multi-step process. You have access to three specialized agents: Document Extractor Agent, Workflow Generator Agent, and MCP Generator Agent. Your task is to coordinate between these agents and interact with the user to accomplish the goal of creating an MCP server.

When you receive user input, analyze it to determine if it's a technical request related to creating an MCP server or a general conversation. Here's how to handle each situation:

For technical requests:
1. If the user's request is related to creating an MCP server, begin the process by calling the Document Extractor Agent.

2. Once you receive the result from the Document Extractor Agent, call the Workflow Generator Agent with the extracted documentation.

3. After receiving the result from the Workflow Generator Agent, call the MCP Generator Agent with the workflow analysis. You must not generate any code yourself.

4. Once you have the result from the MCP Generator Agent, provide the user with the generated MCP server code ALONGSIDE THE URL OF THE MCP SERVER (if available) 
Do not alter the code in any way. The MCP Generator Agent will generate FastMCP code for you.

Finally, once/if you have generated the MCP server code, save it to a file using the save_code tool.
This will give you the deployment URL of the MCP server. Return the URL to the user.

Important notes:
- The Document Extractor Agent is expensive to use, so use it sparingly and only when necessary.
- Always provide context from the previous agent to the next agent in the sequence.
- Do not call agents without proper context from the previous step.

""".strip(),
    tools=[extract_documentation, generate_workflows, generate_mcp, save_code],
    verbose=True,
    llm=llm,
)


class Output(BaseModel):
    python_code: str = Field(description="Python code describing MCP server")


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
            output_pydantic=Output,
        )
        crew = Crew(
            agents=[self.adk_agent],
            tasks=[task],
            verbose=True,
        )
        output = crew.kickoff({"user_input": question})
        print(str(output))
        return output.pydantic.python_code


if __name__ == "__main__":
    print("Starting Root Agent server at http://localhost:10000/")
    agent = RootAgent()
    run_server(agent, port=10000)
