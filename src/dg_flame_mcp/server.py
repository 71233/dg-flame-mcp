"""DG Flame MCP server entry point."""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from .bridge_client import (
    BridgeUnavailableError,
    FlameBridgeClient,
    default_socket_path,
)
from .protocol import BridgeProtocolError, error_response

mcp = MCPServer("DG Flame MCP")
_bridge = FlameBridgeClient()


def _call_bridge(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        return _bridge.call(method, params)
    except (BridgeUnavailableError, BridgeProtocolError) as exc:
        return error_response(
            request_id=None,
            method=method,
            backend="bridge",
            error_type=type(exc).__name__,
            message=str(exc),
            details={"socket_path": default_socket_path()},
        )


@mcp.tool(name="flame.status")
def flame_status() -> dict[str, Any]:
    """Check the Flame bridge and return a compact live-session status."""
    return _call_bridge("status")


@mcp.tool(name="flame.capabilities")
def flame_capabilities() -> dict[str, Any]:
    """Return the execution backends exposed by the current Flame bridge."""
    return _call_bridge("capabilities")


@mcp.tool(name="flame.get_context")
def flame_get_context() -> dict[str, Any]:
    """Return Flame version, current tab, project, and workspace."""
    return _call_bridge("get_context")


@mcp.tool(name="flame.get_selection")
def flame_get_selection() -> dict[str, Any]:
    """Return the current Media Panel selection."""
    return _call_bridge("get_selection")


@mcp.tool(name="flame.set_current_tab")
def flame_set_current_tab(tab: str) -> dict[str, Any]:
    """Switch Flame tabs through the Python API and verify the observed tab."""
    return _call_bridge("set_current_tab", {"tab": tab})


@mcp.tool(name="flame.execute_shortcut")
def flame_execute_shortcut(description: str) -> dict[str, Any]:
    """Execute a native Flame shortcut when that experimental backend is enabled."""
    return _call_bridge("execute_shortcut", {"description": description})


@mcp.tool(name="flame.press_button")
def flame_press_button(name: str, param: float = 0.0) -> dict[str, Any]:
    """Invoke a Flame button when that experimental backend is enabled."""
    return _call_bridge("press_button", {"name": name, "param": param})


def main() -> None:
    """Run DG Flame MCP over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
