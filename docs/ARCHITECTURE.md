# Architecture

DG Flame MCP is designed around one idea:

> **The Python API is not the boundary. It is just one of the tools.**

The architecture must therefore support multiple execution paths without making any single path the definition of what the project can do.

## High-level architecture

```text
MCP Client / AI Agent
        |
        v
+---------------------------+
| DG Flame MCP Server       |
|---------------------------|
| Capability discovery      |
| Planning / path selection |
| Tool schemas              |
| Execution requests        |
| Verification requests     |
+-------------+-------------+
              |
              v
+---------------------------+
| Flame Bridge              |
|---------------------------|
| Flame-thread scheduling   |
| State inspection          |
| Capability adapters       |
| Result normalization      |
+-------------+-------------+
              |
      +-------+-------+------------------+------------------+
      |               |                  |                  |
      v               v                  v                  v
 Python API      Native actions      Raw Python       External tools
      |          shortcuts/buttons        |          presets/Wiretap/etc.
      +---------------+-------------------+------------------+
                              |
                              v
                        Autodesk Flame

Later:
                              |
                              v
                      UI / Computer Use
```

## Core loop

Every meaningful operation should follow:

```text
Observe -> Plan -> Act -> Observe -> Verify
```

### Observe

Collect enough state to understand the current Flame context.

Examples:

- current project
- selected clips
- active Batch group
- Batch nodes and connections
- current desktop / tab / panel
- visible UI state when computer use is involved

### Plan

Choose the most appropriate execution path.

The planner should prefer:

1. direct, deterministic Flame APIs
2. native commands / shortcuts / buttons
3. structured extension operations
4. raw Python
5. external tools / preset or file manipulation
6. UI automation

This is a preference order, not a hard policy. Some operations may be more reliable through a lower-level path.

### Act

Execute the selected capability.

### Verify

Re-read Flame state and confirm the desired effect.

Verification should be semantic where possible. For example:

- confirm that a node exists, not merely that a create call returned
- confirm that a connection changed, not merely that a click occurred
- confirm that an exported file exists and matches expected properties
- confirm that the intended UI state changed after a visual interaction

## Capability model

A capability is a discoverable execution method with metadata.

Conceptually:

```python
Capability(
    name="batch.create_node",
    backend="python_api",
    available=True,
    destructive=False,
    verifiable=True,
)
```

The server should eventually be able to answer questions such as:

- Which backends are available in this Flame version?
- Can this operation be executed directly?
- Is a shortcut registered?
- Is UI automation available?
- Can the result be verified programmatically?

## Execution backends

### 1. Flame Python API

Preferred when an official or stable Python interface exists.

Advantages:

- deterministic
- inspectable
- easier to test
- generally easier to verify

Limitation:

- significant portions of Flame remain inaccessible or awkward through the documented API

### 2. Native commands, shortcuts, and buttons

Flame exposes useful actions through mechanisms such as shortcuts, button invocation, tab changes, and command execution.

These should be treated as first-class execution paths rather than incidental hacks.

### 3. Raw Python

Raw Python is an intentional escape hatch.

It exists because restricting the project to pre-defined tools would conflict with the project's goal of maximizing practical Flame control.

Raw Python should not become the only architecture. It should be:

- explicit
- easy to disable
- observable
- logged
- used when more structured capabilities are insufficient

### 4. External tools and file-based control

Some workflows may be easier or only possible through:

- shell tools
- Flame setup or preset files
- generated resources
- Autodesk utilities
- Wiretap
- shader_builder
- production pipeline tools

These belong behind adapters so the MCP layer does not need to understand every low-level implementation detail.

### 5. UI automation / computer use

UI automation is the long-term fallback when an operation is available to a human operator but not exposed through programmable interfaces.

This backend requires a stronger verification loop.

A successful click is not a successful operation.

The UI backend should eventually support:

- screenshots
- element / region understanding
- mouse interaction
- keyboard input
- drag and drop
- post-action visual verification

## Flame Bridge

The Flame Bridge runs inside or alongside Flame and provides the controlled interface between the MCP server and Flame's execution environment.

Responsibilities:

- receive structured requests
- schedule Flame-sensitive work correctly
- invoke execution backends
- serialize results
- expose capability availability
- normalize exceptions
- keep MCP transport concerns out of Flame-specific implementation

The exact transport is intentionally not locked yet.

Candidates include:

- Unix domain sockets
- local IPC
- stdio subprocess arrangements
- another local-only mechanism proven reliable in Flame environments

The PoC should choose based on real Flame testing rather than aesthetic preference.

## Threading

Flame API calls may need to execute on Flame's main application thread.

The Bridge should isolate transport handling from Flame execution and use the appropriate Flame scheduling mechanism where required.

The architecture must avoid assuming that incoming MCP or socket callbacks can safely mutate Flame state directly.

## Tool surface

The first MCP tool surface should be small.

Candidate early tools:

- `flame.status`
- `flame.capabilities`
- `flame.get_context`
- `flame.get_selection`
- `flame.execute_operation`
- `flame.execute_python`
- `flame.execute_shortcut`
- `flame.press_button`
- `flame.verify`

This list is provisional.

The project should avoid creating dozens of narrowly mapped tools before validating which abstractions are actually useful.

## Model independence

DG Flame MCP should not depend on a specific AI model.

The MCP server exposes capabilities. Planning may be performed by:

- ChatGPT
- Codex
- Claude
- another MCP client
- a local model
- future agent frameworks

The Flame integration should remain useful even as client models change.

## Version adaptation

Flame versions may expose different APIs and behaviors.

Version-specific differences should eventually be isolated behind adapters or capability probes rather than scattered across the MCP tool surface.

Possible structure:

```text
adapters/
  flame_2026.py
  flame_2027.py
  common.py
```

This should only be introduced once real version differences justify it.

## Safety philosophy

This project optimizes for capability, not for pretending dangerous operations do not exist.

Safety mechanisms should therefore focus on visibility and control:

- explicit destructive metadata
- configurable raw Python
- execution logs
- optional confirmation policies
- dry-run where meaningful
- clear distinction between observation and mutation
- result verification

Security boundaries must be enforced by the component that actually controls the capability, not only by descriptive MCP annotations.

## Logging and reproducibility

Every execution should eventually be representable as a trace:

```text
request
selected capability
input arguments
execution backend
result
verification method
verification result
```

This trace will be important for:

- debugging
- reproducibility
- evaluating reliability
- improving planning
- comparing execution paths
- production adoption

## Initial architectural questions

The first PoC should resolve these before the project expands:

1. What is the most reliable local transport between MCP server and Flame?
2. Which calls require Flame main-thread scheduling?
3. Which non-Python-API controls are practical and stable?
4. How can current Flame context be inspected consistently?
5. How should capabilities advertise availability?
6. How should raw Python be executed and reported?
7. What can be verified automatically?
8. What UI automation approach is viable on real Flame workstations?

Until these are answered through real testing, the architecture should remain deliberately lightweight.
