# Roadmap

This roadmap prioritizes **learning what is actually possible in Autodesk Flame** over building a large API surface too early.

## Guiding objective

> **If a human can do it in Flame, an AI agent should eventually be able to do it too.**

The central research problem is not "How many Flame Python methods can we wrap?"

It is:

> **How can an MCP agent reliably complete Flame operations even when the official Python API is incomplete?**

---

## Phase 0 - Foundation

Goal: establish the project identity and a minimal runnable package.

- [x] Define project concept
- [x] Define capability-first architecture
- [x] Define Observe -> Plan -> Act -> Verify loop
- [x] Document relationship to prior Flame MCP work
- [x] Create minimal MCP server package
- [x] Add development instructions
- [x] Add basic tests
- [x] Define first experimental protocol between MCP server and Flame

Exit condition:

A developer can install the project and run a minimal MCP server locally.

---

## Phase 1 - Flame connection PoC

Goal: prove reliable two-way communication with Flame.

A minimal bridge, Unix-domain socket transport, state handlers, normalized results, and main-thread scheduler are now implemented for testing. The checklist below remains open until those paths are validated on a live Flame workstation. See [Phase 1 PoC](PHASE1_POC.md).

- [ ] Create minimal Flame-side bridge
- [ ] Establish local transport
- [ ] Query Flame version
- [ ] Query current project/context
- [ ] Query current selection
- [ ] Execute one known-safe Flame Python API call
- [ ] Return normalized result/errors
- [ ] Confirm correct main-thread scheduling behavior

Exit condition:

An MCP client can inspect a live Flame session and execute a simple operation reliably.

---

## Phase 2 - Capability discovery

Goal: stop treating Flame as a single API surface.

- [ ] Define capability schema
- [ ] Report available execution backends
- [ ] Detect Python API capabilities
- [ ] Experiment with `execute_shortcut`
- [ ] Experiment with `press_button`
- [ ] Experiment with command execution
- [ ] Record Flame-version-specific behavior
- [ ] Add execution trace logging

Exit condition:

The MCP client can ask what execution paths are currently available and select among more than one.

---

## Phase 3 - Beyond-the-API PoC

Goal: prove the core project thesis.

Find one useful Flame operation that is difficult or unavailable through the normal documented high-level Python API and complete it through another path.

Candidate paths:

- shortcut
- button action
- command
- raw Python
- preset/setup manipulation
- external utility
- Wiretap

Required for the experiment:

- [ ] Observe initial state
- [ ] Execute through non-standard path
- [ ] Observe resulting state
- [ ] Verify intended result
- [ ] Document reliability and failure modes

Exit condition:

DG Flame MCP demonstrates a useful operation that goes meaningfully beyond a conventional API wrapper.

---

## Phase 4 - Batch as the first deep workflow

Goal: provide enough Batch understanding to support useful AI-assisted compositing workflows.

Potential capabilities:

- [ ] inspect current Batch
- [ ] enumerate nodes
- [ ] inspect node types
- [ ] inspect connections
- [ ] create nodes
- [ ] connect/disconnect nodes
- [ ] inspect and set accessible parameters
- [ ] identify unsupported node operations
- [ ] fall back to alternate execution paths where required
- [ ] verify resulting graph

Why Batch first:

Batch gives a contained environment for testing state understanding, graph reasoning, mutation, and verification without trying to automate all of Flame at once.

---

## Phase 5 - UI automation research

Goal: determine whether visual computer use can become a reliable last-resort execution backend.

Experiments:

- [ ] capture Flame UI state
- [ ] identify stable screen regions / elements
- [ ] click a known UI target
- [ ] type into a controlled field
- [ ] perform a drag interaction
- [ ] verify visual result
- [ ] recover from unexpected dialogs
- [ ] measure reliability across UI layouts / resolutions

Principle:

> A UI action is incomplete until its result is verified.

Exit condition:

A small but real Flame operation unavailable through lower-level interfaces can be completed and verified using UI automation.

---

## Phase 6 - Execution strategy

Goal: allow the agent to choose the best backend for a requested operation.

Conceptual selection:

```text
Can a stable structured operation do it?
  -> yes: use it
  -> no:

Can the Flame Python API do it?
  -> yes: use it
  -> no:

Can a native command / shortcut / button do it?
  -> yes: use it
  -> no:

Can raw Python or an extension do it?
  -> yes: use it
  -> no:

Can an external tool / preset / Wiretap do it?
  -> yes: use it
  -> no:

Can a human do it in the UI?
  -> yes: attempt computer use
  -> no: report capability gap
```

Future work:

- [ ] backend scoring
- [ ] reliability history
- [ ] backend preference
- [ ] fallback after failure
- [ ] verification-driven retries
- [ ] capability caching

---

## Phase 7 - Production workflows

Only after the control foundation works reliably.

Candidates:

- Timeline operations
- Media Panel workflows
- import / conform
- render
- export / delivery
- versioning
- publish workflows
- Flow Production Tracking
- production-specific extensions

---

## Phase 8 - Extensions

Possible first-party or community extensions:

- Matchbox generation
- shader_builder integration
- conform helpers
- delivery tooling
- naming / validation rules
- studio-specific pipeline actions
- diagnostic / support tools

Extensions should be able to add capabilities without modifying the core MCP server.

---

## Research backlog

Topics worth exploring:

- undocumented-but-stable Flame actions
- PySide / Qt visibility from Flame Python
- internal widget discovery
- keyboard shortcut enumeration
- Flame command enumeration
- setup/preset formats
- Wiretap coverage
- Flame-specific screen understanding
- undo / transaction behavior
- crash recovery
- agent-safe state snapshots
- action history and replay
- semantic verification of visual operations

---

## v0.1 target

The first version should **not** attempt broad Flame coverage.

v0.1 is successful if it can demonstrate:

1. MCP connection to a live Flame session.
2. Reliable state inspection.
3. One operation through the normal Python API.
4. One useful operation through a different execution path.
5. Verification that both operations actually succeeded.
6. Clear logs showing how each action was performed.

That is enough to validate the core idea before scaling the tool surface.
