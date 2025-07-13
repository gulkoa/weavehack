#!/usr/bin/env python3
"""
Demo: Python Functions to MCP Server Conversion

This demonstrates how to take any Python file with documented functions
and automatically convert it into both stdio and HTTP MCP servers.
"""

import os
import sys
from pathlib import Path

def demo_conversion():
    """Run a demonstration of the conversion process."""
    
    print("🔄 Python Functions → MCP Server Conversion Demo")
    print("=" * 55)
    
    print("\n📝 Step 1: You have a Python file with functions")
    print("   Example: example_weather_functions.py")
    print("   - Functions with docstrings")
    print("   - Type annotations (recommended)")
    print("   - Google/Sphinx style parameter documentation")
    
    print("\n🛠️  Step 2: Run the converter")
    print("   Command: python convert_to_mcp.py your_functions.py")
    print("   ")
    print("   Options:")
    print("   --output-dir DIR     # Output directory")
    print("   --http-only         # Generate only HTTP server") 
    print("   --stdio-only        # Generate only stdio server")
    
    print("\n📦 Step 3: Generated files")
    print("   ✅ your_functions_mcp_server.py        # stdio MCP server")
    print("   ✅ your_functions_http_mcp_server.py   # HTTP MCP server")
    print("   ✅ manifest.json                       # MCP manifest")
    
    print("\n🚀 Step 4: Deploy and use")
    print("   Local HTTP server: python your_functions_http_mcp_server.py")
    print("   Docker: docker build -t my-mcp-server .")
    print("   Cloud: Deploy to Fly.io, Heroku, etc.")
    
    print("\n🎯 What the converter extracts:")
    print("   - Function names → Tool names")
    print("   - Docstrings → Tool descriptions") 
    print("   - Parameters → Input schemas")
    print("   - Type hints → JSON schema types")
    print("   - Default values → Optional parameters")
    
    print("\n💡 Example input function:")
    print('''   def get_weather(lat: float, lon: float, days: int = 7) -> dict:
       """
       Get weather forecast for coordinates.
       
       Args:
           lat (float): Latitude coordinate
           lon (float): Longitude coordinate  
           days (int): Number of forecast days
           
       Returns:
           dict: Weather forecast data
       """
       # Your implementation here
       pass''')
    
    print("\n📋 Generated MCP tool:")
    print('''   {
       "name": "get_weather",
       "description": "Get weather forecast for coordinates.",
       "inputSchema": {
           "type": "object",
           "properties": {
               "lat": {"type": "number", "description": "Latitude coordinate"},
               "lon": {"type": "number", "description": "Longitude coordinate"},
               "days": {"type": "integer", "description": "Number of forecast days", "default": 7}
           },
           "required": ["lat", "lon"]
       }
   }''')
    
    print("\n🔗 Usage with AI agents:")
    print("   Once deployed, any AI can use your tools:")
    print('   tools=[{"type":"mcp","url":"https://your-server.com"}]')
    
    print("\n" + "=" * 55)
    print("✨ From Python functions to production MCP server in seconds!")

def check_generated_files():
    """Check what files were generated and their status."""
    
    generated_dir = Path("./generated")
    if not generated_dir.exists():
        print("❌ No generated directory found. Run the converter first!")
        return
    
    print("\n📁 Generated Files Status:")
    print("-" * 30)
    
    files_to_check = [
        "example_weather_functions_mcp_server.py",
        "example_weather_functions_http_mcp_server.py", 
        "manifest.json"
    ]
    
    for filename in files_to_check:
        filepath = generated_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"✅ {filename:<40} ({size:,} bytes)")
        else:
            print(f"❌ {filename:<40} (missing)")
    
    print(f"\n📊 Total files in generated/: {len(list(generated_dir.iterdir()))}")

if __name__ == "__main__":
    demo_conversion()
    check_generated_files()
    
    print("\n🚀 Next steps:")
    print("1. cd generated/")
    print("2. pip install mcp fastapi uvicorn requests")
    print("3. python example_weather_functions_http_mcp_server.py")
    print("4. Test: curl http://localhost:8080/")
