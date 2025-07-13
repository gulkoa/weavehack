import ast
import json
from typing import List, Dict, Any, Optional
import asyncio
import uvicorn
from google.adk import Agent

# A2A imports
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Part,
    TaskState,
    TextPart,
)
from a2a.utils import new_agent_text_message, new_task


class MCPCodeGeneratorAgent(Agent):
    """ADK A2A agent that generates Python MCP tools from workflow analysis using LLM."""
    
    def __init__(self, llm_client=None):
        super().__init__()
        self.name = "mcp_code_generator"
        self.description = "Generates Python MCP tool code from workflow analysis using LLM"
        self.llm_client = llm_client
        
        
        self.mcp_generation_prompt = """You are an expert Python developer creating MCP (Model Context Protocol) tools from workflow analysis.

Given the following workflow analysis, create useful MCP tools as Python functions. Each tool should:
1. Be completely synchronous (no async/await)
2. Handle authentication properly using the auth information provided
3. Include comprehensive error handling and retry logic
4. Implement complete workflows by combining multiple API calls
5. Return meaningful results in a structured format
6. Include proper docstrings with parameter descriptions
7. Use only standard libraries (requests, json, time, urllib, etc.)
8. Handle common edge cases (network errors, rate limits, invalid responses)

Workflow Analysis:
{workflow_analysis}

For each workflow in the analysis, generate corresponding Python functions that implement the complete workflow.

Return a JSON array where each object has:
{{
    "name": "function_name",
    "description": "Brief description of what this tool does",
    "workflow_name": "name of the workflow this implements",
    "python_body": "complete Python function code as a string",
    "complexity": "simple|medium|complex",
    "estimated_api_calls": "number of API calls this function makes"
}}

Guidelines for code generation:
- Create one function per workflow
- Include proper authentication handling in each function
- Add retry logic for network failures
- Handle rate limiting with appropriate delays
- Validate input parameters
- Return structured, useful results
- Include error context in exceptions
- Add logging or status updates for complex workflows
- Use descriptive variable names
- Include examples in docstrings

Make the tools as practical and robust as possible. Focus on real-world usage scenarios."""
    
    def validate_python_syntax(self, code: str) -> Dict[str, Any]:
        """Validates Python code syntax and returns validation result."""
        try:
            ast.parse(code)
            return {"valid": True, "error": None}
        except SyntaxError as e:
            return {
                "valid": False, 
                "error": f"Syntax error at line {e.lineno}: {e.msg}"
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def generate_mcp_tools_from_workflows(self, workflow_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Uses LLM to generate MCP tools from workflow analysis."""
        if not self.llm_client:
            raise Exception("LLM client not configured")
        
        prompt = self.mcp_generation_prompt.format(workflow_analysis=json.dumps(workflow_analysis, indent=2))
        
        try:
            response = self.llm_client.generate(prompt)
            # Parse JSON response from LLM
            mcp_tools = json.loads(response)
            return mcp_tools
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"MCP tool generation failed: {e}")
    

class MCPCodeGeneratorExecutor(AgentExecutor):
    """A2A executor for the MCP Code Generator Agent."""
    
    def __init__(self, agent: MCPCodeGeneratorAgent):
        self.agent = agent
        
    async def cancel(self, task_id: str) -> None:
        """Cancel the execution of a specific task."""
        # Implementation for cancelling tasks
        pass
        
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute MCP code generation using the ADK agent."""
        query = context.get_user_input()
        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)
        
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        try:
            # Update status
            await updater.update_status(
                TaskState.working,
                new_agent_text_message("Generating Python MCP tools from workflow analysis...", task.contextId, task.id)
            )
            
            # Try to parse workflow analysis from query
            try:
                workflow_analysis = json.loads(query)
            except json.JSONDecodeError:
                # If not JSON, assume it's a request with workflow analysis
                workflow_analysis = {"workflows": [], "endpoints": []}
            
            # Validate workflow analysis
            if not workflow_analysis.get("workflows"):
                await updater.update_status(
                    TaskState.failed,
                    new_agent_text_message("Error: No workflows provided in analysis", task.contextId, task.id),
                    final=True
                )
                return
            
            # Generate MCP tools from workflows
            mcp_tools_raw = self.agent.generate_mcp_tools_from_workflows(workflow_analysis)
            
            # Validate and filter tools
            validated_tools = []
            validation_errors = []
            
            for tool in mcp_tools_raw:
                if "name" not in tool or "python_body" not in tool:
                    validation_errors.append(f"Tool missing required fields: {tool}")
                    continue
                
                # Validate Python syntax
                validation = self.agent.validate_python_syntax(tool["python_body"])
                if validation["valid"]:
                    validated_tools.append(tool)
                else:
                    validation_errors.append(f"Tool '{tool['name']}' has syntax error: {validation['error']}")
            
            # Check for errors
            if validation_errors:
                error_msg = "Validation errors: " + "; ".join(validation_errors)
                await updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(f"Error: {error_msg}", task.contextId, task.id),
                    final=True
                )
            else:
                # Format the generated tools as readable text
                summary = {
                    "generated_tools": [
                        {
                            "name": t.get("name", ""),
                            "description": t.get("description", ""),
                            "workflow_name": t.get("workflow_name", ""),
                            "complexity": t.get("complexity", "unknown")
                        }
                        for t in validated_tools
                    ]
                }
                
                response_text = f"""# MCP Tools Generated

## Summary
- Total Tools Generated: {len(validated_tools)}
- Source Workflows: {len(workflow_analysis.get("workflows", []))}

## Generated Tools
"""
                
                for i, tool in enumerate(validated_tools, 1):
                    response_text += f"""
### Tool {i}: {tool.get('name', 'Unnamed Tool')}
- Description: {tool.get('description', 'No description')}
- Workflow: {tool.get('workflow_name', 'Unknown')}
- Complexity: {tool.get('complexity', 'Unknown')}

```python
{tool.get('python_body', 'No code available')}
```
"""
                
                if validation_errors:
                    response_text += f"""

## Validation Errors
"""
                    for error in validation_errors:
                        response_text += f"- {error}\n"
                
                # Add response as artifact
                await updater.add_artifact(
                    [Part(root=TextPart(text=response_text))],
                    name="mcp_tools"
                )
                
                await updater.complete()
                
        except Exception as e:
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(f"MCP code generation failed: {str(e)}", task.contextId, task.id),
                final=True
            )


