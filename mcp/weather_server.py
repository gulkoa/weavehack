#!/usr/bin/env python3
"""
Weather MCP Server

An MCP server that provides weather forecast tools using the Open-Meteo API.
"""

import asyncio
import httpx
from typing import Any, Dict, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, 
    Tool, 
    TextContent, 
    CallToolRequest,
    CallToolResult
)

# Initialize the MCP server
server = Server("weather-mcp")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_forecast",
            description="Get weather forecast for a specific location",
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
                    },
                    "current": {
                        "type": "string",
                        "description": "Current weather variables (comma-separated)",
                        "default": "temperature_2m,relative_humidity_2m,wind_speed_10m"
                    },
                    "hourly": {
                        "type": "string",
                        "description": "Hourly weather variables (comma-separated)",
                        "default": "temperature_2m,precipitation_probability"
                    },
                    "daily": {
                        "type": "string", 
                        "description": "Daily weather variables (comma-separated)",
                        "default": "temperature_2m_max,temperature_2m_min,precipitation_sum"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone for the forecast",
                        "default": "auto"
                    }
                },
                "required": ["latitude", "longitude"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    if name != "get_forecast":
        raise ValueError(f"Unknown tool: {name}")
    
    # Extract parameters
    latitude = arguments["latitude"]
    longitude = arguments["longitude"]
    current = arguments.get("current", "temperature_2m,relative_humidity_2m,wind_speed_10m")
    hourly = arguments.get("hourly", "temperature_2m,precipitation_probability")
    daily = arguments.get("daily", "temperature_2m_max,temperature_2m_min,precipitation_sum")
    timezone = arguments.get("timezone", "auto")
    
    # Prepare API request
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": current,
        "hourly": hourly,
        "daily": daily,
        "timezone": timezone
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            weather_data = response.json()
            
            # Format the response
            result = f"""Weather Forecast for ({latitude}, {longitude}):

Current Weather:
"""
            if "current" in weather_data:
                current_data = weather_data["current"]
                for key, value in current_data.items():
                    if key != "time":
                        result += f"  {key}: {value}\n"
            
            result += "\nLocation Details:\n"
            result += f"  Timezone: {weather_data.get('timezone', 'Unknown')}\n"
            result += f"  Elevation: {weather_data.get('elevation', 'Unknown')} m\n"
            
            if "daily" in weather_data and weather_data["daily"]:
                result += "\nDaily Forecast (next 7 days):\n"
                daily_data = weather_data["daily"]
                times = daily_data.get("time", [])
                for i, date in enumerate(times[:7]):
                    result += f"  {date}:\n"
                    for key, values in daily_data.items():
                        if key != "time" and i < len(values):
                            result += f"    {key}: {values[i]}\n"
            
            return [TextContent(type="text", text=result)]
            
    except httpx.HTTPError as e:
        error_msg = f"HTTP error occurred: {str(e)}"
        return [TextContent(type="text", text=error_msg)]
    except Exception as e:
        error_msg = f"Error fetching weather data: {str(e)}"
        return [TextContent(type="text", text=error_msg)]

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
