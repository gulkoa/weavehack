#!/usr/bin/env python3
"""
Weather Plugin for Modular MCP Server

This plugin provides weather-related functionality using the Open-Meteo API.
Functions in this file will be automatically discovered and loaded by the MCP server.
"""

import requests
import json
from typing import Dict, List, Optional, Any
import datetime


def get_weather_forecast(latitude: float, longitude: float, days: int = 7) -> Dict[str, Any]:
    """
    Get weather forecast for a specific location.
    
    This function fetches weather data from Open-Meteo API for the given coordinates.
    It returns current conditions, hourly forecasts, and daily forecasts.
    
    Args:
        latitude (float): Latitude coordinate (-90 to 90)
        longitude (float): Longitude coordinate (-180 to 180)  
        days (int): Number of forecast days (1-16, default: 7)
        
    Returns:
        dict: Weather forecast data including current, hourly, and daily forecasts
        
    Example:
        >>> forecast = get_weather_forecast(37.7749, -122.4194, 5)
        >>> print(forecast['current']['temperature_2m'])
        18.5
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "hourly": "temperature_2m,precipitation_probability,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
        "timezone": "auto",
        "forecast_days": min(days, 16)
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def get_current_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Get current weather conditions for a specific location.
    
    This is a simplified version that only returns current weather data
    without forecasts.
    
    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate
        
    Returns:
        dict: Current weather conditions
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,apparent_temperature",
        "timezone": "auto"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    return {
        "location": {
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "timezone": data["timezone"]
        },
        "current": data["current"],
        "timestamp": datetime.datetime.now().isoformat()
    }


def search_locations(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search for locations by name to get coordinates.
    
    Uses the geocoding API to find locations matching the search query.
    Useful for converting city names to coordinates.
    
    Args:
        query (str): Location name to search for (e.g., "San Francisco", "London")
        max_results (int): Maximum number of results to return (default: 10)
        
    Returns:
        list: List of location dictionaries with name, coordinates, and details
        
    Example:
        >>> locations = search_locations("San Francisco")
        >>> print(locations[0]['name'], locations[0]['latitude'])
        San Francisco 37.7749
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": query,
        "count": max_results,
        "language": "en",
        "format": "json"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    return data.get("results", [])


def calculate_weather_summary(weather_data: Dict[str, Any]) -> str:
    """
    Calculate a human-readable weather summary from raw weather data.
    
    Takes the output from get_weather_forecast and creates a natural
    language summary suitable for display.
    
    Args:
        weather_data (dict): Raw weather data from get_weather_forecast
        
    Returns:
        str: Human-readable weather summary
    """
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})
    
    summary = f"Current temperature: {current.get('temperature_2m', 'N/A')}°C\n"
    summary += f"Humidity: {current.get('relative_humidity_2m', 'N/A')}%\n"
    summary += f"Wind speed: {current.get('wind_speed_10m', 'N/A')} km/h\n"
    
    if daily and "time" in daily:
        summary += "\nUpcoming forecast:\n"
        times = daily["time"][:3]  # Next 3 days
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        
        for i, date in enumerate(times):
            if i < len(max_temps) and i < len(min_temps):
                summary += f"  {date}: {min_temps[i]}°C - {max_temps[i]}°C\n"
    
    return summary
