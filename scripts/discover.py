import asyncio
import uuid
import httpx
from a2a.client import A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

async def main():
    # Replace with your server1 URL
    server_url = "http://localhost:10001/"
    
    async with httpx.AsyncClient() as httpx_client:
        # Discover agent card and initialize client
        client = await A2AClient.get_client_from_agent_card_url(httpx_client, server_url)
        
        # Prepare the message payload
        send_message_payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "Hello from server2!"}],
                "messageId": uuid.uuid4().hex,
            }
        }
        request = SendMessageRequest(params=MessageSendParams(**send_message_payload))
        
        # Send the message and print the response
        response = await client.send_message(request)
        print(response.model_dump(mode="json", exclude_none=True))

if __name__ == "__main__":
    asyncio.run(main())