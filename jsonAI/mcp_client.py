import requests
import aiohttp
from typing import Dict, Any, Optional

class MCPClient:
    def __init__(self, base_url: str, auth_token: str = None, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json"}
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"

    def call_tool_sync(self, server: str, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool synchronously with detailed error handling."""
        url = f"{self.base_url}/{server}/{tool}"
        try:
            response = requests.post(url, json=args, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise ValueError(f"Failed to call tool '{tool}' on server '{server}': {e}")

    async def call_tool_async(self, server: str, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool asynchronously with detailed error handling."""
        url = f"{self.base_url}/{server}/{tool}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=args, headers=self.headers, timeout=self.timeout) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            raise ValueError(f"Failed to call tool '{tool}' on server '{server}': {e}")

    @staticmethod
    def create_default_client() -> 'MCPClient':
        return MCPClient(
            base_url="http://localhost:8080",
            auth_token="default_token"
        )
