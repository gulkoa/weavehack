from .agent import MCPCodeGeneratorAgent, mcp_agent

# Export both the A2A server and the ADK agent for backward compatibility
__all__ = ["MCPCodeGeneratorAgent", "mcp_agent"]
