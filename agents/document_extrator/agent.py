# doc_agent_server.py

import os
import sys
from typing import Dict

# --- ADK and A2A imports ---
from google.adk.agents import Agent
from python_a2a import A2AServer, TaskState, TaskStatus, agent, run_server, skill
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types


from .temp import extract_documentation as original_extract_documentation


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
        # The function now returns a dict, so we can return it directly
        return result
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
        print(f"[DocumentationAgent] Initialized with ADK agent: {self.adk_agent.name}")

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
        print(f"\n[DocumentationAgent.extract_documentation] Called with query: '{query}'")
        try:
            # Use the original extract_documentation function which now returns a dict
            print(f"[DocumentationAgent.extract_documentation] Calling original_extract_documentation...")
            result = original_extract_documentation(query)
            print(f"[DocumentationAgent.extract_documentation] Got result: {result}")
            return result
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
            print(f"\n[DocumentationAgent] Received task: {task}")
            print(f"[DocumentationAgent] Task message: {task.message}")
            # Extract query from the task message
            message_data = task.message or {}
            content = message_data.get("content", {})

            if isinstance(content, dict):
                text = content.get("text", "")
            else:
                text = str(content)

            print(f"[DocumentationAgent] Extracted text: '{text}'")

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
            print(f"[DocumentationAgent] Calling extract_documentation with: '{text.strip()}'")
            result = self.extract_documentation(text.strip())
            print(f"[DocumentationAgent] Result: {result}")

            # Format response based on result status
            if result["status"] == "success":
                response_text = f"**Documentation for {text.strip()}**\n\n{result['documentation']}"
            else:
                response_text = f"**Error extracting documentation for {text.strip()}**\n\n{result['error_message']}\n\n{result.get('suggested_action', '')}"

            # Create response
            print(f"[DocumentationAgent] Sending response: {response_text[:100]}...")
            task.artifacts = [{"parts": [{"type": "text", "text": response_text}]}]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            print(f"[DocumentationAgent] Task completed successfully")

        except Exception as e:
            print(f"[DocumentationAgent] Error processing task: {str(e)}")
            import traceback
            traceback.print_exc()
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
    print("Starting Documentation Agent server at http://localhost:10001/")
    print("[DocumentationAgent] Creating agent instance...")
    agent = DocumentationAgent()
    print(f"[DocumentationAgent] Agent created: {agent}")
    print("[DocumentationAgent] Starting A2A server...")
    run_server(agent, port=10001)
