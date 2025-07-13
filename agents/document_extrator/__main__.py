from a2a.server import start_server  # TODO: Fix this
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from .task_manager import AgentTaskManager

# Define the agent's skill
skill = AgentSkill(
    id="DocumentationExtractor",
    name="Documentation_Extractor_Agent",
    description="Agent to extract comprehensive API documentation from websites and services using CrewAI",
    tags=[
        "documentation",
        "api",
        "extraction",
        "web-scraping",
        "crewai",
        "technical-docs",
    ],
    examples=[
        "Extract documentation for: https://api.example.com/docs",
        "Get API documentation for Stripe payments",
        "Extract documentation from OpenAI API",
        "Find API docs for GitHub REST API",
    ],
)


# Define the agent's card for discovery
def create_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="DocumentationExtractor",
        description="Agent designed to extract comprehensive API documentation from websites and services using CrewAI",
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
    port = 10001

    agent_card = create_agent_card(host, port)
    task_manager = AgentTaskManager()

    print(f"Starting Documentation Extractor Agent at http://{host}:{port}/")
    start_server(task_manager, agent_card, host, port)
