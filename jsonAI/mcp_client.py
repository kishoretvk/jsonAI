import requests
import aiohttp
from aiohttp import ClientTimeout
from typing import Dict, Any, Optional, Mapping, List, Union, cast

class MCPClient:
    def __init__(self, base_url: str, auth_token: Optional[str] = None, timeout: int = 30):
        self.base_url: str = base_url.rstrip('/')
        self.timeout: int = timeout
        self.headers: Dict[str, str] = {"Content-Type": "application/json"}
        if auth_token is not None:
            self.headers["Authorization"] = f"Bearer {auth_token}"

    def call_tool_sync(self, server: str, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool synchronously with detailed error handling."""
        url = f"{self.base_url}/{server}/{tool}"
        try:
            response = requests.post(url, json=args, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            body: Union[Mapping[str, Any], List[Any]] = cast(Union[Mapping[str, Any], List[Any]], response.json())
            # Prefer dict responses; if list, wrap under 'result' to maintain Dict[str, Any]
            if isinstance(body, dict):
                return dict(body)
            return {"result": list(body)}
        except requests.RequestException as e:
            raise ValueError(f"Failed to call tool '{tool}' on server '{server}': {e}")

    async def call_tool_async(self, server: str, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool asynchronously with detailed error handling."""
        url = f"{self.base_url}/{server}/{tool}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=args,
                    headers=self.headers,
                    timeout=ClientTimeout(total=float(self.timeout))
                ) as response:
                    response.raise_for_status()
                    body = await response.json()
                    # Normalize to Dict[str, Any]
                    if isinstance(body, dict):
                        return dict(body)
                    if isinstance(body, list):
                        return {"result": body}
                    return {"result": body}
        except aiohttp.ClientError as e:
            raise ValueError(f"Failed to call tool '{tool}' on server '{server}': {e}")

    @staticmethod
    def create_default_client() -> 'MCPClient':
        return MCPClient(
            base_url="http://localhost:8080",
            auth_token=None
        )
