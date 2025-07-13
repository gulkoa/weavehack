import asyncio
import os

from stagehand import Stagehand, StagehandConfig


async def main():
    # # Set up environment variables if not already set
    if not os.getenv("STAGEHAND_API_URL"):
        os.environ["STAGEHAND_API_URL"] = "https://api.stagehand.browserbase.com/v1"

    config = StagehandConfig(
        env=(
            "LOCAL"
            # if os.getenv("USE_LOCAL") == "true"
            # else (
            #     "BROWSERBASE"
            #     if os.getenv("BROWSERBASE_API_KEY")
            #     and os.getenv("BROWSERBASE_PROJECT_ID")
            #     else "LOCAL"
            # )
        ),
        # api_key=os.getenv("BROWSERBASE_API_KEY"),
        # project_id=os.getenv("BROWSERBASE_PROJECT_ID"),
        verbose=1,
        model_name="openai/gpt-4.1",
        model_api_key=os.getenv("OPENAI_API_KEY"),
        use_api=False,
    )

    # Initialize Stagehand with the API URL
    stagehand = Stagehand(config=config, model_api_key=os.getenv("OPENAI_API_KEY"))
    await stagehand.init()
    page = stagehand.page

    try:
        # Navigate to the documentation page
        await page.goto("https://pokeapi.co/docs/v2")

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

        print(documentation)

    finally:
        # Close the session
        await stagehand.close()


if __name__ == "__main__":
    asyncio.run(main())
