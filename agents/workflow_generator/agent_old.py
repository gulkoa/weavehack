import json
from typing import Dict, Any
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


class WorkflowGeneratorAgent(Agent):
    """ADK A2A agent that analyzes REST APIs and generates useful workflows."""
    
    def __init__(self, llm_client=None):
        super().__init__()
        self.name = "workflow_generator"
        self.description = "Analyzes REST API descriptions and generates logical workflows"
        self.llm_client = llm_client
        
        self.workflow_analysis_prompt = """You are an expert API workflow analyst. Analyze the following REST API description and identify:

1. All available endpoints and their HTTP methods
2. Required and optional parameters for each endpoint
3. Authentication requirements
4. Data formats and response types
5. Logical workflows that combine multiple endpoints for common use cases
6. Dependencies between endpoints (e.g., create before update, authenticate before action)
7. Error handling patterns and edge cases
8. Rate limiting or special considerations

Focus heavily on identifying USEFUL WORKFLOWS that solve real problems by combining multiple API calls.

API Description:
{api_description}

Return your analysis as a JSON object with this structure:
{{
    "endpoints": [
        {{
            "method": "GET|POST|PUT|DELETE|PATCH",
            "path": "/endpoint/path",
            "description": "What this endpoint does",
            "parameters": [
                {{"name": "param_name", "type": "string|number|boolean|object", "required": true|false, "description": "param description"}}
            ],
            "auth_required": true|false,
            "response_type": "json|text|binary|etc",
            "depends_on": ["endpoint_ids that must be called first"],
            "error_codes": ["common error codes and meanings"]
        }}
    ],
    "auth": {{
        "type": "bearer|api_key|basic|oauth",
        "header_name": "Authorization|X-API-Key|etc",
        "description": "How to authenticate",
        "endpoint": "/auth/endpoint if applicable"
    }},
    "workflows": [
        {{
            "name": "workflow_name",
            "description": "What this workflow accomplishes and why it's useful",
            "steps": [
                {{
                    "step": 1,
                    "endpoint": "/endpoint/path",
                    "method": "GET|POST|etc",
                    "description": "What this step does",
                    "requires_data_from": ["previous step numbers"],
                    "error_handling": "How to handle errors in this step"
                }}
            ],
            "use_case": "Detailed description of when and why to use this workflow",
            "complexity": "simple|medium|complex",
            "estimated_duration": "How long this workflow typically takes"
        }}
    ],
    "base_url": "https://api.example.com",
    "considerations": [
        "rate limits",
        "async operations", 
        "file uploads",
        "pagination",
        "error retry strategies",
        "data validation requirements"
    ],
    "common_patterns": [
        {{
            "pattern": "CRUD operations",
            "description": "Standard create, read, update, delete patterns",
            "applicable_workflows": ["workflow names that use this pattern"]
        }}
    ]
}}

Be extremely thorough in identifying workflows. Think about:
- Complete user journeys (sign up, configure, use, delete)
- Data processing pipelines (upload, process, download results)
- Batch operations (bulk create, bulk update, bulk delete)
- Monitoring and reporting workflows
- Integration scenarios
- Error recovery workflows"""
    
    def analyze_api_workflows(self, api_description: str) -> Dict[str, Any]:
        """Uses LLM to analyze REST API description and extract workflow information."""
        if not self.llm_client:
            raise Exception("LLM client not configured")
        
        prompt = self.workflow_analysis_prompt.format(api_description=api_description)
        
        try:
            response = self.llm_client.generate(prompt)
            # Parse JSON response from LLM
            workflow_analysis = json.loads(response)
            return workflow_analysis
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Workflow analysis failed: {e}")
    
    def validate_workflows(self, workflow_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validates the workflow analysis for completeness and consistency."""
        validation_issues = []
        
        # Check required fields
        required_fields = ["endpoints", "workflows", "base_url"]
        for field in required_fields:
            if field not in workflow_analysis:
                validation_issues.append(f"Missing required field: {field}")
        
        # Validate workflows
        if "workflows" in workflow_analysis:
            for i, workflow in enumerate(workflow_analysis["workflows"]):
                workflow_name = workflow.get("name", f"workflow_{i}")
                
                # Check required workflow fields
                required_workflow_fields = ["name", "description", "steps", "use_case"]
                for field in required_workflow_fields:
                    if field not in workflow:
                        validation_issues.append(f"Workflow '{workflow_name}' missing field: {field}")
                
                # Validate steps
                if "steps" in workflow:
                    for j, step in enumerate(workflow["steps"]):
                        if "endpoint" not in step:
                            validation_issues.append(f"Workflow '{workflow_name}' step {j+1} missing endpoint")
                        if "method" not in step:
                            validation_issues.append(f"Workflow '{workflow_name}' step {j+1} missing method")
        
        return {
            "valid": len(validation_issues) == 0,
            "issues": validation_issues,
            "workflow_count": len(workflow_analysis.get("workflows", [])),
            "endpoint_count": len(workflow_analysis.get("endpoints", []))
        }
    

class WorkflowGeneratorExecutor(AgentExecutor):
    """A2A executor for the Workflow Generator Agent."""
    
    def __init__(self, agent: WorkflowGeneratorAgent):
        self.agent = agent
        
    async def cancel(self, task_id: str) -> None:
        """Cancel the execution of a specific task."""
        # Implementation for cancelling tasks
        pass
        
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute workflow generation using the ADK agent."""
        query = context.get_user_input()
        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)
        
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        try:
            # Update status
            await updater.update_status(
                TaskState.working,
                new_agent_text_message("Analyzing API and generating workflows...", task.contextId, task.id)
            )
            
            # Call agent's analysis method directly
            workflow_analysis = self.agent.analyze_api_workflows(query)
            validation_result = self.agent.validate_workflows(workflow_analysis)
            
            # Check for errors
            if not validation_result["valid"]:
                error_msg = "Validation failed: " + "; ".join(validation_result["issues"])
                await updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(f"Error: {error_msg}", task.contextId, task.id),
                    final=True
                )
            else:
                # Format the workflow analysis as readable text
                summary = {
                    "base_url": workflow_analysis.get("base_url", ""),
                    "auth_type": workflow_analysis.get("auth", {}).get("type", "unknown"),
                    "workflows": [
                        {
                            "name": w.get("name", ""),
                            "description": w.get("description", ""),
                            "complexity": w.get("complexity", "unknown"),
                            "step_count": len(w.get("steps", []))
                        }
                        for w in workflow_analysis.get("workflows", [])
                    ]
                }
                
                response_text = f"""# Workflow Analysis Results

## Summary
- Base URL: {summary.get('base_url', 'Not specified')}
- Authentication: {summary.get('auth_type', 'Unknown')}
- Total Endpoints: {validation_result.get('endpoint_count', 0)}
- Total Workflows: {validation_result.get('workflow_count', 0)}

## Workflows Generated
"""
                
                for workflow in summary.get('workflows', []):
                    response_text += f"""
### {workflow.get('name', 'Unnamed Workflow')}
- Description: {workflow.get('description', 'No description')}
- Complexity: {workflow.get('complexity', 'Unknown')}
- Steps: {workflow.get('step_count', 0)}
"""
                
                response_text += f"""

## Full Analysis Data
```json
{json.dumps(workflow_analysis, indent=2)}
```
"""
                
                # Add response as artifact
                await updater.add_artifact(
                    [Part(root=TextPart(text=response_text))],
                    name="workflow_analysis"
                )
                
                await updater.complete()
                
        except Exception as e:
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(f"Workflow generation failed: {str(e)}", task.contextId, task.id),
                final=True
            )


