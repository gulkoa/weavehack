# Stage 1: Builder stage
FROM python:3.12-slim AS builder

# Install uv
RUN pip install uv

# Install dependencies
COPY pyproject.toml .
RUN uv sync

# Stage 2: Final stage
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Expose port and set command
EXPOSE 8000
CMD ["uv", "run", "fastmcp", "run", "main.py", "--host", "0.0.0.0", "--port", "8000", "--transport", "http"]