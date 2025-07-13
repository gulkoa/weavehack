import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from google.adk.models.anthropic_llm import Claude


root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-pro",
    description=(
        "Agent to orchestrate generation of MCP tools from API descriptions."
    ),
    instruction=(
        "You are a root agent that orchestrates the generation of MCP tools from API descriptions. "
    ),
)