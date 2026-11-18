# -*- coding: utf-8 -*-
import os
import sys
import httpx
import anyio
from mcp.server.fastmcp import FastMCP, Image, Context
import base64
from typing import Optional, Dict, Any, Union

# Create a generic MCP server for interacting with Revit
# Use stateless_http=True and json_response=True for better compatibility
mcp = FastMCP(
    "Revit MCP Server", 
    host="0.0.0.0", 
    port=8000,
    stateless_http=True,
    json_response=True
)

# Configuration
REVIT_HOST = "localhost"
# pyRevit Routes gives the first Revit session port 48884 and each extra
# session the next port (48885, 48886, ...). Set REVIT_PORT to pin one port;
# otherwise the server finds the Revit session itself, so it can start before
# Revit does and follows Revit if it comes back on a different port.
_PINNED_PORT = os.environ.get("REVIT_PORT", "").strip()
_CANDIDATE_PORTS = [int(_PINNED_PORT)] if _PINNED_PORT else list(range(48884, 48890))
_revit_port = _CANDIDATE_PORTS[0]
_port_checked = False


def _base_url(port: int) -> str:
    return f"http://{REVIT_HOST}:{port}/revit_mcp"


async def _discover_port() -> None:
    """Point at the first candidate port where pyRevit Routes answers as revit_mcp."""
    global _revit_port, _port_checked
    for port in _CANDIDATE_PORTS:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{_base_url(port)}/status/")
            if r.status_code == 200 and r.json().get("api_name") == "revit_mcp":
                if port != _revit_port:
                    print(f"Revit found on port {port}", file=sys.stderr)
                _revit_port = port
                _port_checked = True
                return
        except Exception:
            continue


async def _send(method: str, endpoint: str, timeout: float, **kwargs) -> httpx.Response:
    """Send a request to Revit. If Revit can't be reached, look for it on the
    other ports and retry once. A connection error means the request was never
    sent, so retrying a POST can't apply a change twice."""
    if not _port_checked:
        await _discover_port()
    for attempt in (1, 2):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                return await client.request(method, f"{_base_url(_revit_port)}{endpoint}", **kwargs)
        except httpx.ConnectError:
            if attempt == 2:
                raise
            await _discover_port()


async def revit_get(endpoint: str, ctx: Context = None, **kwargs) -> Union[Dict, str]:
    """Simple GET request to Revit API"""
    return await _revit_call("GET", endpoint, ctx=ctx, **kwargs)


async def revit_post(endpoint: str, data: Dict[str, Any], ctx: Context = None, **kwargs) -> Union[Dict, str]:
    """Simple POST request to Revit API"""
    return await _revit_call("POST", endpoint, data=data, ctx=ctx, **kwargs)


async def revit_image(endpoint: str, ctx: Context = None) -> Union[Image, str]:
    """GET request that returns an Image object"""
    try:
        response = await _send("GET", endpoint, timeout=60.0)
        if response.status_code == 200:
            data = response.json()
            image_bytes = base64.b64decode(data["image_data"])
            return Image(data=image_bytes, format="png")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {e}"


async def _revit_call(method: str, endpoint: str, data: Dict = None, ctx: Context = None, 
                     timeout: float = 30.0, params: Dict = None) -> Union[Dict, str]:
    """Internal function handling all HTTP calls"""
    try:
        if method == "GET":
            response = await _send("GET", endpoint, timeout=timeout, params=params)
        else:  # POST
            response = await _send("POST", endpoint, timeout=timeout, json=data,
                                   headers={"Content-Type": "application/json"})

        return response.json() if response.status_code == 200 else f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {e}"


# Register all tools BEFORE the main block
from tools import register_tools
register_tools(mcp, revit_get, revit_post, revit_image)


async def run_combined_async():
    """Run server with both SSE and streamable-http endpoints.

    This allows clients to connect via either:
    - SSE: GET /sse, POST /messages/
    - Streamable-HTTP: POST/GET /mcp
    """
    import uvicorn

    # Get the streamable-http app first - it has the proper lifespan
    # that initializes the session manager's task group
    http_app = mcp.streamable_http_app()

    # Get SSE routes (SSE doesn't need special lifespan - it creates
    # task groups per-request in connect_sse())
    sse_app = mcp.sse_app()

    # Add SSE routes to the http app (preserving its lifespan)
    for route in sse_app.routes:
        http_app.routes.append(route)

    config = uvicorn.Config(
        http_app,
        host=mcp.settings.host,
        port=mcp.settings.port,
        log_level=mcp.settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    transport = "stdio"

    if "--sse" in sys.argv:
        transport = "sse"
    elif "--http" in sys.argv or "--streamable-http" in sys.argv:
        transport = "streamable-http"
    elif "--combined" in sys.argv:
        # Run both SSE and streamable-http transports simultaneously
        print("Starting combined server with SSE (/sse, /messages/) and streamable-http (/mcp) endpoints...")
        anyio.run(run_combined_async)
        sys.exit(0)

    mcp.run(transport=transport)
