import os
import sys
from typing import Dict
import asyncio

import uvicorn
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities, 
    AgentCard, 
    AgentSkill,
    TaskState,
    Part,
    TextPart
)
from a2a.utils import new_agent_text_message, new_task
from fastapi import FastAPI

# --- ADK and A2A imports ---
from google.adk.agents import Agent

# Fix the import - should be doc_extractor, not doc_extrator
try:
    from agents.doc_extrator import extract_documentation as original_extract_documentation
except ImportError:
    # Fallback if the file is actually named doc_extrator
    from agents.doc_extrator import extract_documentation as original_extract_documentation


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


# --- A2A Executor for proper integration ---
class DocAgentExecutor(AgentExecutor):
    """A2A executor that wraps the ADK doc agent."""
    
    def __init__(self, agent: Agent):
        self.agent = agent
        
    async def cancel(self, task_id: str) -> None:
        """Cancel the execution of a specific task."""
        pass
        
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute documentation extraction using the ADK agent."""
        query = context.get_user_input()
        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)
        
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        try:
            # ADD MESSAGE FILTERING LOGIC HERE
            query_lower = query.lower()
            doc_keywords = [
                'extract', 'documentation', 'docs', 'api', 'extract documentation',
                'get documentation', 'api docs', 'documentation for', 'get docs',
                'github api', 'stripe api', 'twitter api', 'api.', '.com', 'http'
            ]
            
            # Check if this is actually a documentation request
            is_doc_request = any(keyword in query_lower for keyword in doc_keywords)
            
            if not is_doc_request:
                # Handle non-documentation requests
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message("Processing your request...", task.contextId, task.id)
                )
                
                # Simple response for non-doc requests
                simple_responses = {
                    'hello': "Hello! I'm a documentation extraction agent. I can help you extract API documentation from websites and services.",
                    'capabilities': "I can extract comprehensive API documentation for websites and services. Try asking me to 'extract documentation for GitHub API' or 'get docs for stripe.com'.",
                    'help': "I specialize in extracting API documentation. You can ask me things like:\n- Extract documentation for GitHub API\n- Get API docs for stripe.com\n- Documentation for twitter API",
                    'ping': "Pong! I'm online and ready to extract documentation.",
                    'what are your capabilities': "I can extract comprehensive API documentation for websites and services. Try asking me to 'extract documentation for GitHub API' or 'get docs for stripe.com'.",
                    'how much is 10 usd in inr': "I'm a documentation extraction agent, not a currency converter. I help extract API documentation from websites and services. Try asking me to extract documentation for a specific API!"
                }
                
                response_text = simple_responses.get(query_lower, 
                    "I'm a documentation extraction agent. I help extract API documentation from websites and services. Try asking me to extract documentation for a specific API or service!")
                
                await updater.add_artifact(
                    [Part(root=TextPart(text=response_text))],
                    name="response"
                )
                await updater.complete()
                return
            
            # Only extract documentation for actual doc requests
            await updater.update_status(
                TaskState.working,
                new_agent_text_message("Extracting documentation...", task.contextId, task.id)
            )
            
            # Extract documentation
            result = extract_documentation(query)
            
            if result["status"] == "success":
                response_text = f"""# Documentation Extraction Results

## Source
{result["source"]}

## Documentation
{result["documentation"]}
"""
                
                # Add response as artifact
                await updater.add_artifact(
                    [Part(root=TextPart(text=response_text))],
                    name="documentation"
                )
                
                await updater.complete()
            else:
                await updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(f"Error: {result['error_message']}", task.contextId, task.id),
                    final=True
                )
                
        except Exception as e:
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(f"Documentation extraction failed: {str(e)}", task.contextId, task.id),
                final=True
            )


# --- Define AgentSkill and AgentCard for A2A ---
skill = AgentSkill(
    id="extract_documentation",
    name="API Documentation Extractor",
    description="Extracts comprehensive API documentation for websites and services.",
    tags=["documentation", "api", "extraction"],
    examples=[
        "Extract documentation for GitHub API",
        "Get API docs for stripe.com",
        "Documentation for twitter API",
    ],
)

agent_card = AgentCard(
    name="doc_agent",
    description="Provides API documentation details for websites and services.",
    url="http://localhost:10001/",
    version="1.0.0",
    skills=[skill],
    capabilities=AgentCapabilities(streaming=True),
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
)

# --- Create proper A2A server ---
def create_doc_agent_server():
    """Create A2A server for documentation agent."""
    executor = DocAgentExecutor(agent=doc_agent)
    
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    
    return A2AFastAPIApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

if __name__ == "__main__":
    print("Starting doc_agent server at http://localhost:10001/")
    server = create_doc_agent_server()
    uvicorn.run(server.build(), host="localhost", port=10001)