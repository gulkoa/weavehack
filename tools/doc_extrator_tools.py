import asyncio
import os
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from stagehand import StagehandConfig
from stagehand.client import Stagehand

from lib.exa import exa


class DocumentationScraperInput(BaseModel):
    url: str = Field(..., description="The URL of the documentation to scrape")


class LinkDocumentationScraper(BaseTool):
    name: str = "link_documentation_scraper"
    description: str = (
        "Given a URL, scrape comprehensive API documentation including all endpoints, parameters, authentication, and detailed descriptions"
    )
    args_schema: Type[BaseModel] = DocumentationScraperInput

    async def _run(self, url: str) -> str:
        try:
            # Configure Stagehand
            config = StagehandConfig(
                env=(
                    "LOCAL"
                    if os.getenv("USE_LOCAL") == "true"
                    else (
                        "BROWSERBASE"
                        if os.getenv("BROWSERBASE_API_KEY")
                        and os.getenv("BROWSERBASE_PROJECT_ID")
                        else "LOCAL"
                    )
                ),
                api_key=os.getenv("BROWSERBASE_API_KEY"),
                project_id=os.getenv("BROWSERBASE_PROJECT_ID"),
                model_name="openai/gpt-4.1",
                model_api_key=os.getenv("OPENAI_API_KEY"),
                verbose=1,
                use_api=False,
            )

            # Initialize Stagehand
            stagehand = Stagehand(
                config=config,
                server_url=os.getenv("STAGEHAND_API_URL"),
            )
            await stagehand.init()
            page = stagehand.page

            # Navigate to the documentation page
            await page.goto(url)

            # Wait for page to load and settle
            await page.wait_for_load_state("networkidle")

            # Extract comprehensive API documentation
            documentation = await page.extract(
                f"""
            Extract comprehensive API documentation from this page. Focus on:
            
            1. **All API Endpoints**: List every endpoint/route available
            2. **HTTP Methods**: GET, POST, PUT, DELETE, etc. for each endpoint
            3. **Parameters**: For each endpoint, extract:
               - Required parameters (mark as REQUIRED)
               - Optional parameters (mark as OPTIONAL)
               - Parameter types (string, integer, boolean, etc.)
               - Parameter descriptions
               - Default values if specified
            4. **Authentication**: 
               - Authentication methods (API keys, OAuth, Bearer tokens, etc.)
               - How to include auth in requests
               - Auth token formats
            5. **Request/Response Examples**: 
               - Example request bodies
               - Example response formats
               - Status codes
            6. **Rate Limits**: Any mentioned rate limiting information
            7. **Base URLs**: API base URLs and versions
            8. **Error Handling**: Common error responses and codes
            
            Format the output as structured text with clear sections and bullet points.
            Be comprehensive and include all technical details found on the page.
            """
            )

            # Also try to navigate to common API documentation sections
            try:
                # Look for API reference, endpoints, or similar sections
                api_sections = await page.observe(
                    "find links or sections related to API, endpoints, reference, or developer documentation"
                )
                if api_sections:
                    additional_docs = []
                    for section in api_sections[
                        :3
                    ]:  # Limit to first 3 sections to avoid too much data
                        try:
                            await page.act(section)
                            await page.wait_for_load_state("networkidle")
                            section_docs = await page.extract(
                                "Extract all API endpoints, parameters, and technical details from this section"
                            )
                            additional_docs.append(section_docs)
                        except Exception as e:
                            print(f"Error extracting from section: {e}")

                    if additional_docs:
                        documentation += (
                            "\n\n=== ADDITIONAL API SECTIONS ===\n\n"
                            + "\n\n".join(additional_docs)
                        )

            except Exception as e:
                print(f"Error navigating additional sections: {e}")

            # Close the session
            await stagehand.close()

            return str(documentation)

        except Exception as e:
            print(f"Error with Stagehand extraction: {e}")

    async def _arun(self, url: str) -> str:
        return await self._run(url)

    def _run(self, url: str) -> str:
        return asyncio.run(self._arun(url))


class DocumentationExtractorInput(BaseModel):
    text: str = Field(
        ...,
        description="A description of the documentation to extract (along with the web site link)",
    )


class TextDocumentationExtractor(BaseTool):
    name: str = "text_documentation_extractor"
    description: str = (
        "Given a description of the documentation to extract (along with the web site link), go to the web site and extract the documentation"
    )
    args_schema: Type[BaseModel] = DocumentationExtractorInput

    def _run(self, text: str) -> str:
        # return exa.extract_text(text)
        result = exa.search_and_contents(
            text,
            text=True,
            num_results=1,
            summary={
                "query": "Extract comprehensive API documentation from this page. Focus on:\n            \n            1. **All API Endpoints**: List every endpoint/route available\n            2. **HTTP Methods**: GET, POST, PUT, DELETE, etc. for each endpoint\n            3. **Parameters**: For each endpoint, extract:\n               - Required parameters (mark as REQUIRED)\n               - Optional parameters (mark as OPTIONAL)\n               - Parameter types (string, integer, boolean, etc.)\n               - Parameter descriptions\n               - Default values if specified\n            4. **Authentication**: \n               - Authentication methods (API keys, OAuth, Bearer tokens, etc.)\n               - How to include auth in requests\n               - Auth token formats\n            5. **Request/Response Examples**: \n               - Example request bodies\n               - Example response formats\n               - Status codes\n            6. **Rate Limits**: Any mentioned rate limiting information\n            7. **Base URLs**: API base URLs and versions\n            8. **Error Handling**: Common error responses and codes\n            \n            Format the output as structured text with clear sections and bullet points.\n            Be comprehensive and include all technical details found on the page."
            },
        )

        return str(result)

    def _arun(self, text: str) -> str:
        return self._run(text)
