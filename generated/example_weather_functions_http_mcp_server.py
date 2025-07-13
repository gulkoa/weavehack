#!/usr/bin/env python3
"""
Auto-generated HTTP MCP Server from example_weather_functions.py

This FastAPI server exposes the functions from example_weather_functions as HTTP endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
from pydantic import BaseModel
import json

# Import the original functions
from example_weather_functions import get_weather_forecast, get_current_weather, search_locations, get_weather_alerts, calculate_weather_summary

# Initialize FastAPI app
app = FastAPI(
    title="Example_Weather_Functions MCP Server",
    description="Auto-generated MCP server",
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

class GetWeatherForecastRequest(BaseModel):
    latitude: float
    longitude: float
    days: Optional[int] = 7


class GetCurrentWeatherRequest(BaseModel):
    latitude: float
    longitude: float


class SearchLocationsRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10


class GetWeatherAlertsRequest(BaseModel):
    latitude: float
    longitude: float


class CalculateWeatherSummaryRequest(BaseModel):
    weather_data: str

@app.get("/")
async def get_manifest():
    """Serve the MCP manifest."""
    manifest = {
    "schema_version": "1.0",
    "name": "example_weather_functions-mcp",
    "description": "Auto-generated MCP server from example_weather_functions",
    "version": "1.0.0",
    "tools": [
        {
            "name": "get_weather_forecast",
            "description": "Get weather forecast for a specific location.",
            "inputSchema": {
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
        },
        {
            "name": "get_current_weather",
            "description": "Get current weather conditions for a specific location.",
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
                    }
                },
                "required": [
                    "latitude",
                    "longitude"
                ]
            }
        },
        {
            "name": "search_locations",
            "description": "Search for locations by name to get coordinates.",
            "inputSchema": {
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
        },
        {
            "name": "get_weather_alerts",
            "description": "Get weather alerts and warnings for a location.",
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
                    }
                },
                "required": [
                    "latitude",
                    "longitude"
                ]
            }
        },
        {
            "name": "calculate_weather_summary",
            "description": "Calculate a human-readable weather summary from raw weather data.",
            "inputSchema": {
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
        }
    ]
}
    return JSONResponse(content=manifest)

@app.get("/manifest.json")
async def get_manifest_json():
    """Alternative manifest endpoint."""
    return await get_manifest()

@app.post("/get_weather_forecast")
async def get_weather_forecast_endpoint(request: GetWeatherForecastRequest):
    """Get weather forecast for a specific location."""
    try:
        result = get_weather_forecast(request.latitude, request.longitude, request.days)
        return JSONResponse(content={"result": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in get_weather_forecast: {str(e)}")


@app.post("/get_current_weather")
async def get_current_weather_endpoint(request: GetCurrentWeatherRequest):
    """Get current weather conditions for a specific location."""
    try:
        result = get_current_weather(request.latitude, request.longitude)
        return JSONResponse(content={"result": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in get_current_weather: {str(e)}")


@app.post("/search_locations")
async def search_locations_endpoint(request: SearchLocationsRequest):
    """Search for locations by name to get coordinates."""
    try:
        result = search_locations(request.query, request.max_results)
        return JSONResponse(content={"result": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in search_locations: {str(e)}")


@app.post("/get_weather_alerts")
async def get_weather_alerts_endpoint(request: GetWeatherAlertsRequest):
    """Get weather alerts and warnings for a location."""
    try:
        result = get_weather_alerts(request.latitude, request.longitude)
        return JSONResponse(content={"result": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in get_weather_alerts: {str(e)}")


@app.post("/calculate_weather_summary")
async def calculate_weather_summary_endpoint(request: CalculateWeatherSummaryRequest):
    """Calculate a human-readable weather summary from raw weather data."""
    try:
        result = calculate_weather_summary(request.weather_data)
        return JSONResponse(content={"result": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in calculate_weather_summary: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": f"{app.title}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
