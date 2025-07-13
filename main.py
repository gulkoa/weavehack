#!/usr/bin/env python3
"""
Main server launcher for all A2A agents.
Boots up all agents concurrently on their designated ports.
"""
from dotenv import load_dotenv

load_dotenv()


import os
import signal
import sys
import threading
import time
from contextlib import contextmanager

import weave
from python_a2a import A2AClient, run_server

# weave.init("rochan-hm-self/quickstart_playground")

# Add the parent directory to the path to import agents
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import (
    DocumentationAgent,
    MCPCodeGeneratorAgent,
    RootAgent,
    WorkflowGeneratorAgent,
)

# Server configuration
SERVERS = [
    {
        "agent_class": RootAgent,
        "port": 10000,
        "name": "Root Agent",
        "description": "Main coordination agent",
        "test_message": "Hello! Can you help me extract documentation for https://api.github.com?",
    },
    {
        "agent_class": DocumentationAgent,
        "port": 10001,
        "name": "Documentation Agent",
        "description": "API documentation extractor",
        "test_message": "Get API documentation for Stripe",
    },
    {
        "agent_class": WorkflowGeneratorAgent,
        "port": 10002,
        "name": "Workflow Generator",
        "description": "REST API workflow analyzer",
        "test_message": "Analyze REST API for user management and generate workflows",
    },
    {
        "agent_class": MCPCodeGeneratorAgent,
        "port": 10003,
        "name": "MCP Code Generator",
        "description": "MCP tool code generator",
        "test_message": "Generate MCP tools for user authentication workflow",
    },
]

# Global server management
server_threads = []
running_servers = []
shutdown_event = threading.Event()


def start_server(agent_class, port, name):
    """Start a server in a separate thread."""
    try:
        print(f"🚀 Starting {name} on port {port}...")
        agent_instance = agent_class()

        # Store the agent instance for potential cleanup
        running_servers.append({"agent": agent_instance, "port": port, "name": name})

        # Run the server (this will block until shutdown)
        run_server(agent_instance, port=port)

    except Exception as e:
        print(f"❌ Error starting {name} on port {port}: {str(e)}")
        import traceback

        traceback.print_exc()


def test_server(port, name, test_message, max_retries=3):
    """Test if a server is responding."""
    for attempt in range(max_retries):
        try:
            client = A2AClient(f"http://localhost:{port}")
            response = client.ask(test_message)
            print(f"✅ {name} (port {port}) - Test successful!")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(
                    f"⏳ {name} (port {port}) - Attempt {attempt + 1} failed, retrying..."
                )
                time.sleep(2)
            else:
                print(f"❌ {name} (port {port}) - All test attempts failed: {str(e)}")
                return False
    return False


def wait_for_all_servers(timeout=30):
    """Wait for all servers to be ready."""
    print("\n⏳ Waiting for all servers to be ready...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        all_ready = True
        for server in SERVERS:
            try:
                client = A2AClient(f"http://localhost:{server['port']}")
                # Simple health check
                client.ask("status")
            except:
                all_ready = False
                break

        if all_ready:
            print("✅ All servers are ready!")
            return True

        time.sleep(1)

    print("⚠️  Timeout waiting for servers to be ready")
    return False


def run_tests():
    """Run tests on all servers."""
    print(f"\n{'='*60}")
    print("RUNNING SERVER TESTS")
    print(f"{'='*60}")

    results = []
    for server in SERVERS:
        success = test_server(server["port"], server["name"], server["test_message"])
        results.append((server["name"], success))

    # Print test summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")

    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 All servers are working correctly!")
    else:
        print("\n⚠️  Some servers failed testing.")

    return all_passed


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print("\n🛑 Received shutdown signal. Stopping all servers...")
    shutdown_event.set()

    # Give servers time to shut down gracefully
    for thread in server_threads:
        thread.join(timeout=5)

    print("👋 All servers stopped.")
    sys.exit(0)


def main():
    """Main function to boot up all servers."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🚀 WeaveHacks A2A Agent Cluster")
    print("=" * 50)
    print("Starting all agents with Python A2A framework...")
    print("Each agent uses ADK (Agent Development Kit) with Gemini")
    print("and is wrapped in A2A protocol for interoperability\n")

    # Start all servers concurrently
    for server in SERVERS:
        thread = threading.Thread(
            target=start_server,
            args=(server["agent_class"], server["port"], server["name"]),
            daemon=True,
        )
        thread.start()
        server_threads.append(thread)
        time.sleep(1)  # Brief pause between starts

    # Wait for servers to be ready
    # if wait_for_all_servers():
    #     # Run tests
    #     test_success = run_tests()

    #     # Print connection info
    #     print(f"\n{'='*60}")
    #     print("🌐 ALL SERVERS RUNNING")
    #     print(f"{'='*60}")

    #     for server in SERVERS:
    #         print(f"• {server['name']}: http://localhost:{server['port']}")
    #         print(f"  └── {server['description']}")

    #     print(f"\n{'='*60}")
    #     print("💡 USAGE EXAMPLES")
    #     print(f"{'='*60}")

    #     print("Using A2A Client:")
    #     print("```python")
    #     print("from python_a2a import A2AClient")
    #     print("client = A2AClient('http://localhost:10000')")
    #     print("response = client.ask('Extract docs for GitHub API')")
    #     print("```")

    #     print("\nUsing curl:")
    #     print("```bash")
    #     print("curl -X POST http://localhost:10000/ask \\")
    #     print("  -H 'Content-Type: application/json' \\")
    #     print('  -d \'{"message": "Extract docs for GitHub API"}\'')
    #     print("```")

    #     print(f"\n{'='*60}")
    #     print("🔄 AGENT WORKFLOW")
    #     print(f"{'='*60}")
    #     print("1. Root Agent (10000) - Coordinates and routes requests")
    #     print("2. Documentation Agent (10001) - Extracts API documentation")
    #     print("3. Workflow Generator (10002) - Analyzes APIs and creates workflows")
    #     print("4. MCP Code Generator (10003) - Generates MCP tools from workflows")

    #     print(f"\n{'='*60}")
    #     print("Press Ctrl+C to stop all servers")
    #     print(f"{'='*60}")

    # Keep the main thread alive
    try:
        while not shutdown_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

    # else:
    #     print("❌ Failed to start all servers properly")
    #     sys.exit(1)


if __name__ == "__main__":
    main()
