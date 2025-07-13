# Weather MCP HTTP Server

A Model Context Protocol (MCP) server that provides weather forecast tools using the Open-Meteo API. This server exposes MCP functionality over HTTP for easy deployment and consumption by AI agents.

## Features

- **HTTP-based MCP Server**: Easy to deploy and consume
- **Weather Forecasting**: Get current, hourly, and daily weather forecasts
- **Open-Meteo Integration**: Uses the free Open-Meteo API (no API key required)
- **Docker Support**: Ready for containerized deployment
- **CORS Enabled**: Can be consumed by web applications

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server:**
   ```bash
   python start_server.py
   ```

3. **Test the server:**
   ```bash
   # Get the manifest
   curl http://localhost:8080/

   # Get weather forecast for San Francisco
   curl -X POST http://localhost:8080/get_forecast \
        -H "Content-Type: application/json" \
        -d '{"latitude":37.8,"longitude":-122.4}'
   ```

### Docker Deployment

1. **Build the image:**
   ```bash
   docker build -t weather-mcp .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8080:8080 weather-mcp
   ```

## API Endpoints

### GET `/` or `/manifest.json`
Returns the MCP manifest describing available tools.

### POST `/get_forecast`
Get weather forecast for a specific location.

**Request Body:**
```json
{
  "latitude": 37.8,
  "longitude": -122.4,
  "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
  "hourly": "temperature_2m,precipitation_probability",
  "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
  "timezone": "auto"
}
```

**Response:**
```json
{
  "location": {
    "latitude": 37.763283,
    "longitude": -122.41286,
    "timezone": "America/Los_Angeles",
    "elevation": 7.0
  },
  "current": { ... },
  "hourly": { ... },
  "daily": { ... },
  "summary": "Human-readable weather summary..."
}
```

### GET `/health`
Health check endpoint.

## Deployment Options

### Fly.io Deployment

1. **Install Fly CLI:** https://fly.io/docs/hands-on/install-flyctl/

2. **Deploy:**
   ```bash
   fly launch --name weather-mcp --region lax --dockerfile ./Dockerfile
   ```

3. **Test the deployed service:**
   ```bash
   curl https://weather-mcp.fly.dev/
   curl -X POST https://weather-mcp.fly.dev/get_forecast \
        -H "Content-Type: application/json" \
        -d '{"latitude":37.8,"longitude":-122.4}'
   ```

### Other Deployment Platforms

- **Heroku**: Use the included `Dockerfile`
- **Railway**: Connect your GitHub repo
- **Google Cloud Run**: Deploy the container image
- **AWS ECS/Fargate**: Deploy the container image

## Usage with AI Agents

Once deployed, you can use this MCP server with AI agents:

```python
# Example with Claude
client.messages.create(
    model="claude-3-opus-20240229",
    anthropic_beta="mcp-client-2025-04-04",
    tools=[{"type":"mcp","url":"https://your-deployed-url.com"}],
    messages=[{"role":"user","content":"What's the weather forecast for New York City?"}]
)
```

## Files

- `http_weather_server.py` - Main HTTP server implementation
- `weather_server.py` - Original stdio-based MCP server
- `start_server.py` - Convenient startup script
- `clean-spec.yaml` - OpenAPI specification
- `manifest.json` - MCP manifest
- `Dockerfile` - Container configuration
- `requirements.txt` - Python dependencies

## License

This project is open source. The Open-Meteo API is free for non-commercial use.
