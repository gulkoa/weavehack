#!/usr/bin/env python3
"""
Start script for the Weather MCP HTTP Server
"""

import uvicorn
from http_weather_server import app

if __name__ == "__main__":
    print("Starting Weather MCP HTTP Server...")
    print("Server will be available at: http://localhost:8080")
    print("Manifest endpoint: http://localhost:8080/")
    print("Forecast endpoint: http://localhost:8080/get_forecast")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8080,
        log_level="info"
    )
