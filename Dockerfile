FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the modular server and plugins
COPY modular_mcp_server.py .
COPY convert_to_mcp.py .
COPY plugins/ ./plugins/
COPY manifest.json .
COPY clean-spec.yaml .

# Expose port for HTTP access
EXPOSE 8080

# Run the modular MCP server
CMD ["python", "modular_mcp_server.py"]
