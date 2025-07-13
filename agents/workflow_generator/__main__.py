from a2a.cards.agent_card import AgentCapabilities, AgentCard
from a2a.server import start_server
from a2a.skills.skill_declarations import AgentSkill

from .task_manager import AgentTaskManager

# Define the agent's skill
skill = AgentSkill(
    id="WorkflowGenerator",
    name="Workflow_Generator_Agent",
    description="Agent to analyze REST API descriptions and generate logical workflows",
    tags=["api", "workflow", "analysis", "rest", "endpoints", "automation"],
    examples=[
        "Analyze this REST API description and generate workflows: {...}",
        "Generate workflows for GitHub API",
        "Analyze Stripe API and identify workflows",
        "validate: def api_call(): return response",
    ],
)


# Define the agent's card for discovery
def create_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="WorkflowGenerator",
        description="Agent designed to analyze REST API descriptions and generate logical workflows",
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
    port = 10002

    agent_card = create_agent_card(host, port)
    task_manager = AgentTaskManager()

    print(f"Starting Workflow Generator Agent at http://{host}:{port}/")
    start_server(task_manager, agent_card, host, port)
