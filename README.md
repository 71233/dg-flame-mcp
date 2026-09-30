# DG Flame MCP

**A high-freedom MCP interface for Autodesk Flame.**

> **If a human can do it in Flame, an AI agent should eventually be able to do it too.**

DG Flame MCP is an open-source project for connecting AI agents to Autodesk Flame through the Model Context Protocol (MCP).

The project is intentionally broader than a wrapper around the official Flame Python API. The Python API is one execution path among several. The long-term goal is to let an agent choose the best available way to complete a task, including cases where the official API does not expose the required operation.

> **The Python API is not the boundary. It is just one of the tools.**

## Status

**Early experimental development.**

The initial focus is not API coverage. The first goal is to prove that an MCP-connected agent can reliably operate Flame across multiple execution paths, especially for actions that are difficult or impossible through the documented Python API alone.

Expect breaking changes while the architecture is being validated.

A first Phase 1 connection implementation is available for live-Flame testing: MCP-over-stdio on the client side, an experimental local Unix-domain socket bridge, main-thread scheduling, state inspection, and a verified tab-switching operation. See [Phase 1 PoC](docs/PHASE1_POC.md).

## Goals

- Provide an MCP-native interface for Autodesk Flame.
- Maximize practical control rather than limiting the project to documented Python APIs.
- Prefer the most reliable execution path available for each task.
- Support both structured operations and escape hatches for advanced workflows.
- Allow the agent to inspect Flame before acting and verify the resulting state afterward.
- Remain model-agnostic: ChatGPT, Codex, Claude, local models, and other MCP clients should be able to use the same Flame capabilities.
- Build an extensible foundation for future capabilities such as Matchbox generation, conform, delivery, Flow Production Tracking integration, and production-specific extensions.

## Non-goals

DG Flame MCP is **not** intended to be:

- A thin one-to-one wrapper around the Flame Python API.
- Tied to a single AI model or vendor.
- Limited to operations that Autodesk exposes as high-level Python methods.
- A replacement for Flame's own scripting ecosystem.
- A guarantee that every execution path is equally safe or deterministic.

Freedom and capability are primary goals. Risky execution paths should be explicit, observable, and configurable rather than silently pretending they do not exist.

## Core Principles

### 1. Freedom first

Prefer practical capability over artificial limitations.

If an operation cannot be completed through one interface, the system should be able to fall back to another appropriate execution path.

### 2. Use the best available path

Use the official API when it is the best tool, but do not treat it as the only tool.

Planned execution paths include:

1. **Flame Python API**
2. **Native Flame commands**
3. **Shortcuts and button actions**
4. **Raw Python execution**
5. **External tools and command-line utilities**
6. **Preset / setup / file-based manipulation**
7. **Wiretap and other Autodesk interfaces where appropriate**
8. **Visual UI automation / computer use**
9. **Future execution methods discovered by the community**

### 3. Observe → Plan → Act → Verify

An action is not complete because a command was sent.

The agent should:

1. **Observe** the current Flame state.
2. **Plan** the desired change and select an execution path.
3. **Act** using the selected capability.
4. **Observe again**.
5. **Verify** that the intended result actually occurred.

This becomes increasingly important as the project moves beyond deterministic Python API calls into UI automation and mixed execution paths.

## Capability Ladder

DG Flame MCP will treat Flame control as a capability ladder rather than a single API surface.

```text
AI / MCP Client
      |
      v
DG Flame MCP
      |
      +--> Structured Flame operations
      |
      +--> Flame Python API
      |
      +--> Native commands / shortcuts / buttons
      |
      +--> Raw Python
      |
      +--> External tools / files / presets / Wiretap
      |
      +--> Visual UI automation
      |
      v
Autodesk Flame
```

The agent should generally prefer the most direct and verifiable path that can complete the task, while retaining lower-level fallbacks when higher-level interfaces are insufficient.

## Why another Flame MCP project?

There is already important prior work in the Flame community, including [abrahamADSK/flame-mcp](https://github.com/abrahamADSK/flame-mcp).

DG Flame MCP is not intended as a dismissive replacement for that work. It explores a different emphasis:

- MCP remains central, but **Flame control is not restricted to Python API coverage**.
- Multiple execution backends are treated as first-class capabilities.
- **API gaps are a core design problem**, not merely unsupported cases.
- UI-level operation is considered a legitimate eventual fallback.
- The architecture is built around **capability discovery, execution-path selection, and verification**.

Where useful and license-compatible, prior art should be acknowledged and learned from rather than unnecessarily reinvented.

## Initial Proof of Concept

The first meaningful milestone is deliberately small:

> **Demonstrate that an MCP client can inspect Flame, perform at least one useful operation through the normal Python API, perform at least one useful operation through a non-standard path, and verify both results.**

The PoC should answer:

- How should the MCP server communicate with the process running inside Flame?
- Which Flame operations are safe to call directly, and which need to be scheduled on Flame's main thread?
- What can be reached through Python API, shortcuts, button actions, commands, or other internal hooks?
- How can the system discover which capabilities are currently available?
- How should raw Python be exposed without making it the only architecture?
- How can UI automation observe enough state to act reliably?
- How should execution results be verified?

See [Architecture](docs/ARCHITECTURE.md) and [Roadmap](docs/ROADMAP.md).

## Proposed Project Structure

```text
dg-flame-mcp/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PHASE1_POC.md
│   └── ROADMAP.md
├── src/
│   └── dg_flame_mcp/
│       ├── __init__.py
│       ├── bridge_client.py
│       ├── flame_bridge.py
│       ├── protocol.py
│       └── server.py
├── .gitignore
├── LICENSE
├── pyproject.toml
└── README.md
```

The package structure will remain intentionally small until the first Flame-side PoC validates the architecture.

## Development Philosophy

Do not add abstractions simply because they look clean on paper.

A new abstraction should solve a real Flame integration problem discovered through testing.

In particular:

- Do not build dozens of MCP tools before proving the connection and execution model.
- Do not assume the Python API is the only reliable route.
- Do not assume UI automation is necessary when a lower-level route exists.
- Do not report success until the resulting Flame state has been checked.
- Preserve escape hatches for expert users and future capabilities.

## Licensing

DG Flame MCP is released under the MIT License. See [LICENSE](LICENSE).

Autodesk Flame is a product of Autodesk, Inc. This project is independent and is not affiliated with or endorsed by Autodesk.

## Contributing

The project is at an early architecture stage. Issues, experiments, Flame API findings, undocumented behavior reports, and reproducible examples are especially valuable.

Before contributing a large implementation, please prefer a small PoC or issue describing:

- the Flame version,
- the desired operation,
- which execution paths were tested,
- what worked,
- what failed,
- and how the result was verified.

---

**DG Flame MCP**

**The Python API is not the boundary. It is just one of the tools.**
