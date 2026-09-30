# Phase 1: Flame connection PoC

This document describes the first executable connection experiment for DG Flame MCP.

The implementation is intentionally small. It is not a final transport decision, and it is not a claim that the bridge has already been validated on a live Flame workstation.

## Implemented in this PoC

- MCP server using the MCP Python SDK.
- Flame-side bridge that can be started from Flame Python.
- Experimental Unix-domain socket transport.
- Newline-delimited JSON request/response protocol.
- Normalized result and error envelopes.
- Main-thread scheduling through `flame.schedule_idle_event`.
- State handlers for Flame version, project/workspace, current tab, and Media Panel selection.
- A safe Python API mutation experiment using `flame.set_current_tab`.
- Experimental native-action hooks for `flame.execute_shortcut` and `flame.press_button`.
- Unit tests that run without Autodesk Flame.

## Process layout

```text
MCP Client
    |
    | MCP over stdio
    v
DG Flame MCP Server
    |
    | local Unix-domain socket
    | newline-delimited JSON
    v
Flame Bridge listener thread
    |
    | flame.schedule_idle_event(...)
    v
Flame main application thread
    |
    v
Autodesk Flame
```

The Unix-domain socket is an experiment, not an architectural commitment. Keep it only if it proves reliable on a real Flame workstation.

## Local protocol

The default socket is per-user:

```text
/tmp/dg-flame-mcp-<uid>.sock
```

Override it in both processes with `DG_FLAME_MCP_SOCKET`.

Each connection carries one request and one response. Messages are UTF-8 JSON terminated by a newline.

Responses always report the selected backend. Successful mutations can also contain a verification object. Errors use a normalized object with type, message, and optional details.

## Development

Install from a checkout:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

Run the MCP server over stdio:

```bash
dg-flame-mcp
```

## Start the bridge inside Flame

If the repository `src` directory is already on Flame's Python path:

```python
from dg_flame_mcp.flame_bridge import start_bridge

start_bridge()
```

For a checkout-based PoC, add the source directory first:

```python
import sys
sys.path.insert(0, "/path/to/dg-flame-mcp/src")

from dg_flame_mcp.flame_bridge import start_bridge
start_bridge()
```

Stop it with:

```python
from dg_flame_mcp.flame_bridge import stop_bridge
stop_bridge()
```

## MCP tools

Observation:

- `flame.status`
- `flame.capabilities`
- `flame.get_context`
- `flame.get_selection`

The first `get_selection` implementation means Media Panel selection only. Other selection contexts should be added after the initial connection is proven.

Safe Python API mutation:

- `flame.set_current_tab`

This performs the mutation and then reads `flame.get_current_tab()` again. Success is verified from observed state rather than only from the return value of the setter.

Experimental native paths:

- `flame.execute_shortcut`
- `flame.press_button`

Native actions are disabled by default. Enable them only in a disposable test project:

```python
start_bridge(enable_native_actions=True)
```

These hooks deliberately do not claim generic semantic verification. The first beyond-the-API experiment must select one concrete operation and define the observable state that proves it succeeded.

## Live Flame validation checklist

1. Open a disposable Flame project.
2. Start the Flame bridge.
3. Start the MCP server as the same OS user.
4. Call `flame.status` and confirm the reported version/project.
5. Change Media Panel selection and confirm `flame.get_selection` changes.
6. Call `flame.set_current_tab` and confirm both the visible UI change and `verification.ok == true`.
7. Repeat observation and tab switching enough times to expose scheduling/transport instability.
8. Restart the bridge and confirm stale socket cleanup behaves correctly.
9. Only then enable native actions.
10. Pick one controlled shortcut or button operation.
11. Define a post-action observation that proves success.
12. Run the operation and verify that state.

## Questions still requiring a real Flame workstation

- Is `flame.schedule_idle_event` reliable when requested from the bridge listener thread?
- Is blocking that listener thread while waiting for the idle callback stable over repeated calls?
- Does the Unix-domain socket remain reliable through normal project/workspace changes?
- Which state observations are required beyond project, tab, and Media Panel selection?
- Which shortcut/button is the best first beyond-the-API proof?
- What semantic verifier should be paired with that native action?
- Should the bridge ultimately load manually, at startup, or via a Flame hook?

Do not mark the Phase 1 exit condition complete until the live-workstation checks pass.
