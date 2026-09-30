"""DG Flame MCP server entry point.

This module is intentionally minimal while the first live-Flame proof of
concept validates transport, threading, capability discovery, and execution
backends.
"""


def main() -> None:
    """Run the DG Flame MCP server.

    The MCP transport implementation will be added after the initial
    architecture is validated against a live Autodesk Flame session.
    """
    raise SystemExit(
        "DG Flame MCP is in pre-alpha development. "
        "The live Flame connection PoC has not been implemented yet."
    )


if __name__ == "__main__":
    main()
