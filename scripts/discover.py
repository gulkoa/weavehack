#!/usr/bin/env python3
"""
Simple client to discover all running A2A servers from the WeaveHacks agent cluster.
"""

import asyncio
import sys
from pprint import pprint
from uuid import uuid4

import httpx
from a2a.client import A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

# Expected servers from main.py configuration
EXPECTED_SERVERS = [
    {
        "name": "Root Agent",
        "port": 10000,
        "description": "Main coordination agent",
        "test_message": "Hello! What can you help me with?",
    },
    {
        "name": "Documentation Agent",
        "port": 10001,
        "description": "API documentation extractor",
        "test_message": "Can you extract documentation?",
    },
    {
        "name": "Workflow Generator",
        "port": 10002,
        "description": "REST API workflow analyzer",
        "test_message": "Can you analyze API workflows?",
    },
    {
        "name": "MCP Code Generator",
        "port": 10003,
        "description": "MCP tool code generator",
        "test_message": "Can you generate MCP tools?",
    },
]


async def discover_server(httpx_client, server_info):
    """Discover and test a single server."""
    url = f"http://localhost:{server_info['port']}"

    try:
        print(f"🔍 Discovering {server_info['name']} at {url}...")

        # Try to get the agent card
        try:
            client = await A2AClient.get_client_from_agent_card_url(httpx_client, url)

            # Get agent card info
            agent_card_response = await httpx_client.get(f"{url}/agent-card")
            agent_card = (
                agent_card_response.json()
                if agent_card_response.status_code == 200
                else None
            )

            # Test with a simple message
            send_message_payload = {
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": server_info["test_message"]}],
                    "messageId": uuid4().hex,
                }
            }

            request = SendMessageRequest(
                id=uuid4().hex, params=MessageSendParams(**send_message_payload)
            )

            response = await client.send_message(request)

            return {
                "name": server_info["name"],
                "url": url,
                "port": server_info["port"],
                "description": server_info["description"],
                "status": "✅ ONLINE",
                "agent_card": agent_card,
                "test_response": (
                    response.model_dump(mode="json", exclude_none=True)
                    if response
                    else None
                ),
                "error": None,
            }

        except Exception as e:
            # Try alternative discovery method if agent card fails
            try:
                # Try a simple HTTP request to see if server is running
                response = await httpx_client.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    return {
                        "name": server_info["name"],
                        "url": url,
                        "port": server_info["port"],
                        "description": server_info["description"],
                        "status": "⚠️ PARTIAL (No A2A support)",
                        "agent_card": None,
                        "test_response": None,
                        "error": "Server running but no A2A agent card available",
                    }
            except:
                pass

            return {
                "name": server_info["name"],
                "url": url,
                "port": server_info["port"],
                "description": server_info["description"],
                "status": "❌ OFFLINE",
                "agent_card": None,
                "test_response": None,
                "error": str(e),
            }

    except Exception as e:
        return {
            "name": server_info["name"],
            "url": url,
            "port": server_info["port"],
            "description": server_info["description"],
            "status": "❌ ERROR",
            "agent_card": None,
            "test_response": None,
            "error": str(e),
        }


async def discover_all_servers():
    """Discover all expected servers."""
    print("🚀 WeaveHacks Agent Discovery Client")
    print("=" * 50)
    print("Discovering all running A2A servers...\n")

    discovered_agents = []

    async with httpx.AsyncClient() as httpx_client:
        # Discover all servers concurrently
        tasks = [discover_server(httpx_client, server) for server in EXPECTED_SERVERS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                print(f"❌ Error during discovery: {result}")
                continue

            discovered_agents.append(result)

            # Print discovery result
            print(f"{result['status']} {result['name']}")
            print(f"   URL: {result['url']}")
            print(f"   Description: {result['description']}")

            if result["agent_card"]:
                print(f"   Agent Card: Available")
                if "capabilities" in result["agent_card"]:
                    print(f"   Capabilities: {result['agent_card']['capabilities']}")

            if result["error"]:
                print(f"   Error: {result['error']}")

            print()

    return discovered_agents


async def print_summary(discovered_agents):
    """Print a summary of discovered agents."""
    print("\n" + "=" * 60)
    print("📊 DISCOVERY SUMMARY")
    print("=" * 60)

    online_agents = [
        agent for agent in discovered_agents if "ONLINE" in agent["status"]
    ]
    partial_agents = [
        agent for agent in discovered_agents if "PARTIAL" in agent["status"]
    ]
    offline_agents = [
        agent
        for agent in discovered_agents
        if "OFFLINE" in agent["status"] or "ERROR" in agent["status"]
    ]

    print(f"Total Agents Expected: {len(EXPECTED_SERVERS)}")
    print(f"✅ Online (Full A2A): {len(online_agents)}")
    print(f"⚠️ Partial (Limited): {len(partial_agents)}")
    print(f"❌ Offline/Error: {len(offline_agents)}")

    if online_agents:
        print(f"\n🌐 ONLINE AGENTS:")
        for agent in online_agents:
            print(f"• {agent['name']} - {agent['url']}")

    if partial_agents:
        print(f"\n⚠️ PARTIAL AGENTS:")
        for agent in partial_agents:
            print(f"• {agent['name']} - {agent['url']}")

    if offline_agents:
        print(f"\n❌ OFFLINE AGENTS:")
        for agent in offline_agents:
            print(f"• {agent['name']} - {agent['url']}")

    print(f"\n💡 USAGE:")
    if online_agents:
        print("You can connect to online agents using:")
        print("```python")
        print("from python_a2a import A2AClient")
        for agent in online_agents[:2]:  # Show first 2 examples
            print(f"client = A2AClient('{agent['url']}')")
            print(f"response = client.ask('Your message here')")
        print("```")

    if len(online_agents) < len(EXPECTED_SERVERS):
        print(f"\n🔧 TROUBLESHOOTING:")
        print("If agents are offline:")
        print("1. Make sure main.py is running: python main.py")
        print("2. Check if ports are available: netstat -an | grep :1000")
        print("3. Check firewall settings")
        print("4. Look for error messages in the main.py console")


async def test_agent_network():
    """Test the agent network functionality if available."""
    try:
        # Try to import and use AgentNetwork if available
        from python_a2a import AgentNetwork

        print(f"\n🔗 TESTING AGENT NETWORK...")

        # Create a network
        network = AgentNetwork(name="WeaveHacks Agent Network")

        # Add discovered agents
        urls = [f"http://localhost:{server['port']}" for server in EXPECTED_SERVERS]
        discovered_count = network.discover_agents(urls)

        print(f"Network discovered {discovered_count} agents")

        # List all agents in the network
        for agent_info in network.list_agents():
            print(f"• {agent_info['name']} at {agent_info['url']}")
            if "description" in agent_info:
                print(f"  Description: {agent_info['description']}")

        return network

    except ImportError:
        print(f"\n⚠️ AgentNetwork not available in this version of python-a2a")
        return None
    except Exception as e:
        print(f"\n❌ Error testing agent network: {e}")
        return None


async def main():
    """Main discovery function."""
    try:
        # Discover all servers
        discovered_agents = await discover_all_servers()

        # Print summary
        await print_summary(discovered_agents)

        # Test agent network if available
        await test_agent_network()

        print(f"\n🎉 Discovery complete!")

    except KeyboardInterrupt:
        print("\n\n👋 Discovery interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Discovery failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
