import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from google.adk.models.anthropic_llm import Claude


root_agent = Agent(
    name="root_agent",
    model=Claude(model="claude-sonnet-4-20250514"),
    description=(
        "Agent to orchestrate generation of MCP tools from API descriptions."
    ),
    instruction=(
        "You are a root agent that orchestrates the generation of MCP tools from API descriptions. "
    ),
)