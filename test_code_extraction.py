#!/usr/bin/env python3
"""Test script to verify code extraction from agent responses"""

import re

def test_code_extraction():
    """Test different response formats to ensure code extraction works"""
    
    # Test case 1: Code in markdown code block
    response1 = """Here's your MCP server implementation:

```python
import mcp
from mcp.server import Server
from mcp.types import Tool

class APIServer(Server):
    def __init__(self):
        super().__init__("api-server")
        
    @tool()
    async def fetch_data(self, endpoint: str) -> str:
        # Implementation here
        return f"Data from {endpoint}"

if __name__ == "__main__":
    server = APIServer()
    server.run()
```

This server provides basic API integration.
"""
    
    # Test case 2: Direct code without markdown
    response2 = """import mcp
from mcp.server import Server

class SimpleServer(Server):
    def __init__(self):
        super().__init__("simple-server")

server = SimpleServer()
server.run()"""
    
    # Test case 3: Response with filename
    response3 = """filename: weather_api_mcp.py

Here's your MCP server:

```python
import mcp
import requests

class WeatherMCPServer:
    def get_weather(self, city):
        return requests.get(f"api.weather.com/{city}")
```
"""
    
    print("Testing code extraction patterns...")
    
    # Test extraction function
    def extract_code(text):
        # Try to extract code between ```python and ``` markers
        code_match = re.search(r'```python\n([\s\S]*?)```', text)
        if code_match:
            return code_match.group(1).strip()
        
        # If no code blocks found, check if the entire text is code
        if 'import ' in text or 'def ' in text or 'class ' in text:
            # Remove any non-code lines (like "filename:" lines)
            lines = text.split('\n')
            code_lines = []
            for line in lines:
                if not line.strip().startswith('filename:') and not line.strip().endswith(':'):
                    code_lines.append(line)
            return '\n'.join(code_lines).strip()
        
        return ""
    
    def extract_filename(text):
        filename_match = re.search(r'filename:\s*([^\n]+)', text, re.IGNORECASE)
        if filename_match:
            return filename_match.group(1).strip()
        return "mcp_server.py"
    
    # Test case 1
    code1 = extract_code(response1)
    print("\nTest 1 - Markdown code block:")
    print(f"Extracted: {len(code1)} characters")
    print(f"First line: {code1.split(chr(10))[0] if code1 else 'None'}")
    
    # Test case 2
    code2 = extract_code(response2)
    print("\nTest 2 - Direct code:")
    print(f"Extracted: {len(code2)} characters")
    print(f"First line: {code2.split(chr(10))[0] if code2 else 'None'}")
    
    # Test case 3
    code3 = extract_code(response3)
    filename3 = extract_filename(response3)
    print("\nTest 3 - With filename:")
    print(f"Filename: {filename3}")
    print(f"Extracted: {len(code3)} characters")
    print(f"First line: {code3.split(chr(10))[0] if code3 else 'None'}")
    
    print("\n✅ All extraction tests completed!")

if __name__ == "__main__":
    test_code_extraction()