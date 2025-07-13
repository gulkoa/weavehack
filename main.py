from lib.exa import exa


def main():
    result = exa.search_and_contents(
        "Get me paypal API docs for orders",
        text=True,
        num_results=1,
        summary={
            "query": "Extract comprehensive API documentation from this page. Focus on:\n            \n            1. **All API Endpoints**: List every endpoint/route available\n            2. **HTTP Methods**: GET, POST, PUT, DELETE, etc. for each endpoint\n            3. **Parameters**: For each endpoint, extract:\n               - Required parameters (mark as REQUIRED)\n               - Optional parameters (mark as OPTIONAL)\n               - Parameter types (string, integer, boolean, etc.)\n               - Parameter descriptions\n               - Default values if specified\n            4. **Authentication**: \n               - Authentication methods (API keys, OAuth, Bearer tokens, etc.)\n               - How to include auth in requests\n               - Auth token formats\n            5. **Request/Response Examples**: \n               - Example request bodies\n               - Example response formats\n               - Status codes\n            6. **Rate Limits**: Any mentioned rate limiting information\n            7. **Base URLs**: API base URLs and versions\n            8. **Error Handling**: Common error responses and codes\n            \n            Format the output as structured text with clear sections and bullet points.\n            Be comprehensive and include all technical details found on the page."
        },
    )
    with open("exa_result.txt", "w") as f:
        f.write(str(result))


if __name__ == "__main__":
    main()
