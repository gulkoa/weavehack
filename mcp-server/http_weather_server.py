#!/usr/bin/env python3
"""
HTTP Weather MCP Server

A FastAPI-based HTTP server that provides weather forecast tools using the Open-Meteo API.
This server exposes MCP functionality over HTTP for easy deployment and consumption.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import json
from typing import Any, Dict, Optional
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="Weather MCP Server",
    description="MCP server for weather forecast data via Open-Meteo API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ForecastRequest(BaseModel):
    latitude: float
    longitude: float
    current: Optional[str] = "temperature_2m,relative_humidity_2m,wind_speed_10m"
    hourly: Optional[str] = "temperature_2m,precipitation_probability"
    daily: Optional[str] = "temperature_2m_max,temperature_2m_min,precipitation_sum"
    timezone: Optional[str] = "auto"

class MCPManifest(BaseModel):
    schema_version: str = "1.0"
    name: str = "weather-mcp"
    description: str = "Weather forecast MCP server"
    version: str = "1.0.0"
    tools: list = []

@app.get("/")
async def get_manifest():
    """Serve the MCP manifest at the root endpoint."""
    manifest = {
        "schema_version": "1.0",
        "name": "weather-mcp",
        "description": "Weather forecast MCP server using Open-Meteo API",
        "version": "1.0.0",
        "tools": [
            {
                "name": "get_forecast",
                "description": "Get weather forecast for a specific location",
                "inputSchema": {
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
            }
        ]
    }
    return JSONResponse(content=manifest)

@app.get("/manifest.json")
async def get_manifest_json():
    """Alternative endpoint for the manifest."""
    return await get_manifest()

@app.post("/get_forecast")
async def get_forecast(request: ForecastRequest):
    """Get weather forecast for a specific location."""
    
    # Prepare API request to Open-Meteo
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": request.latitude,
        "longitude": request.longitude,
        "current": request.current,
        "hourly": request.hourly,
        "daily": request.daily,
        "timezone": request.timezone
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            weather_data = response.json()
            
            # Format the response for MCP consumption
            result = {
                "location": {
                    "latitude": weather_data.get("latitude"),
                    "longitude": weather_data.get("longitude"),
                    "timezone": weather_data.get("timezone"),
                    "elevation": weather_data.get("elevation")
                },
                "current": weather_data.get("current", {}),
                "hourly": weather_data.get("hourly", {}),
                "daily": weather_data.get("daily", {}),
                "summary": format_weather_summary(weather_data, request.latitude, request.longitude)
            }
            
            return JSONResponse(content=result)
            
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP error occurred: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather data: {str(e)}")

def format_weather_summary(weather_data: dict, latitude: float, longitude: float) -> str:
    """Format weather data into a human-readable summary."""
    result = f"Weather Forecast for ({latitude}, {longitude}):\n\n"
    
    # Current Weather
    if "current" in weather_data:
        result += "Current Weather:\n"
        current_data = weather_data["current"]
        for key, value in current_data.items():
            if key != "time":
                result += f"  {key}: {value}\n"
        result += "\n"
    
    # Location Details
    result += "Location Details:\n"
    result += f"  Timezone: {weather_data.get('timezone', 'Unknown')}\n"
    result += f"  Elevation: {weather_data.get('elevation', 'Unknown')} m\n\n"
    
    # Daily Forecast
    if "daily" in weather_data and weather_data["daily"]:
        result += "Daily Forecast (next 7 days):\n"
        daily_data = weather_data["daily"]
        times = daily_data.get("time", [])
        for i, date in enumerate(times[:7]):
            result += f"  {date}:\n"
            for key, values in daily_data.items():
                if key != "time" and i < len(values):
                    result += f"    {key}: {values[i]}\n"
    
    return result

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "weather-mcp"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