def create_mcp_code_generator_server(host="localhost", port=10031):
    """Create A2A server for MCP Code Generator Agent."""
    # Create the ADK agent
    code_agent = MCPCodeGeneratorAgent()
    
    # Agent capabilities
    capabilities = AgentCapabilities(streaming=True)
    
    # Agent card (metadata)
    agent_card = AgentCard(
        name="MCP Code Generator Agent",
        description="Generates Python MCP tool code from workflow analysis",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=capabilities,
        skills=[
            AgentSkill(
                id="generate_mcp_code",
                name="Generate MCP Tools",
                description="Generates Python MCP tool code from workflow analysis",
                tags=["mcp", "python", "code", "generation", "tools"],
                examples=[
                    "Generate MCP tools from this workflow analysis",
                    "Create Python code for these API workflows",
                    "Convert workflow analysis to MCP tools",
                ],
            )
        ],
    )
    
    # Create executor
    executor = MCPCodeGeneratorExecutor(agent=code_agent)
    
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )
    
    # Create A2A application
    return A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )


# Factory function for ADK
def create_agent(llm_client=None):
    """Factory function to create the MCP code generator agent."""
    return MCPCodeGeneratorAgent(llm_client=llm_client)


def run_server():
    """Run the A2A server."""
    app = create_mcp_code_generator_server()
    uvicorn.run(app.build(), host="127.0.0.1", port=10031, log_level="info")


if __name__ == "__main__":
    run_server()