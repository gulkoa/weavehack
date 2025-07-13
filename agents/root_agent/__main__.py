from a2a.cards.agent_card import AgentCapabilities, AgentCard
from a2a.server import start_server
from a2a.skills.skill_declarations import AgentSkill

from .task_manager import AgentTaskManager

# Define the agent's skills
orchestration_skill = AgentSkill(
    id="AgentOrchestration",
    name="Agent_Orchestration",
    description="Coordinate and route requests between different specialized agents",
    tags=["orchestration", "coordination", "routing", "multi-agent", "delegation"],
    examples=[
        "List all available agents",
        "Extract documentation for GitHub API",
        "Generate workflows for Stripe API then create MCP tools",
        "What agents are available to help with API analysis?",
    ],
)

documentation_skill = AgentSkill(
    id="DirectDocumentationExtraction",
    name="Direct_Documentation_Extraction",
    description="Extract API documentation directly using CrewAI",
    tags=["documentation", "api", "extraction", "direct", "crewai"],
    examples=[
        "Extract documentation for: https://api.example.com/docs",
        "Get API documentation for OpenAI",
        "Extract docs from REST API endpoint",
    ],
)


# Define the agent's card for discovery
def create_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="RootOrchestrator",
        description="Main coordination agent that can route requests to other specialized agents and provide general assistance",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[orchestration_skill, documentation_skill],
        supportsAuthenticatedExtendedCard=True,
    )


if __name__ == "__main__":
    host = "localhost"
    port = 10000

    agent_card = create_agent_card(host, port)
    task_manager = AgentTaskManager()

    print(f"Starting Root Orchestrator Agent at http://{host}:{port}/")
    start_server(task_manager, agent_card, host, port)
