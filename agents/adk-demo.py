import datetime
import os

# Import the original extract_documentation function
import sys
from zoneinfo import ZoneInfo

from google.adk.agents import Agent

from agents.doc_extrator import extract_documentation as original_extract_documentation


def extract_documentation(query: str) -> dict:
    """ADK-compatible wrapper for the original extract_documentation function.

    Extracts comprehensive documentation for APIs, websites, or services based on user query.
    This function uses advanced documentation extraction techniques to find and structure
    relevant API documentation, endpoints, code examples, and technical details.

    Args:
        query (str): The website, API name, or service to extract documentation for.
                    Can be a URL, service name (e.g., 'TMDB'), or descriptive request.

    Returns:
        dict: A structured dictionary containing:
            - status: "success" or "error"
            - documentation: The extracted documentation content (if successful)
            - source: Information about the documentation source
            - error_message: Error details (if unsuccessful)
    """
    try:
        # Call the original extract_documentation function
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


# Create a specialized documentation agent
doc_agent = Agent(
    name="doc_agent",
    model="gemini-2.0-flash",
    description="Provides API documentation details for websites and services.",
    instruction="Use the extract_documentation tool to answer API-related queries and documentation requests.",
    tools=[extract_documentation],
)
