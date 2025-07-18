# doc_agent_server.py

import os
import sys
from typing import Dict

# --- ADK and A2A imports ---
from google.adk.agents import Agent
from python_a2a import A2AServer, TaskState, TaskStatus, agent, run_server, skill

from agents.document_extrator.doc_extrator import extract_documentation as original_extract_documentation


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
doc_agent = Agent(
    name="doc_agent",
    model="gemini-2.0-flash",
    description="Provides API documentation details for websites and services.",
    instruction="Use the extract_documentation tool to answer API-related queries and documentation requests.",
    tools=[extract_documentation],
)


@agent(
    name="Documentation Agent",
    description="Provides comprehensive API documentation details for websites and services using ADK",
    version="1.0.0",
)
class DocumentationAgent(A2AServer):

    def __init__(self):
        super().__init__()
        self.adk_agent = doc_agent

    @skill(
        name="Extract API Documentation",
        description="Extracts comprehensive API documentation for websites and services using ADK with Gemini",
        tags=["documentation", "api", "extraction", "web-scraping", "adk", "gemini"],
    )
    def extract_documentation(self, query: str) -> Dict:
        """
        Extract API documentation for websites and services using ADK agent.

        Args:
            query (str): The website, API name, or service to extract documentation from.

        Returns:
            dict: Structured response with status, documentation, and metadata.
        """
        try:
            # Use the ADK agent to process the query
            result = self.adk_agent.ask(f"Extract documentation for: {query}")

            return {
                "status": "success",
                "documentation": str(result),
                "source": f"Documentation extracted for: {query}",
                "query": query,
                "extraction_method": "adk_gemini",
                "model": "gemini-2.0-flash",
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Failed to extract documentation: {str(e)}",
                "query": query,
                "suggested_action": "Please verify the URL or service name and try again",
            }

    def handle_task(self, task):
        """Handle incoming A2A tasks for documentation extraction."""
        try:
            # Extract query from the task message
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
                            "text": "Please provide a website URL, API name, or service name to extract documentation from.",
                        },
                    },
                )
                return task

            # Extract documentation using our ADK-powered skill
            result = self.extract_documentation(text.strip())

            # Format response based on result status
            if result["status"] == "success":
                response_text = f"**Documentation for {result['query']}**\n\n{result['documentation']}"
            else:
                response_text = f"**Error extracting documentation for {result['query']}**\n\n{result['error_message']}\n\n{result.get('suggested_action', '')}"

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
                        "text": f"Error processing documentation request: {str(e)}",
                    },
                },
            )

        return task


if __name__ == "__main__":
    print("Starting Documentation Agent server at http://localhost:10001/")
    agent = DocumentationAgent()
    run_server(agent, port=10001)
