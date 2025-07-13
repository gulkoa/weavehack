from typing import Dict

from google.adk.agents import Agent

from agents.doc_extrator import extract_documentation as original_extract_documentation


# # --- ADK-compatible wrapper ---
# def extract_documentation(query: str) -> Dict:
#     """
#     ADK-compatible wrapper for the original extract_documentation function.

#     Args:
#         query (str): The website, API name, or service.

#     Returns:
#         dict: Structured response with status, documentation, and errors.
#     """
#     try:
#         result = original_extract_documentation(query)
#         return {
#             "status": "success",
#             "documentation": str(result),
#             "source": f"Documentation extracted for: {query}",
#             "query": query,
#         }
#     except Exception as e:
#         return {
#             "status": "error",
#             "error_message": f"Failed to extract documentation: {str(e)}",
#             "query": query,
#         }


# --- Define the ADK Agent ---
root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-pro",
    description="Provides API documentation details for websites and services.",
    instruction="Use the extract_documentation tool to answer API-related queries and documentation requests.",
    tools=[],
)
