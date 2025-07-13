#!/usr/bin/env python3
"""
Auto-generated MCP Server from example_weather_functions.py

This server exposes the functions from example_weather_functions as MCP tools.
"""

import asyncio
import json
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult

# Import the original functions
from example_weather_functions import get_weather_forecast, get_current_weather, search_locations, get_weather_alerts, calculate_weather_summary

# Initialize the MCP server
server = Server("example_weather_functions-mcp")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_weather_forecast",
            description="Get weather forecast for a specific location.",
            inputSchema={
            "type": "object",
            "properties": {
                        "latitude": {
                                    "type": "number",
                                    "description": "Latitude coordinate (-90 to 90)"
                        },
                        "longitude": {
                                    "type": "number",
                                    "description": "Longitude coordinate (-180 to 180)"
                        },
                        "days": {
                                    "type": "integer",
                                    "description": "Number of forecast days (1-16, default: 7)",
                                    "default": 7
                        }
            },
            "required": [
                        "latitude",
                        "longitude"
            ]
}
        ),
        Tool(
            name="get_current_weather",
            description="Get current weather conditions for a specific location.",
            inputSchema={
            "type": "object",
            "properties": {
                        "latitude": {
                                    "type": "number",
                                    "description": "Latitude coordinate"
                        },
                        "longitude": {
                                    "type": "number",
                                    "description": "Longitude coordinate"
                        }
            },
            "required": [
                        "latitude",
                        "longitude"
            ]
}
        ),
        Tool(
            name="search_locations",
            description="Search for locations by name to get coordinates.",
            inputSchema={
            "type": "object",
            "properties": {
                        "query": {
                                    "type": "string",
                                    "description": "Location name to search for (e.g., \"San Francisco\", \"London\")"
                        },
                        "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return (default: 10)",
                                    "default": 10
                        }
            },
            "required": [
                        "query"
            ]
}
        ),
        Tool(
            name="get_weather_alerts",
            description="Get weather alerts and warnings for a location.",
            inputSchema={
            "type": "object",
            "properties": {
                        "latitude": {
                                    "type": "number",
                                    "description": "Latitude coordinate"
                        },
                        "longitude": {
                                    "type": "number",
                                    "description": "Longitude coordinate"
                        }
            },
            "required": [
                        "latitude",
                        "longitude"
            ]
}
        ),
        Tool(
            name="calculate_weather_summary",
            description="Calculate a human-readable weather summary from raw weather data.",
            inputSchema={
            "type": "object",
            "properties": {
                        "weather_data": {
                                    "type": "string",
                                    "description": "Raw weather data from get_weather_forecast"
                        }
            },
            "required": [
                        "weather_data"
            ]
}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    if name not in ["get_weather_forecast", "get_current_weather", "search_locations", "get_weather_alerts", "calculate_weather_summary"]:
        raise ValueError(f"Unknown tool: {name}")
    
    elif name == "get_weather_forecast":
        latitude = arguments["latitude"]
        longitude = arguments["longitude"]
        days = arguments.get("days", 7)
        
        try:
            result = get_weather_forecast(latitude, longitude, days)
            if isinstance(result, dict):
                formatted_result = json.dumps(result, indent=2)
            else:
                formatted_result = str(result)
            return [TextContent(type="text", text=formatted_result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in get_weather_forecast: {str(e)}")]
    elif name == "get_current_weather":
        latitude = arguments["latitude"]
        longitude = arguments["longitude"]
        
        try:
            result = get_current_weather(latitude, longitude)
            if isinstance(result, dict):
                formatted_result = json.dumps(result, indent=2)
            else:
                formatted_result = str(result)
            return [TextContent(type="text", text=formatted_result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in get_current_weather: {str(e)}")]
    elif name == "search_locations":
        query = arguments["query"]
        max_results = arguments.get("max_results", 10)
        
        try:
            result = search_locations(query, max_results)
            if isinstance(result, dict):
                formatted_result = json.dumps(result, indent=2)
            else:
                formatted_result = str(result)
            return [TextContent(type="text", text=formatted_result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in search_locations: {str(e)}")]
    elif name == "get_weather_alerts":
        latitude = arguments["latitude"]
        longitude = arguments["longitude"]
        
        try:
            result = get_weather_alerts(latitude, longitude)
            if isinstance(result, dict):
                formatted_result = json.dumps(result, indent=2)
            else:
                formatted_result = str(result)
            return [TextContent(type="text", text=formatted_result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in get_weather_alerts: {str(e)}")]
    elif name == "calculate_weather_summary":
        weather_data = arguments["weather_data"]
        
        try:
            result = calculate_weather_summary(weather_data)
            if isinstance(result, dict):
                formatted_result = json.dumps(result, indent=2)
            else:
                formatted_result = str(result)
            return [TextContent(type="text", text=formatted_result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in calculate_weather_summary: {str(e)}")]

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
