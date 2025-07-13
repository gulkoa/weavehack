# Import from "agent copy.py" file
import importlib.util
import os

spec = importlib.util.spec_from_file_location(
    "workflow_agent_copy", os.path.join(os.path.dirname(__file__), "agent copy.py")
)
workflow_agent_copy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow_agent_copy)

# Export the A2A server and ADK agent for backward compatibility
WorkflowGeneratorAgent = workflow_agent_copy.WorkflowGeneratorAgent
workflow_agent = workflow_agent_copy.workflow_agent

__all__ = ["WorkflowGeneratorAgent", "workflow_agent"]