def create_workflow_generator_server(host="localhost", port=10030):
    """Create A2A server for Workflow Generator Agent."""
    # Create the ADK agent
    workflow_agent = WorkflowGeneratorAgent()
    
    # Agent capabilities
    capabilities = AgentCapabilities(streaming=True)
    
    # Agent card (metadata)
    agent_card = AgentCard(
        name="Workflow Generator Agent",
        description="Analyzes REST API descriptions and generates logical workflows",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=capabilities,
        skills=[
            AgentSkill(
                id="generate_workflows",
                name="Generate API Workflows",
                description="Analyzes REST API descriptions and identifies useful workflows",
                tags=["api", "workflow", "analysis", "rest"],
                examples=[
                    "Analyze this API and generate workflows",
                    "What workflows can I create with this REST API?",
                    "Generate useful workflows from this API documentation",
                ],
            )
        ],
    )
    
    # Create executor
    executor = WorkflowGeneratorExecutor(agent=workflow_agent)
    
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
    """Factory function to create the workflow generator agent."""
    return WorkflowGeneratorAgent(llm_client=llm_client)


def run_server():
    """Run the A2A server."""
    app = create_workflow_generator_server()
    uvicorn.run(app.build(), host="127.0.0.1", port=10030, log_level="info")


if __name__ == "__main__":
    run_server()
