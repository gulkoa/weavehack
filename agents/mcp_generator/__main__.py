from a2a.cards.agent_card import AgentCapabilities, AgentCard
from a2a.server import start_server
from a2a.skills.skill_declarations import AgentSkill

from .task_manager import AgentTaskManager

# Define the agent's skill
skill = AgentSkill(
    id="MCPGenerator",
    name="MCP_Generator_Agent",
    description="Agent to generate Python MCP tool code from workflow analysis using LLM",
    tags=["mcp", "python", "code", "generation", "tools", "workflow", "automation"],
    examples=[
        "Generate MCP tools from this workflow analysis: {...}",
        "Create MCP tools for REST API workflow",
        "Generate Python MCP code for authentication workflow",
        "validate: def my_function(): pass",
    ],
)


# Define the agent's card for discovery
def create_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="MCPGenerator",
        description="Agent designed to generate Python MCP tool code from workflow analysis using LLM",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
        supportsAuthenticatedExtendedCard=True,
    )


if __name__ == "__main__":
    host = "localhost"
    port = 10003

    agent_card = create_agent_card(host, port)
    task_manager = AgentTaskManager()

    print(f"Starting MCP Generator Agent at http://{host}:{port}/")
    start_server(task_manager, agent_card, host, port)
