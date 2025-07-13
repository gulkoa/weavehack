from dotenv import load_dotenv

load_dotenv()

import os

# import weave
from crewai import LLM, Agent, Crew, Task

from tools.doc_extrator_tools import (
    LinkDocumentationScraper,
    TextDocumentationExtractor,
)

# weave.init("rochan-hm-self/quickstart_playground")
# client = openai.OpenAI(
#     base_url="https://api.inference.wandb.ai/v1",
#     api_key=os.getenv("WANDB_OPENAI_API_KEY"),
#     project="rochan-hm-self/quickstart_playground",
# )

llm = LLM(
    model="openai/gpt-4.1",
    timeout=100,
    api_base="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
# llm = LLM(
#     model="openai/deepseek-ai/DeepSeek-V3-0324",
#     api_base="https://api.inference.wandb.ai/v1",
#     timeout=1000,
#     api_key=os.getenv("WANDB_OPENAI_API_KEY"),
#     extra_headers={"OpenAI-Project": "gulkoa/my_project_name"},
# )

# Setup the agent
agent = Agent(
    role="Smart Documentation Extractor",
    goal="Analyze the user input and extract relevant documentation using the most appropriate method",
    backstory="""You are an intelligent documentation extractor agent. You have two tools available, and you should use them in the following priority order:

1. PRIMARY METHOD: Always start with the text_documentation_extractor tool first, regardless of whether the user provides a URL or descriptive request. This tool can search for and extract documentation from various sources.

2. FALLBACK METHOD: Only use the link_documentation_scraper tool if the text_documentation_extractor fails to find the required documentation or returns insufficient results.

Your job is to:
- Always attempt to use text_documentation_extractor first for any request
- Only fall back to link_documentation_scraper if the primary method fails
- Extract comprehensive documentation that matches the user's needs
- Focus on APIs, endpoints, code examples, and technical documentation when requested
- Provide clear reasoning if you need to use the fallback method""",
    verbose=True,
    tools=[LinkDocumentationScraper(), TextDocumentationExtractor()],
    llm=llm,
)


def extract_documentation(user_input: str) -> dict:
    task = Task(
        description="""Analyze this user request and extract the relevant documentation: "{user_input}"

Instructions:
- ALWAYS start with the text_documentation_extractor tool first, regardless of input type
- Only use the link_documentation_scraper tool if the text_documentation_extractor fails or returns insufficient results
- Focus on extracting APIs, endpoints, code examples, and technical details when relevant
- Provide comprehensive and well-structured documentation output
- If you need to use the fallback method, explain why the primary method didn't work""",
        expected_output="Comprehensive documentation extracted from the specified source, formatted clearly with relevant technical details, APIs, and examples",
        agent=agent,
    )
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
    )
    result = crew.kickoff({"user_input": user_input})
    return {
        "status": "success",
        "documentation": str(result),
        "errors": []
    }


if __name__ == "__main__":
    inp = input("Enter the input: ")
    print(extract_documentation(inp))
