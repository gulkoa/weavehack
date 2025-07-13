# doc_agent_server.py

import os
import sys
from typing import Dict

import uvicorn
from a2a.server.apps import A2AFastAPIApplication
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from fastapi import FastAPI

# --- ADK and A2A imports ---
from google.adk.agents import Agent

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

# --- Define AgentSkill and AgentCard for A2A ---
skill = AgentSkill(
    id="extract_documentation",
    name="API Documentation Extractor",
    description="Extracts comprehensive API documentation for websites and services.",
    tags=["documentation", "api", "extraction"],
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

# --- Expose agent as an A2A FastAPI server ---
server = A2AFastAPIApplication(agent_card=agent_card, http_handler=doc_agent)

if __name__ == "__main__":
    print("Starting doc_agent server at http://localhost:10001/")
    uvicorn.run(server.build(), host="localhost", port=10001)
