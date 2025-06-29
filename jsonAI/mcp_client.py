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
        url = f"{self.base_url}/{server}/{tool}"
        response = requests.post(
            url,
            json=args,
            headers=self.headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    async def call_tool_async(self, server: str, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{server}/{tool}"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=args,
                headers=self.headers,
                timeout=self.timeout
            ) as response:
                response.raise_for_status()
                return await response.json()

    @staticmethod
    def create_default_client() -> 'MCPClient':
        return MCPClient(
            base_url="http://localhost:8080",
            auth_token="default_token"
        )
