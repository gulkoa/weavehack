# Auto-generated Dockerfile for MCP servers
# Created by convert_to_mcp.py

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the original functions module
COPY ../example_weather_functions.py ./example_weather_functions.py

# Copy the generated MCP servers
COPY example_weather_functions_http_mcp_server.py .
COPY example_weather_functions_mcp_server.py .
COPY manifest.json .

# Expose port for HTTP server
EXPOSE 8080

# Default to running the HTTP server
CMD ["python", "example_weather_functions_http_mcp_server.py"]

# Alternative commands:
# For stdio server: CMD ["python", "example_weather_functions_mcp_server.py"]
