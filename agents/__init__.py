# Import from "agent copy.py" file
import importlib.util
import os

from .document_extrator import DocumentationAgent
from .mcp_generator import MCPCodeGeneratorAgent
from .root_agent.agent import RootAgent

spec = importlib.util.spec_from_file_location(
    "workflow_agent_copy",
    os.path.join(os.path.dirname(__file__), "workflow_generator", "agent copy.py"),
)
workflow_agent_copy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow_agent_copy)
WorkflowGeneratorAgent = workflow_agent_copy.WorkflowGeneratorAgent

# Main A2A agents
__all__ = [
    "RootAgent",
    "DocumentationAgent",
    "MCPCodeGeneratorAgent",
    "WorkflowGeneratorAgent",
]
