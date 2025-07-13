from python_a2a.discovery import DiscoveryClient

# Create a discovery client (no agent card needed for discovery)
client = DiscoveryClient(agent_card=None)

# Add your registry (could be a local or remote registry server)
client.add_registry("http://localhost:10001/")

# Discover all agents
agents = client.discover()
print(f"Discovered {len(agents)} agents:")
for agent in agents:
    print(f"- {agent.name} at {agent.url}")
    print(f"  Capabilities: {agent.capabilities}")