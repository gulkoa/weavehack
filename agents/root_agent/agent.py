from typing import Dict, Optional, Any
import json
import time
import threading
from datetime import datetime

# --- ADK and A2A imports ---
from crewai import LLM
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from python_a2a import A2AServer, TaskState, TaskStatus, agent, run_server, skill
from python_a2a import AgentNetwork, A2AClient, AIAgentRouter
import os

# Create an agent network
network = AgentNetwork(name="MCP Development Network")

# Add agents to the network
network.add("document_extractor", "http://localhost:10001")
network.add("workflow_generator", "http://localhost:10002")
network.add("mcp_generator", "http://localhost:10003")

ROUTER_LLM = LLM(
    # model="openrouter/deepseek/deepseek-chat-v3-0324:free",
    model="openai/gpt-4.1",
    timeout=1000,
    api_base="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Create a router to intelligently direct queries to the best agent
router = AIAgentRouter(
    llm_client=A2AClient("http://localhost:10003/", google_a2a_compatible=True),
    agent_network=network
)

# We'll create the ADK agent inside the class so we can bind tools to it

@agent(
    name="Root Agent",
    description="Main coordination agent that orchestrates the MCP server generation process",
    version="1.0.0",
)
class RootAgent(A2AServer):
    def __init__(self):
        super().__init__()
        self.current_context = {}
        self.session_states = {}  # Track session states across requests
        self.workflow_history = {}  # Track workflow progress
        self.lock = threading.Lock()  # Thread safety for state management
        self.current_session_context = {}  # Current session context for tools
        
        # Create the ADK agent with function tools
        self.adk_agent = Agent(
            name="root_agent",
            model="gemini-2.0-flash-exp",
            description="Main coordination agent that orchestrates the MCP server generation process",
            instruction="""You are a root coordination agent that helps users create MCP servers through a multi-step process.

When a user asks you to create an MCP server, you MUST follow these steps IN ORDER:

1. Use the extract_documentation tool to get API documentation
2. Use the generate_workflows tool to analyze the documentation and create workflows
3. Use the generate_mcp_server tool to generate the final MCP server code

ALWAYS complete all three steps before returning a response to the user.

IMPORTANT: You must execute ALL THREE tools in sequence. Do not stop after just one tool call.""",
            tools=[self._extract_documentation_tool, self._generate_workflows_tool, self._generate_mcp_tool],
        )

    def get_session_context(self, session_id: str) -> Dict:
        """Get context for a specific session."""
        with self.lock:
            return self.session_states.get(session_id, {
                "documentation": None,
                "workflows": None,
                "mcp_server": None,
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "workflow_step": "start"
            })
    
    def update_session_context(self, session_id: str, updates: Dict) -> None:
        """Update context for a specific session."""
        with self.lock:
            if session_id not in self.session_states:
                self.session_states[session_id] = self.get_session_context(session_id)
            
            self.session_states[session_id].update(updates)
            self.session_states[session_id]["last_activity"] = datetime.now().isoformat()
    
    def retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """Retry a function with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                delay = base_delay * (2 ** attempt)
                print(f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                time.sleep(delay)
    
    @skill(
        name="Agent Coordination",
        description="Coordinates the MCP server generation process across specialized agents",
        tags=["coordination", "routing", "orchestration", "adk", "gemini"],
    )
    def coordinate_request(self, request: str, agent_type: str = "auto", session_id: str = "default") -> Dict:
        """
        Coordinate requests across specialized agents to generate MCP servers.

        You can reach out to a documentation_extractor (pulls api docs from web)
        workflow_generator (takes in api docs and generates useful workflows)
        and mcp_generator (writes code for mcp server)

        Args:
            request (str): Fine-grained request to an agent
            agent_type (str): Type of agent to route to ("documentation_extractor", "workflow_generator", "mcp_generator", "auto")

        Returns:
            dict: Response from the appropriate agent with next steps
        """
        try:
            # Get session context
            context = self.get_session_context(session_id)
            
            # Determine routing
            if agent_type == "auto":
                agent_type = self._determine_next_agent(request, context)
                print(f"Auto-routing to {agent_type} based on request and context")
            
            # Validate agent availability
            def get_agent():
                agent = network.get_agent(agent_type)
                if not agent:
                    raise Exception(f"Agent {agent_type} not available")
                return agent
            
            # Get the selected agent with retry
            print(f"[RootAgent] Getting agent: {agent_type}")
            agent = self.retry_with_backoff(get_agent)
            print(f"[RootAgent] Got agent: {agent}")
            
            # Process based on agent type and session context
            if agent_type == "document_extractor":
                # Extract API documentation
                def extract_docs():
                    print(f"[RootAgent] Sending request to document_extractor: '{request}'")
                    response = agent.ask(request)
                    print(f"[RootAgent] Got response from document_extractor: {response}")
                    return response
                
                response = self.retry_with_backoff(extract_docs)
                
                # Update session context
                self.update_session_context(session_id, {
                    "documentation": response,
                    "workflow_step": "documentation_complete"
                })
                
                return {
                    "status": "success",
                    "response": response,
                    "next_step": "workflow_generator",
                    "message": "Documentation extracted successfully. Ready for workflow analysis.",
                    "session_id": session_id,
                    "workflow_step": "documentation_complete"
                }
                
            elif agent_type == "workflow_generator":
                # Generate workflows from documentation
                if not context.get("documentation"):
                    return {
                        "status": "error",
                        "error_message": "Documentation extraction required first. Please provide API documentation.",
                        "next_step": "document_extractor",
                        "session_id": session_id,
                        "current_step": "workflow_generation",
                        "required_input": "API documentation"
                    }
                
                def generate_workflows():
                    return agent.ask(context["documentation"])
                
                response = self.retry_with_backoff(generate_workflows)
                
                # Update session context
                self.update_session_context(session_id, {
                    "workflows": response,
                    "workflow_step": "workflows_complete"
                })
                
                return {
                    "status": "success",
                    "response": response,
                    "next_step": "mcp_generator",
                    "message": "Workflows analyzed successfully. Ready to generate MCP server code.",
                    "session_id": session_id,
                    "workflow_step": "workflows_complete"
                }
                
            elif agent_type == "mcp_generator":
                # Generate MCP server implementation
                if not context.get("workflows"):
                    return {
                        "status": "error",
                        "error_message": "Workflow analysis required first. Please complete the workflow generation step.",
                        "next_step": "workflow_generator",
                        "session_id": session_id,
                        "current_step": "mcp_generation",
                        "required_input": "workflow analysis"
                    }
                
                def generate_mcp():
                    return agent.ask(context["workflows"])
                
                response = self.retry_with_backoff(generate_mcp)
                
                # Update session context
                self.update_session_context(session_id, {
                    "mcp_server": response,
                    "workflow_step": "complete"
                })
                
                return {
                    "status": "success",
                    "response": response,
                    "next_step": "complete",
                    "message": "MCP server generated successfully! You can now use the generated code.",
                    "session_id": session_id,
                    "workflow_step": "complete"
                }
            
            else:
                return {
                    "status": "error",
                    "error_message": f"Unknown agent type: {agent_type}. Available: document_extractor, workflow_generator, mcp_generator",
                    "session_id": session_id,
                    "available_agents": ["document_extractor", "workflow_generator", "mcp_generator"]
                }

        except Exception as e:
            # Log the error with context
            error_context = {
                "session_id": session_id,
                "agent_type": agent_type,
                "request": request[:100] + "..." if len(request) > 100 else request,
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "status": "error",
                "error_message": f"Coordination error: {str(e)}",
                "agent_type": agent_type,
                "session_id": session_id,
                "error_context": error_context,
                "suggested_action": "Please try again or contact support if the problem persists"
            }
    
    def _determine_next_agent(self, request: str, context: Dict) -> str:
        """Intelligently determine the next agent based on request and context."""
        request_lower = request.lower()
        
        # Check current workflow step
        current_step = context.get("workflow_step", "start")
        
        # If user explicitly mentions an agent type
        if "document" in request_lower or "extract" in request_lower or "api" in request_lower:
            return "document_extractor"
        elif "workflow" in request_lower or "analyze" in request_lower:
            return "workflow_generator"
        elif "mcp" in request_lower or "generate" in request_lower or "code" in request_lower:
            return "mcp_generator"
        
        # Based on workflow progression
        if current_step == "start" or not context.get("documentation"):
            return "document_extractor"
        elif current_step == "documentation_complete" or not context.get("workflows"):
            return "workflow_generator"
        elif current_step == "workflows_complete" or not context.get("mcp_server"):
            return "mcp_generator"
        
        # Use AI router as fallback
        try:
            agent_type, confidence = router.route_query(request)
            return agent_type
        except:
            # Default fallback
            return "document_extractor"
    
    def _extract_session_id(self, task) -> str:
        """Extract session ID from task or generate one."""
        try:
            # Try to get session ID from task metadata
            if hasattr(task, 'session_id') and task.session_id:
                return task.session_id
            
            # Try to extract from message metadata
            message_data = task.message or {}
            if isinstance(message_data, dict) and 'session_id' in message_data:
                return message_data['session_id']
            
            # Generate based on task content hash for consistency
            content = str(task.message or "")
            import hashlib
            return hashlib.md5(content.encode()).hexdigest()[:8]
        except:
            return "default"
    
    def _format_status_response(self, context: Dict, session_id: str) -> str:
        """Format a status response showing current workflow state."""
        step = context.get("workflow_step", "start")
        created = context.get("created_at", "unknown")
        last_activity = context.get("last_activity", "unknown")
        
        status_text = f"**Session Status**\n\n"
        status_text += f"**Session ID:** {session_id}\n"
        status_text += f"**Created:** {created}\n"
        status_text += f"**Last Activity:** {last_activity}\n"
        status_text += f"**Current Step:** {step}\n\n"
        
        status_text += "**Progress:**\n"
        status_text += f"✅ Documentation: {'Complete' if context.get('documentation') else 'Pending'}\n"
        status_text += f"✅ Workflows: {'Complete' if context.get('workflows') else 'Pending'}\n"
        status_text += f"✅ MCP Server: {'Complete' if context.get('mcp_server') else 'Pending'}\n\n"
        
        if step == "complete":
            status_text += "🎉 **All steps completed!** Your MCP server is ready."
        else:
            next_steps = {
                "start": "Provide API documentation or URL to extract",
                "documentation_complete": "Workflow analysis will begin automatically",
                "workflows_complete": "MCP server generation will begin automatically"
            }
            status_text += f"**Next:** {next_steps.get(step, 'Continue with your request')}"
        
        return status_text

    def handle_task(self, task):
        """Handle incoming A2A tasks with intelligent routing using ADK."""
        try:
            # Extract request from the task message
            message_data = task.message or {}
            content = message_data.get("content", {})

            if isinstance(content, dict):
                text = content.get("text", "")
            else:
                text = str(content)

            if not text.strip():
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={
                        "role": "agent",
                        "content": {
                            "type": "text",
                            "text": "Please provide a request. I can help you create an MCP server by coordinating documentation extraction, workflow analysis, and code generation."
                        },
                    },
                )
                return task

            # Extract session ID for state tracking
            session_id = self._extract_session_id(task)
            
            # Check for session commands
            if text.strip().lower().startswith("status"):
                context = self.get_session_context(session_id)
                status_response = self._format_status_response(context, session_id)
                task.artifacts = [{"parts": [{"type": "text", "text": status_response}]}]
                task.status = TaskStatus(state=TaskState.COMPLETED)
                return task
            
            if text.strip().lower().startswith("reset"):
                with self.lock:
                    if session_id in self.session_states:
                        del self.session_states[session_id]
                reset_response = f"**Session Reset**\n\nSession {session_id} has been reset. You can start a new workflow."
                task.artifacts = [{"parts": [{"type": "text", "text": reset_response}]}]
                task.status = TaskStatus(state=TaskState.COMPLETED)
                return task

            # Use the ADK agent to process the request and orchestrate the full workflow
            result = self._run_full_workflow(text.strip(), session_id)

            # Create response
            task.artifacts = [{"parts": [{"type": "text", "text": result}]}]
            task.status = TaskStatus(state=TaskState.COMPLETED)

        except Exception as e:
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent",
                    "content": {
                        "type": "text",
                        "text": f"Error processing request: {str(e)}",
                    },
                },
            )

        return task
    
    def _extract_documentation_tool(self, request: str) -> str:
        """Tool function to extract documentation."""
        try:
            agent = network.get_agent("document_extractor")
            if not agent:
                return "Error: Document extractor agent not available"
            
            print(f"[Tool] Extracting documentation for: {request}")
            response = agent.ask(request)
            print(f"[Tool] Documentation extracted successfully")
            
            # Store in session context
            self.current_session_context["documentation"] = response
            return response
        except Exception as e:
            return f"Error extracting documentation: {str(e)}"
    
    def _generate_workflows_tool(self, api_docs: str) -> str:
        """Tool function to generate workflows."""
        try:
            agent = network.get_agent("workflow_generator")
            if not agent:
                return "Error: Workflow generator agent not available"
            
            print(f"[Tool] Generating workflows from documentation")
            response = agent.ask(api_docs)
            print(f"[Tool] Workflows generated successfully")
            
            # Store in session context
            self.current_session_context["workflows"] = response
            return response
        except Exception as e:
            return f"Error generating workflows: {str(e)}"
    
    def _generate_mcp_tool(self, workflows: str) -> str:
        """Tool function to generate MCP server."""
        try:
            agent = network.get_agent("mcp_generator")
            if not agent:
                return "Error: MCP generator agent not available"
            
            print(f"[Tool] Generating MCP server from workflows")
            response = agent.ask(workflows)
            print(f"[Tool] MCP server generated successfully")
            
            # Store in session context
            self.current_session_context["mcp_server"] = response
            return response
        except Exception as e:
            return f"Error generating MCP server: {str(e)}"
    
    def _run_full_workflow(self, request: str, session_id: str) -> str:
        """Run the complete MCP server generation workflow using the ADK agent."""
        # Set the current session context for tools to use
        self.current_session_context = self.get_session_context(session_id)
        
        # Initialize session and runner for the ADK agent
        session_service = InMemorySessionService()
        session = session_service.create_session_sync(
            app_name="root_agent_app",
            user_id="user1",
            session_id=session_id
        )
        runner = Runner(agent=self.adk_agent, app_name="root_agent_app", session_service=session_service)
        
        # Create the initial user message
        initial_prompt = f"Create an MCP server for: {request}"
        
        content = types.Content(role='user', parts=[types.Part(text=initial_prompt)])
        
        # Collect all responses from the agent
        all_responses = []
        tool_calls = []
        
        # Run the agent to completion
        print(f"[RootAgent] Starting workflow for: {request}")
        events = runner.run(user_id="user1", session_id=session_id, new_message=content)
        
        for event in events:
            if hasattr(event, 'content'):
                if event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            all_responses.append(part.text)
                        if hasattr(part, 'function_call'):
                            tool_calls.append(part.function_call.name)
        
        # Update session context with the results
        self.update_session_context(session_id, self.current_session_context)
        
        # Get final session context
        context = self.get_session_context(session_id)
        
        # Format the complete response
        final_response = "# MCP Server Generation Results\n\n"
        
        if context.get("mcp_server"):
            # If we have the final MCP server, show it prominently
            final_response += "## Generated MCP Server Code:\n\n"
            final_response += "```python\n"
            final_response += context['mcp_server']
            final_response += "\n```\n\n"
            final_response += "✅ **MCP server generated successfully!**\n\n"
            final_response += f"**Tools used:** {', '.join(tool_calls)}\n"
        else:
            # Show whatever progress we made
            final_response += "## Workflow Progress:\n\n"
            
            if context.get("documentation"):
                final_response += "### ✅ Step 1: Documentation Extracted\n"
                final_response += f"{context['documentation'][:300]}...\n\n"
            else:
                final_response += "### ❌ Step 1: Documentation Extraction - Pending\n\n"
            
            if context.get("workflows"):
                final_response += "### ✅ Step 2: Workflows Analyzed\n"
                final_response += f"{context['workflows'][:300]}...\n\n"
            else:
                final_response += "### ❌ Step 2: Workflow Analysis - Pending\n\n"
            
            if context.get("mcp_server"):
                final_response += "### ✅ Step 3: MCP Server Generated\n"
            else:
                final_response += "### ❌ Step 3: MCP Generation - Pending\n\n"
            
            # Add agent responses
            if all_responses:
                final_response += "## Agent Messages:\n\n"
                final_response += "\n\n".join(all_responses)
        
        return final_response
    
    def ask(self, question: str):
        """Ask a question to the Gemini agent using ADK session and runner."""
        session_service = InMemorySessionService()
        session = session_service.create_session_sync(
            app_name="my_app",
            user_id="user1",
            session_id="mysession"
        )
        runner = Runner(agent=self.adk_agent, app_name="my_app", session_service=session_service)
        content = types.Content(role='user', parts=[types.Part(text=question)])

        # Send the question and get response
        events = runner.run(user_id="user1", session_id="mysession", new_message=content)
        for event in events:
            if event.is_final_response():
                return event.content.parts[0].text

if __name__ == "__main__":
    print("Starting Root Agent server at http://localhost:10000/")
    agent = RootAgent()
    run_server(agent, port=10000)