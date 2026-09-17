# Phase 30: Builder-First Construction & Persistence Parity - Research

**Researched:** 2026-09-17
**Domain:** Python FSM construction adapters, declarative metadata, compatibility deprecation, and topology persistence
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `FSMBuilder` is the primary public interface for new programmatic machine construction. Public API reference and migration guidance should lead with it; examples outside explicit compatibility tests should converge on it as their construction mechanism. — **Reversibility:** costly — changing the primary interface again would churn documentation, examples, and user code.
- **D-02:** Direct `StateMachine` and `AsyncStateMachine` construction remains supported, public, and non-deprecated as the advanced interface for users who need explicit state identity or incremental topology control.
- **D-03:** `StateMachine.from_dict()` and `AsyncStateMachine.from_dict()` remain the supported adapter for declarative external topology data. They are not a competing general-purpose programmatic builder, and no second public construction abstraction is added.
- **D-04:** Builder operations continue to accept caller-owned `State` identities and retain fluent mutation before the first successful `build()`. A successful build keeps the established cached/immutable builder behavior; a failed build leaves the staged builder inspectable and repairable.
- **D-05:** `@transition` declarations gain or preserve every canonical transition scalar needed by v0.5.0, including exact priority, timing, and keyword-only `internal=False`; declaration metadata is immutable and validated before builder staging. — **Reversibility:** costly — decorator metadata becomes a public authoring contract.
- **D-06:** Adding a `DeclarativeState` or `AsyncDeclarativeState` to `FSMBuilder` imports its decorated transition declarations into ordinary `_TransitionRequest` values and publishes them only through the canonical construction transaction at `build()`. There is no declarative-only topology table, registrar, or second builder class.
- **D-07:** Declaration discovery must preserve canonical source and destination identity, final-state rejection, internal self-target validation, priority ordering, timing fields, async auto-detection, and exactly-once handler execution. Explicit and declarative declarations that collide are rejected by the same duplicate/candidate rules rather than silently overwriting one another.
- **D-08:** Direct `handle_event()` / `handle_event_async()` state behavior remains available for compatibility, but machine topology and machine-owned dispatch semantics are authored and validated through the builder/canonical registrar.
- **D-09:** `simple_fsm`, `quick_fsm`, `StateMachine.quick_build`, and `StateMachine.from_states` remain callable but emit one actionable `DeprecationWarning` at the user call site (`stacklevel=2`) naming the `FSMBuilder` replacement. Direct constructors, `from_dict()`, `State.create()`, and declarative state classes are not deprecated.
- **D-10:** The convenience constructors remain behaviorally supported throughout the v0.5.x compatibility cycle and may be removed no earlier than v0.6.0. Their runtime, typing, atomicity, final-state, and transition-mode behavior must remain correct until removal. — **Reversibility:** one-way — once removal ships, restoring these symbols would recreate a public compatibility contract.
- **D-11:** Deprecation wording is fixed and bounded, does not echo caller payloads, and distinguishes programmatic replacement (`FSMBuilder`) from serialized reconstruction (`from_dict`). Tests assert warning category, exact call-site attribution, one warning per public invocation, and continued correct construction.
- **D-12:** Phase 30 may update focused API/deprecation reference material and migrate code examples needed to prevent new use of the helpers. Phase 32 owns the full progressive README/Sphinx tutorial and release-facing migration walkthrough.
- **D-13:** Topology dictionaries keep `states: list[str]` and add only deterministic, JSON-native metadata: the existing top-level `final_states` list and transition-row `internal` scalar. `internal` is emitted only when true; absence or explicit false reads as external. Old dictionaries without either field reconstruct non-final states and external transitions. — **Reversibility:** one-way — emitted dictionary fields become a persisted interoperability contract.
- **D-14:** `from_dict()` validates the complete input before candidate publication: exact container/scalar types, unique known final names, exact booleans, internal self-target identity, no outgoing final-source edge, condition references, timing, priority, and row context. A malformed document returns no partial machine and exposes no executable callback or exception payload.
- **D-15:** Compatibility is directional and stated truthfully: old payload → new reader and new payload → new reader are supported; a pre-v0.5 reader may ignore additive metadata and lose semantics. Phase 30 does not add a schema-version key that older readers cannot enforce or claim symmetric new→old semantic safety.
- **D-16:** `clone()` preserves final-state and internal-transition meaning, selected state subclasses, immutable state/entry identities where established, async machine type, and independent topology/callback containers. It retains the existing reset-to-initial behavior rather than copying live current state or history.
- **D-17:** `snapshot()` / `restore()` remains format v1 and state-only. It gains no topology, final-state, or transition-mode fields; termination after restore derives immediately from the receiving machine's canonical current `State.final`, and transition mode remains topology owned.
- **D-18:** Direct, batch, builder, legacy factory/helper, declarative, callback-state, clone, and deserialization paths all converge on `_TransitionRequest` plus the Phase 26 prepare-all/publish-once seam. No adapter performs post-publication semantic repair.
- **D-19:** The parity oracle replays the same final/internal topology across synchronous and asynchronous machines, pure and freshly compiled runtimes, and every retained adapter. It compares observable semantics and atomic failure, not merely dictionary equality.
- **D-20:** Deprecated helpers stay inside the parity matrix for the compatibility cycle. Structural tests also prove that adapter code does not bypass canonical normalization, weaken exact-type checks, mutate graph version on failure, or introduce dispatch-time work.

### the agent's Discretion

- Exact private helper names, staging order within a no-user-code construction transaction, warning constant placement, and test-file partitioning.
- Whether declarative import occurs eagerly on `add_state()` into a temporary validated staging plan or at `build()` from immutable metadata, provided builder mutation remains atomic and conflicts surface before machine publication.
- Exact deterministic dictionary key ordering and whether explicit `internal: false` is accepted on input, provided output omits false, both absent/false read as external, and validation remains exact.

### Deferred Ideas (OUT OF SCOPE)

- Final/internal/rejection projection through validators, JSON diagnostics, Mermaid, and PlantUML — Phase 31.
- Full progressive README/Sphinx restructuring, drone tutorial migration, installed-artifact proof, and release-facing migration walkthrough — Phase 32.
- Immediate removal of deprecated helpers, a topology snapshot v2, executable callback serialization, and a second declarative builder remain outside v0.5.0.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BUILD-01 | Users are guided to `FSMBuilder` as the primary construction interface, direct machine construction as the advanced interface, and `from_dict` as the serialization adapter. | Focused documentation inventory and builder-first migration boundary. [VERIFIED: `.planning/REQUIREMENTS.md:38-42`] |
| BUILD-02 | Users can author declarative behavior through the canonical construction machinery without a separate topology implementation. | Build-time metadata-to-request derivation and one canonical apply transaction. [VERIFIED: `.planning/REQUIREMENTS.md:40-42`] |
| BUILD-03 | Users of `simple_fsm`, `quick_fsm`, `StateMachine.quick_build`, and `StateMachine.from_states` receive documented deprecation guidance and a supported compatibility cycle. | Direct-entry warning design, bounded constants, and compatibility parity tests. [VERIFIED: `.planning/REQUIREMENTS.md:40-44`] |
| BUILD-06 | Users receive identical final-state and transition-mode validation through direct, batch, builder, factory, declarative, helper, callback, clone, and deserialization paths. | Adapter matrix around `_TransitionRequest`, exact type boundaries, and atomic failure fingerprints. [VERIFIED: `.planning/REQUIREMENTS.md:43-46`] |
| BUILD-07 | Users can clone and serialize machines without losing final-state or internal-transition metadata, while older serialized data receives backward-compatible defaults. | True-only dictionary emission, legacy defaults, clone identity/isolation assertions, and directional compatibility. [VERIFIED: `.planning/REQUIREMENTS.md:45-47`] |
| BUILD-08 | Users can continue using snapshot format v1, with termination derived from the receiving machine's current state and topology. | Exact snapshot-schema lock and receiving-topology restore oracle. [VERIFIED: `.planning/REQUIREMENTS.md:46-47`] |
</phase_requirements>

## Summary

Phase 30 should be planned as a cold-path convergence phase, not as a new FSM runtime. The Phase 26 spine already exists: raw adapter values become frozen `_TransitionRequest` rows, the complete tuple is normalized, replacement slots are built off-table, and publication occurs once. The carrier fields are verbatim `"trigger", "sources", "to_state", "condition", "unless", "priority", "condition_ref", "after", "within", "internal"`. [VERIFIED: `src/fast_fsm/core.py:823-862`; `src/fast_fsm/core.py:2029-2073`] The phase's safest shape is therefore to derive declarative requests at `FSMBuilder.build()`, append them to bound explicit requests, and make exactly one `_apply_transition_requests_owned()` call on the private candidate. [VERIFIED: `src/fast_fsm/core.py:6568-6630`; locked D-06/D-18]

The principal implementation gap is not transition validation; it is metadata transport. Current decorator rows contain verbatim `"trigger", "from_state", "to_state", "condition", "priority", "after", "within"` and omit `"internal"`; the builder scans those rows for async requirements but does not convert them to topology, so tests manually mirror decorator rows through `builder.add_transition()`. [VERIFIED: `src/fast_fsm/core.py:865-889`; `src/fast_fsm/core.py:5591-5639`; `src/fast_fsm/core.py:6517-6566`; `tests/test_builder.py:1129-1155`] The implementation must also avoid copying a decorator guard into the transition entry: runtime selection already evaluates the entry guard and then the matched declarative guard, so copying one object into both channels would run it twice. [VERIFIED: `src/fast_fsm/core.py:2940-2958`; `src/fast_fsm/core.py:5991-6004`]

Persistence has one real production gap: `to_dict()` already emits `"name", "initial", "states", "final_states", "transitions"`, but transition rows do not emit `internal`, and `from_dict()` neither parses nor forwards it. [VERIFIED: `src/fast_fsm/core.py:1466-1477`; `src/fast_fsm/core.py:1627-1665`; `src/fast_fsm/core.py:1667-1709`] Clone and snapshot behavior are substantially already correct and should be locked with stronger parity tests rather than redesigned: clone reuses canonical State objects, reconstructs independent entries including `entry.internal`, resets current state/history, and preserves the concrete machine class; snapshot is exactly `{"state": self._current_state.name, "version": 1}`. [VERIFIED: `src/fast_fsm/core.py:3629-3711`; `src/fast_fsm/core.py:3578-3627`]

**Primary recommendation:** implement Phase 30 in four bounded workstreams—declarative metadata/import, deprecated-wrapper compatibility, dictionary/clone/snapshot parity, then a unified structural + pure/native evidence gate—without adding a second builder, schema version, runtime dependency, or dispatch-time policy.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Programmatic authoring | Public construction API (`FSMBuilder`) | Direct machine API | Builder becomes the default recipe while direct construction remains the advanced public path. [VERIFIED: `.planning/phases/30-builder-first-construction-persistence-parity/30-CONTEXT.md:29-41`] |
| Declarative topology import | Builder cold path | Canonical construction core | State-owned immutable declarations are adapted to ordinary requests; the machine remains the sole semantic validator/publisher. [VERIFIED: `src/fast_fsm/core.py:5891-5984`; `src/fast_fsm/core.py:6568-6630`] |
| Topology validation/publication | Compiled canonical core | Adapter-specific parsers | `_normalize_transition_request()` owns final/mode/guard/timing checks and `_commit_transition_plan()` owns publication. [VERIFIED: `src/fast_fsm/core.py:1890-2002`; `src/fast_fsm/core.py:2004-2073`] |
| Serialized topology | `from_dict()` / `to_dict()` adapter | Canonical construction core | The adapter owns JSON-native shape and indexed context; it must not own semantic topology rules. [VERIFIED: `src/fast_fsm/core.py:1362-1709`] |
| Live state persistence | Snapshot/restore v1 | Receiving machine topology | Snapshot stores only state name and version; finality and mode stay topology-owned. [VERIFIED: `src/fast_fsm/core.py:3578-3627`] |
| Compatibility warnings | Four retained public entry points | Private non-warning construction workers | Each public invocation must warn once at its caller without nested helper warnings. [VERIFIED: current nesting at `src/fast_fsm/core.py:1198-1359` and `src/fast_fsm/core.py:6953-7012`; locked D-09/D-11] |
| Semantic parity evidence | Test oracle | Pure/native build harness | Observable lifecycle, finality, mode, atomic failure, identity, and version behavior matter more than serialized equality. [VERIFIED: `.planning/phases/26-canonical-construction-evidence-contract/26-VERIFICATION.md:29-43`; locked D-19/D-20] |

## Project Constraints (from AGENTS.md)

- Use the active `.planning/` artifacts as the GSD execution contract and do not create external GitHub work unless explicitly authorized. [VERIFIED: `AGENTS.md:15-17`]
- Use `uv` for Python/package/test commands; do not invoke bare `python`, `pip`, or `python -m pytest`. [VERIFIED: `.github/copilot-instructions.md:32-38`]
- Preserve slots and the compiled singleton throughput floor; builder work must remain one-time cold construction work and must not scan unrelated topology during dispatch. [VERIFIED: `.github/copilot-instructions.md:40-59`]
- Preserve `*args, **kwargs` callback/condition compatibility and use a deprecation cycle before public-symbol removal. [VERIFIED: `.github/copilot-instructions.md:61-64`]
- Run tests sequentially; use targeted tests during implementation and `uv run pytest tests/ -x -q` once before completion. [VERIFIED: `.github/copilot-instructions.md:66-72`]
- Mypy is the blocking mypyc-compatibility authority; ty is visible advisory feedback. [VERIFIED: `.github/copilot-instructions.md:152-167`]
- Keep `core.py` as the selective mypyc unit, keep condition modules interpreted for downstream subclassing, and preserve pure-Python behavior as a supported mode. [VERIFIED: `setup.py:16-39`; `.specify/memory/constitution.md:123-149`]
- Keep hot-path production classes slotted, use the recursive slots audit as authority, preserve direct singleton O(1) dispatch, and do not add construction validation to trigger/can-trigger paths. [VERIFIED: `.github/copilot-instructions.md:40-59`; `.specify/memory/constitution.md:108-121`]
- Tests must exercise real FSM computation; mock environment boundaries such as clocks, not transition/guard/dispatch logic. [VERIFIED: `.specify/memory/constitution.md:113-121`]
- Preserve the import DAG and do not split the compiled core for this phase. [VERIFIED: `.specify/memory/constitution.md:89-96,113-121`; `.planning/PROJECT.md:132-147`]
- Public API changes require synchronized runtime docstrings, PEP 561 stubs, README, and relevant Sphinx material. [VERIFIED: `.github/copilot-instructions.md:200-227`]
- Preserve unrelated dirty files and stage only explicit task paths; never use `git add .` or `git add -A`. [VERIFIED: `.github/copilot-instructions.md:121-124`]
- Ordinary implementation completion requires appropriate quality gates, an intentional-path commit, safe pull/rebase, push, and a clean/up-to-date status. [VERIFIED: `AGENTS.md:19-30`] The parent task explicitly forbids committing this research artifact, so that ordinary landing rule does not apply to this delegated research write.

## Standard Stack

### Core

| Library/tool | Version | Purpose | Why Standard |
|--------------|---------|---------|--------------|
| Python | Project supports `>=3.10`; local interpreter `3.12.10` | Runtime and tests | Keep syntax/API compatible with the declared floor. [VERIFIED: `pyproject.toml:1-9`; local `uv run python --version` probe] |
| `fast_fsm.core` | Project `0.4.0` baseline | All Phase 30 implementation seams | `setup.py` compiles only `src/fast_fsm/core.py`; conditions remain interpreted. [VERIFIED: `pyproject.toml:1-9`; `setup.py:16-39`] |
| mypy/mypyc | `1.17.1` release pin; local `1.17.1` | Blocking native compatibility | Existing build configuration and release group already pin the compiler. [VERIFIED: `pyproject.toml:22-26,41-43`; local version probe] |
| pytest | `>=8.4.1`; local `8.4.1` | Semantic, atomicity, structural, and parity tests | Existing sequential suite and strict markers are the merge gate. [VERIFIED: `pyproject.toml:11-20,54-70`; `Taskfile.yml:26-33`; local version probe] |
| Sphinx | `>=8.0`; local `9.1.0` | Focused API/deprecation docs | Existing tasks provide warnings-as-errors HTML and doctest gates. [VERIFIED: `pyproject.toml:31-36`; `Taskfile.yml:230-255`; local version probe] |

### Supporting

| Library/tool | Version | Purpose | When to Use |
|--------------|---------|---------|-------------|
| Ruff | `>=0.12.11` | Formatting and linting | Run on Phase 30 Python files before type/test gates. [VERIFIED: `pyproject.toml:11-20`; `Taskfile.yml:67-88`] |
| ty | `>=0.0.1a19` | Advisory type feedback | Run after blocking mypy and report separately. [VERIFIED: `pyproject.toml:11-20`; `Taskfile.yml:100-118`] |
| Existing release-evidence tooling | repository-local | Source-origin, slots, pure/native, and benchmark protection | Reuse the established Phase 28/29 fail-closed native-shadow protocol; do not create a new artifact harness. [VERIFIED: `Taskfile.yml:120-145,185-203`; `.planning/phases/29-expected-domain-rejection/29-04-PLAN.md:168-205`] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Build-time declarative derivation | Eagerly append derived rows during `add_state()` | Eager derivation requires rollback/re-derivation state and risks freezing mutable metadata earlier; build-time derivation needs no new builder slot and naturally participates in the already-private candidate transaction. The latter is recommended. |
| Private non-warning workers | Have helpers call other deprecated public helpers | Public-to-public nesting emits two warnings and misattributes one frame, violating D-11. |
| Additive `internal` field | Schema version 2 | A schema version does not make old readers enforce unknown semantics and is explicitly out of scope. |
| Existing canonical request seam | Declarative-specific registrar/table | A second registrar duplicates final/mode/timing/priority rules and violates D-06/D-18. |

**Installation:** no new package installation is required or recommended. The current dependency declaration remains verbatim `dependencies = ["mypy-extensions>=1.0"]`. [VERIFIED: `pyproject.toml:6-9`; `.planning/PROJECT.md:143-147`]

## Package Legitimacy Audit

Not applicable: Phase 30 installs no external package and adds no runtime dependency. [VERIFIED: locked phase boundary and `pyproject.toml:6-9`] No package-legitimacy gate is required.

## Current Behavior and Exact Gaps

| Surface | Current behavior | Phase 30 gap / planning consequence |
|---------|------------------|-------------------------------------|
| Canonical carrier | Frozen/slotted request and prepared rows already include `internal: Any = False` and `internal: bool = False`. [VERIFIED: `src/fast_fsm/core.py:823-862`] | Reuse them; no new transition API or parallel carrier. |
| Canonical transaction | All requests normalize before `_commit_transition_plan(tuple(prepared))`; equal-priority identity includes `entry.internal`. [VERIFIED: `src/fast_fsm/core.py:2029-2116`] | Every adapter/import path must submit one tuple and perform no post-publication repair. |
| Decorator metadata | Frozen/slotted metadata and handler records omit `internal`; `from_state` may retain a mutable caller list. [VERIFIED: `src/fast_fsm/core.py:865-889`; `src/fast_fsm/core.py:5591-5628`] | Add exact keyword-only mode, deep-freeze plural source metadata, and update structural field-set tests. |
| Handler identity | Discovery identity is verbatim `(metadata.trigger, metadata.from_state, metadata.to_state, metadata.priority)`. [VERIFIED: `src/fast_fsm/core.py:5932-5973`] | Include mode in declaration identity and in runtime matching, so an internal declaration cannot bind an external entry. |
| Builder | Builder holds states and explicit requests, scans declarative rows only for async requirements, and applies only explicit rows. [VERIFIED: `src/fast_fsm/core.py:6174-6248`; `src/fast_fsm/core.py:6517-6630`] | Derive applicable declaration requests at build and combine them before the single apply. Do not persist a second derived table. |
| Declarative tests | Priority parity currently duplicates decorator topology manually through `builder.add_transition()`. [VERIFIED: `tests/test_builder.py:1129-1155`; `tests/test_builder.py:2382-2403`] | Replace/manual-mirroring tests with builder-only declaration authoring and exactly-once guard/handler counters. |
| Deprecated surfaces | The four retained surfaces are callable, and `simple_fsm`/`quick_fsm` call the corresponding classmethod; none emits a deprecation warning. [VERIFIED: `src/fast_fsm/core.py:1198-1359`; `src/fast_fsm/core.py:6953-7012`] | Refactor shared construction into non-warning private workers or equivalent so each public boundary warns exactly once. |
| Dictionary output | `final_states` is present and sorted; transition rows emit priority/reference/timing but not mode. [VERIFIED: `src/fast_fsm/core.py:1667-1709`] | Add `"internal": True` only for internal entries; unchanged external rows preserve old output shape. |
| Dictionary input | Container/string checks mostly use `isinstance`; parsed rows have no internal field; requests omit it. [VERIFIED: `src/fast_fsm/core.py:1435-1656`] | Apply exact built-in container/scalar checks to serialized fields, parse absent/explicit false as external, and forward exact bool with indexed context. |
| Clone | Reuses the exact State dictionary, creates fresh transition tables/entries, forwards finality through State identity and `internal=entry.internal`, and resets current/history. [VERIFIED: `src/fast_fsm/core.py:3659-3711`] | Primarily an evidence task: expand subclass, callback-container, async type, live-state reset, and declarative-import parity tests. |
| Snapshot | Public schema is exactly `"state"` plus `"version": 1`; restore changes only current state. [VERIFIED: `src/fast_fsm/core.py:3578-3627`; `tests/test_graph_invariants.py:402-418`] | Freeze exact keys and prove that identical state snapshots restored into different receiving topologies derive different final/mode truth from those topologies. |
| Public typing | `transition()` stub has priority/timing but no `internal`; retained helpers remain public in stubs and exports. [VERIFIED: `src/fast_fsm/core.pyi:371-433,467-479`; `src/fast_fsm/__init__.py:7-33,75-111`] | Add decorator mode typing; retain deprecated symbols and callable signatures for the full cycle. |
| Guidance | README opens with direct `StateMachine`, presents helpers before the builder, and Quick Start begins with `simple_fsm` then `quick_build`. [VERIFIED: `README.md:1-20,67-150`; `docs/QUICK_START.md:25-78`] | Make only focused builder-first/deprecation edits now; defer the full progressive rewrite to Phase 32. |

## Architecture Patterns

### System Architecture Diagram

```text
Programmatic caller ───────────────┐
                                  ├─> FSMBuilder staging
Decorated State instance ─────────┘       │
                                          ├─ explicit _TransitionRequest rows
                                          └─ build-time derived declaration rows
                                                        │
Serialized topology ─> from_dict parser ─> _TransitionRequest tuple
Legacy public helper ─> warning boundary ─> private compatibility parser
                                                        │
                                                        v
                       private candidate StateMachine / AsyncStateMachine
                                                        │
                       normalize every request (identity/final/mode/timing/guard)
                                                        │
                       merge immutable replacement slots off-table
                                                        │
                       publish once + one graph-version advance iff changed
                                                        │
                                                        v
                               runtime dispatch (unchanged hot path)

clone() ─> request replay through the same transaction ─> independent topology
to_dict()/from_dict() ─> topology persistence (final + true-only internal)
snapshot()/restore() ─> state-only v1 (topology remains receiver-owned)
```

### Recommended Project Structure

```text
src/fast_fsm/core.py                       # implementation; remains one mypyc unit
src/fast_fsm/core.pyi                      # public decorator/builder/helper typing
src/fast_fsm/__init__.py                   # retained compatibility exports
tests/test_builder.py                      # declaration import + warnings/build reuse
tests/test_advanced_functionality.py       # dictionary parsing/round-trip contracts
tests/test_final_states.py                 # final/clone/snapshot receiving topology
tests/test_transition_modes.py             # internal observable semantics
tests/test_graph_invariants.py             # atomicity/version/no-bypass structure
tests/test_mypyc_guard.py                  # carrier/stub/pure-native structure
README.md                                  # focused builder-first correction
docs/QUICK_START.md                        # migrate early deprecated examples
docs/api/core.md                           # canonical hierarchy + deprecation notices
docs/dev/architecture.md                   # retained adapters described as compatibility
.specify/memory/spr-core-api.md             # living construction/persistence contract
```

### Pattern 1: Derive Declarative Requests at Build Time

**What:** Traverse the immutable handler tuples on each staged `DeclarativeState` inside `build()`, derive ordinary requests for declarations applicable to that exact state instance, concatenate with bound explicit rows, and call the canonical apply once.

**When to use:** For every builder candidate, after the complete private state registry exists and before callbacks or `_machine` publication.

**Required behavior:**

1. Treat the exact staged DeclarativeState object as the source; a declaration applies only when `from_state` is omitted or matches that object's canonical name. This preserves the existing state-owned resolver, which only reads `source_state._handlers`. [VERIFIED: `src/fast_fsm/core.py:5642-5670`]
2. A declaration without `to_state` remains direct-`handle_event*()` compatibility behavior and is not topology-complete; do not invent a destination. [VERIFIED: optional destination contract at `src/fast_fsm/core.py:5591-5612`; locked D-08]
3. Bind the destination through `self._states` only as an identity convenience; let canonical normalization reject unknown/foreign/final-source/internal-nonself cases. [VERIFIED: `src/fast_fsm/core.py:1866-1888,1920-1936`]
4. Put priority, timing, and internal mode on the request. Keep the declaration guard on `_DeclarativeHandler`, not on `request.condition`, because selectors already evaluate both channels in sequence. [VERIFIED: `src/fast_fsm/core.py:2940-2958`; `src/fast_fsm/core.py:5991-6004`]
5. Never append derived rows to `builder._transitions`; deriving afresh from immutable metadata on each failed attempt keeps staging inspectable and avoids hidden duplicate accumulation. Successful build remains cached by `_machine`. [VERIFIED: `src/fast_fsm/core.py:6250-6255,6568-6572,6589-6630`]

### Pattern 2: Deeply Immutable Decorator Metadata

**What:** Normalize public decorator scalars before attaching metadata and copy plural source constraints into an immutable tuple. The current frozen dataclass is not deeply immutable when it stores a caller-owned list. [VERIFIED: `src/fast_fsm/core.py:865-875`; `src/fast_fsm/core.py:5591-5628`]

**When to use:** At decorator invocation/discovery, before any builder observes the state.

Prescribe exact validation for the new mode using the existing canonical wording `"internal must be an exact built-in bool"`. [VERIFIED: `src/fast_fsm/core.py:1905-1907`; `src/fast_fsm/core.py:6357-6363`] Continue using implementation parameter type `object` until after the exact check, even though the stub advertises `bool`; this avoids mypyc narrowing/coercion before runtime validation. [VERIFIED: existing priority/timing/internal pattern at `src/fast_fsm/core.py:1898-1903` and `src/fast_fsm/core.py:6334-6363`]

Add `internal` to both immutable record layouts and to mode-aware matching. Machine-owned resolver call sites should pass `entry.internal`; direct compatibility calls should pass no mode filter and continue failing closed on ambiguity. Current machine call sites resolve by source/trigger/target/priority only. [VERIFIED: `src/fast_fsm/core.py:2795-2804,2940-2958,5272-5283`; `src/fast_fsm/core.py:5651-5701`]

Retain the established decorator compatibility attributes and add a bounded `_fsm_internal` attribute/fallback alongside the canonical tuple metadata; discovery should prefer the immutable `_fsm_declarations` tuple just as it does now. [VERIFIED: `src/fast_fsm/core.py:5616-5636`; `src/fast_fsm/core.py:5932-5952`]

### Pattern 3: One Warning Per Public Boundary

**What:** Put `warnings.warn(CONSTANT, DeprecationWarning, stacklevel=2)` directly inside each of the four deprecated public functions/methods as the first operation, then delegate to a private non-warning worker. This yields one warning even when later argument validation fails.

**When to use:** Only at the compatibility authoring entries, never in direct constructors, `from_dict`, `State.create`, builder methods, dispatch, or declaration classes.

Python documents that `stacklevel=2` attributes a wrapper warning to the wrapper's caller, while `DeprecationWarning` is normally ignored outside `__main__`; tests should force visibility with `catch_warnings(record=True)` and `simplefilter("always")`. [CITED: https://docs.python.org/3/library/warnings.html]

Use one fixed constant per symbol. Recommended bounded template:

```python
"<symbol> is deprecated and remains supported through v0.5.x; "
"use FSMBuilder for programmatic construction or StateMachine.from_dict() "
"for serialized topology. It may be removed no earlier than v0.6.0."
```

Do not let `simple_fsm()` call a warning-emitting `from_states()` or `quick_fsm()` call a warning-emitting `quick_build()`; the current nesting is verbatim `simple_fsm -> StateMachine.from_states` and `quick_fsm -> StateMachine.quick_build`. [VERIFIED: `src/fast_fsm/core.py:6956-7012`] Private workers must still accept/construct through `cls` so classmethod calls preserve the existing result subclass contract. [VERIFIED: `src/fast_fsm/core.py:1198-1247`]

### Pattern 4: Exact Two-Phase Dictionary Reconstruction

**What:** Parse and validate the complete JSON-native shape into local rows, create the private candidate/states, resolve opaque conditions without executing them, create the complete request tuple, then apply once with indexed contexts.

**When to use:** In both inherited `StateMachine.from_dict()` and `AsyncStateMachine.from_dict()` paths.

Required input behavior:

- Exact built-in `dict`/`list`/`str` checks for serialized containers/scalars rather than subclass-friendly `isinstance`; exact `bool` for `internal`. [VERIFIED: locked D-14; current weaker checks at `src/fast_fsm/core.py:1435-1456,1480-1519,1575-1593`]
- `entry.get("internal", False)` accepts omission and explicit exact false as external; exact true is internal; values such as `0`, `1`, string booleans, or truthy objects fail with `from_dict: transition[index] field 'internal' ...` context before apply.
- Keep unknown extra keys ignored unless already rejected elsewhere; Phase 30 adds semantics, not a closed schema.
- Preserve opaque `condition_ref` resolution and never serialize callable implementation details. [VERIFIED: `src/fast_fsm/core.py:1394-1411,1536-1573,1603-1625`]
- Let the canonical transaction enforce exact final-source and internal self-target identity; do not duplicate semantic repair after publication. [VERIFIED: `src/fast_fsm/core.py:1920-1936,2029-2073`]

Required output behavior: start from the existing record keys verbatim `"trigger", "from", "to", "priority"`; add `"internal": True` only when `entry.internal is True`, after optional timing/reference keys for stable insertion order. [VERIFIED: current record at `src/fast_fsm/core.py:1684-1700`; locked D-13]

### Pattern 5: Observable-Semantics Parity Oracle

**What:** Build the same small topology through every retained adapter, then assert state-object identity rules, final termination, external versus internal lifecycle traces, selected priority/mode, history, dictionary fields, clone independence/reset, atomic failure, and graph-version behavior.

**When to use:** First in pure source; repeat the same focused oracle from a freshly compiled native origin. The existing Phase 28/29 protocol brackets native build/test with fail-closed source-origin checks and recoverable relocation of only verified `core*.so`/`core*.pyd` shadows. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-VALIDATION.md:72-110`; `.planning/phases/29-expected-domain-rejection/29-04-PLAN.md:168-205`]

Do not use `to_dict()` equality as the sole parity oracle: guards/callbacks are intentionally not executable serialization, clone shares collaborator identities but not containers, and snapshot is state-only. [VERIFIED: `src/fast_fsm/core.py:1676-1678`; `src/fast_fsm/core.py:3629-3711`; locked D-16/D-17/D-19]

### Anti-Patterns to Avoid

- **Second declarative topology table:** duplicates candidate identity, final-source, timing, internal, collision, and graph-version policy.
- **Copying the decorator guard into `TransitionEntry.condition`:** evaluates the same policy once as entry guard and again as declarative guard.
- **Mutating builder staging while deriving declarations:** failed builds could accumulate duplicate hidden rows and cease being repairable.
- **Nested public deprecation wrappers:** produces multiple warnings and wrong call-site attribution.
- **Truthiness-based deserialization:** `bool("false")`, integer booleans, and hostile subclasses weaken the exact-mode contract.
- **Always emitting `internal: false`:** needlessly changes every serialized row and violates the true-only interoperability contract.
- **Adding topology to snapshot v1:** conflates live state with graph persistence and breaks the exact schema.
- **Only testing dictionary fingerprints:** misses lifecycle mode, handler/guard counts, identity, callback aliasing, and atomicity.
- **Putting warning/import logic in selectors:** deprecation and adapter work must stay out of the hot path.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Transition validation | Declarative-specific final/mode/timing checks | `_TransitionRequest` → `_apply_transition_requests_owned()` | The existing seam already prepares all rows and publishes once. [VERIFIED: `src/fast_fsm/core.py:2029-2073`] |
| Candidate collision resolution | Decorator-order overwrite or ad hoc dedupe | `_merge_transition_slot()` | Existing identity includes target/guard/ref/timing/mode and rejects equal-priority nonduplicates. [VERIFIED: `src/fast_fsm/core.py:2075-2116`] |
| Async classification | New decorator-only classifier | Existing builder `_detect_async_requirements()` / `_preflight_async_requirements()` | These already traverse plural handler guards and handler asyncness. [VERIFIED: `src/fast_fsm/core.py:6257-6296,6517-6566`] |
| Warning capture | Custom global warning registry | Python `warnings` module + pytest | The standard context manager restores filters and records category/location. [CITED: https://docs.python.org/3/library/warnings.html] |
| Persistence versioning | Snapshot v2 or schema-version negotiation | Additive `final_states` + true-only `internal`; snapshot v1 unchanged | Locked compatibility is directional, not symmetric. |
| Native verification | New compile/package harness | Existing `task build-check`, source-origin probe, and Phase 29 restoration pattern | Existing machinery already enforces selective compilation and prevents lingering shadows. [VERIFIED: `Taskfile.yml:120-145,185-203`] |

**Key insight:** Phase 30 is an adapter-normalization problem. The semantic engine already owns the hard invariants; the plan should minimize new policy and maximize evidence that every adapter reaches that engine exactly once.

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | External topology dictionaries may omit `final_states` and `internal`; no repository database or migration store is part of this library phase. [VERIFIED: `src/fast_fsm/core.py:1362-1709`; project is a library at `.planning/PROJECT.md:1-6`] | Code compatibility only: default omitted fields to non-final/external. No data migration. |
| Live service config | None — the phase has no server, dashboard, hosted workflow, or service-side configuration. [VERIFIED: project layout `.github/copilot-instructions.md:15-29`] | None. |
| OS-registered state | None — no launchd/systemd/task registration is used by construction or persistence. [VERIFIED: repository task/build entry points at `Taskfile.yml:20-33,180-203`] | None. |
| Secrets/env vars | Existing build selectors `FAST_FSM_BUILD_MODE` and compatibility alias `FAST_FSM_PURE_PYTHON` are unchanged. [VERIFIED: `setup.py:23-29`] | Preserve names and semantics; no secret or environment migration. |
| Build artifacts | In-place mypyc builds create native core shadows that can change import origin. [VERIFIED: `Taskfile.yml:185-203`; `tools/release_evidence.py:1709-1750`] | Start pure, assert origin, compile/test, recoverably relocate only verified core extensions on every exit, and reassert pure origin. No broad deletion. |

## Common Pitfalls

### Pitfall 1: Double Guard Evaluation

**What goes wrong:** A declarative guard copied into a generated request becomes both `entry.condition` and `handler.condition`, so `can_trigger`/`trigger` may call it twice, alter stateful guards twice, or observe two rejection/cancellation points.

**Why it happens:** The current manually mirrored pattern registers an unguarded topology row while the decorator owns the declarative guard. [VERIFIED: `tests/test_builder.py:2389-2403`; `src/fast_fsm/core.py:2940-2958`]

**How to avoid:** Generated request condition stays `None`; async classification and guard execution continue to use immutable handler metadata.

**Warning signs:** Guard call counters equal two for one query/attempt, expected rejection is classified at the transition-guard rather than declarative-guard seam, or a stateful condition changes twice.

### Pitfall 2: Shallow “Immutable” Metadata

**What goes wrong:** A caller mutates the original `from_state` list after decoration and silently changes future builder topology.

**Why it happens:** Frozen dataclasses prevent field assignment but do not freeze a list stored in a field. Current types verbatim allow `Optional[Union[str, List[str]]]`. [VERIFIED: `src/fast_fsm/core.py:865-875`]

**How to avoid:** Copy list inputs to tuples before storing; test that later source-list mutation cannot affect discovered rows or a failed/retried builder.

**Warning signs:** Repeated builds derive different requests without any builder mutation, or metadata hashes/identities depend on caller list state.

### Pitfall 3: Mode-Blind Handler Matching

**What goes wrong:** An `internal=True` declaration can bind a manually registered external self-transition with the same source/trigger/target/priority.

**Why it happens:** Current matching filters source, target, and priority but has no mode parameter. [VERIFIED: `src/fast_fsm/core.py:5651-5701`]

**How to avoid:** Add internal to handler records, declaration identity, and exact machine-owned resolver calls; direct compatibility calls use an unfiltered mode only when unambiguous.

**Warning signs:** External lifecycle runs with an internal-declared handler, or two declarations differing only by mode are collapsed during discovery rather than rejected by canonical candidate rules.

### Pitfall 4: Deprecation Warning Multiplication

**What goes wrong:** Calling `quick_fsm()` emits its own warning and the nested `quick_build()` warning; the nested warning points inside the package.

**Why it happens:** The current helpers delegate public-to-public. [VERIFIED: `src/fast_fsm/core.py:6956-7012`]

**How to avoid:** Split non-warning workers and emit directly at each public boundary with `stacklevel=2`.

**Warning signs:** Captured warning length is two, `warning.filename` resolves to `core.py`, or warnings differ depending on filter registry history.

### Pitfall 5: Mypyc Narrows Before Exact Validation

**What goes wrong:** Annotating an untrusted runtime scalar as `bool` or a typed container before checking it can produce pure/native differences or allow conversion before the intended error.

**Why it happens:** `core.py` is a mypyc native compilation unit; native classes have declared layouts and differ from interpreted classes. [CITED: https://mypyc.readthedocs.io/en/stable/native_classes.html] Existing request carriers deliberately keep raw `priority`, `after`, `within`, and `internal` as `Any`. [VERIFIED: `src/fast_fsm/core.py:823-836`]

**How to avoid:** Accept implementation-level `object`/`Any`, perform `type(value) is ...`, then assign normalized typed values. Update exact AST field-set tests and run the same semantic oracle pure/native.

**Warning signs:** Pure tests reject `1` but native tests accept it, mypyc reports incompatible primitive conversion, or a compiled function raises before indexed context is attached.

### Pitfall 6: Claiming Symmetric Dictionary Compatibility

**What goes wrong:** Documentation says a v0.5 dictionary is safe in a pre-v0.5 reader even though that reader can ignore `final_states` or `internal` and reconstruct different behavior.

**Why it happens:** Additive JSON shape is syntactically readable but not semantically enforceable by the old reader.

**How to avoid:** State only old→new and new→new guarantees; say old readers may silently lose new semantics.

**Warning signs:** Tests only show `json.loads` succeeds, or docs use “fully backward compatible” without direction.

### Pitfall 7: Clone Tests Stop at Topology Equality

**What goes wrong:** Final/mode rows compare equal while callback registries or transition containers remain aliased, live current state/history are copied, or async type is lost.

**Why it happens:** `to_dict()` cannot express callback/container identity and snapshot is intentionally state-only.

**How to avoid:** Assert same State/subclass objects, distinct entry/group/table/list containers, same callable collaborators, reset-to-initial, history disabled, and concrete async type. [VERIFIED: established clone implementation at `src/fast_fsm/core.py:3659-3711`]

## Code Examples

Verified patterns and prescribed Phase 30 usage:

### Builder-First Programmatic Construction

The public objects and method names below already exist in runtime and stubs. [VERIFIED: `src/fast_fsm/core.py:6158-6661`; `src/fast_fsm/core.pyi:405-437`]

```python
from fast_fsm import FSMBuilder, State

idle = State("idle")
done = State("done", final=True)
machine = (
    FSMBuilder(idle, name="Job")
    .add_state(done)
    .add_transition("finish", "idle", "done")
    .build()
)
```

The exact persisted final-state container remains `"final_states"`, and `final=True` is exact immutable State metadata. [VERIFIED: `src/fast_fsm/core.py:905-928`; `src/fast_fsm/core.py:1701-1708`]

### Declarative Topology Without Mirroring

This is the Phase 30 target authoring pattern; keyword-only `internal=False`/`True` is locked by D-05, and an internal transition requires identical canonical source and target. [VERIFIED: canonical rule at `src/fast_fsm/core.py:1905-1936`]

```python
from fast_fsm import DeclarativeState, FSMBuilder, State, transition

class Hover(DeclarativeState):
    @transition("refresh", to_state="hover", internal=True)
    def refresh(self, *args, **kwargs):
        return True

hover = Hover("hover")
machine = FSMBuilder(hover).build()
```

The builder must generate the topology row; user code must not add a duplicate `.add_transition(...)` call.

### True-Only Dictionary Output

The exact stable top-level keys remain `"name", "initial", "states", "final_states", "transitions"`; the new row scalar is `"internal"` and is emitted only with JSON Boolean `true`. [VERIFIED: `src/fast_fsm/core.py:1680-1709`; locked D-13]

```json
{
  "name": "Hover",
  "initial": "hover",
  "states": ["hover"],
  "final_states": [],
  "transitions": [
    {"trigger": "refresh", "from": "hover", "to": "hover", "priority": 0, "internal": true}
  ]
}
```

### Snapshot v1 Remains State-Only

The complete snapshot value is verbatim `{"state": <current_state_name>, "version": 1}`. [VERIFIED: `src/fast_fsm/core.py:3578-3593`]

```python
snapshot = machine.snapshot()
assert snapshot == {"state": "hover", "version": 1}
```

## Threat Model and Security Domain

### Threat Matrix

| Threat | STRIDE | Risk | Standard mitigation / validation |
|--------|--------|------|----------------------------------|
| Truthy or subclassed `internal` changes lifecycle semantics | Tampering | High | Exact built-in bool checks before candidate publication; pure/native negative matrix. [VERIFIED: canonical exact check at `src/fast_fsm/core.py:1905-1907`] |
| Mutable decorator source list changes topology after declaration | Tampering | High | Defensive tuple copy into frozen/slotted metadata; mutation regression test. |
| Malformed later row publishes valid prefix | Tampering | High | Parse complete input and use one prepare-all/publish-once request tuple. [VERIFIED: `src/fast_fsm/core.py:2029-2073`] |
| Executable guard/callback representation leaks through serialization/error text | Information disclosure | Medium | Serialize only opaque condition references; fixed bounded warning/errors; never format caller objects or callable internals. [VERIFIED: `src/fast_fsm/core.py:1394-1411`; locked D-11/D-14] |
| Deprecated wrapper emits warnings from internal frames or with payloads | Information disclosure / Repudiation | Medium | Fixed constants, direct boundary warning, exact filename/line/category/count tests. [CITED: https://docs.python.org/3/library/warnings.html] |
| Old reader silently drops final/internal meaning | Tampering / Repudiation | Medium | Directional compatibility statement; no symmetric safety claim. |
| Clone shares mutable topology/callback containers | Tampering | Medium | Reconstruct entries through canonical transaction and copy every registry container; identity/isolation tests. [VERIFIED: `src/fast_fsm/core.py:3659-3711`] |
| Construction policy leaks into dispatch and lowers throughput | Denial of service | High | Structural absence checks for warnings/request/import helpers in trigger/select/lifecycle regions; compiled singleton benchmark. [VERIFIED: current structural guard `tests/test_graph_invariants.py:1028` and policy `.github/copilot-instructions.md:40-59`] |
| Generated native shadow changes which implementation tests import | Spoofing | High | Fail-closed exact source-origin inventory, asserted native suffix, recoverable exact-path relocation, final pure assertion. [VERIFIED: `tools/release_evidence.py:1709-1750`; `.planning/phases/29-expected-domain-rejection/29-04-PLAN.md:168-205`] |

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No authentication boundary exists in this library phase. |
| V3 Session Management | No | Snapshot is local state serialization, not a user session. |
| V4 Access Control | No | No authorization decision or protected resource is added. |
| V5 Input Validation | Yes | Exact serialized container/scalar validation, bounded context, opaque condition references, and atomic publication. |
| V6 Cryptography | No | No secrets, signing, encryption, or random token generation is in scope. |

Security enforcement is active because `.planning/config.json` does not set `security_enforcement` to false. [VERIFIED: `.planning/config.json:1-31`]

## State of the Art

| Old Approach | Current/Phase 30 Approach | When Changed | Impact |
|--------------|---------------------------|--------------|--------|
| Each adapter may register rows incrementally | Immutable request tuple, prepare all, publish once | Phase 26 | Phase 30 should adapt inputs, not replicate invariants. [VERIFIED: `.planning/phases/26-canonical-construction-evidence-contract/26-VERIFICATION.md:29-43`] |
| Finality inferred or omitted by adapters | Immutable `State.final`, explicit `final_states`, no outgoing final source | Phase 27 | Builder/declarative/dictionary paths must preserve exact State identity/finality. [VERIFIED: `.planning/phases/27-explicit-final-states/27-VERIFICATION.md:31-42`] |
| Same-state transitions always externally re-enter | Per-entry exact `internal` mode | Phase 28 | Persistence and decorator metadata must now carry selected-entry mode. [VERIFIED: `.planning/phases/28-same-state-transition-modes/28-VERIFICATION.md:27-31,58-62`] |
| Expected domain rejection could be flattened by adapter/guard changes | Selector-only terminal `TransitionRejected` contract | Phase 29 | Generated declarative topology must keep the guard on the declarative seam and preserve rejection classification. [VERIFIED: `.planning/phases/29-expected-domain-rejection/29-VERIFICATION.md:28-37`] |
| Multiple “equal” construction recipes in guidance | Builder primary; direct advanced; `from_dict` persistence; helpers deprecated | Phase 30 target | One ordinary authoring story with a compatibility cycle. |

**Deprecated/outdated after Phase 30:**

- `simple_fsm`, `quick_fsm`, `StateMachine.quick_build`, and `StateMachine.from_states` become retained deprecated compatibility surfaces, not recommended authoring recipes. They remain exported and typed through v0.5.x. [VERIFIED: locked D-09/D-10; current exports `src/fast_fsm/__init__.py:108-111`]
- Manual duplication of decorated transitions in `FSMBuilder` examples becomes outdated; the builder imports applicable topology-complete declarations itself.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `8.4.1` local, with pytest-asyncio and Hypothesis available [VERIFIED: `pyproject.toml:11-20`; local version probe] |
| Config file | `pyproject.toml` (`testpaths = ["tests"]`, `addopts = ["-x", "-q", "--tb=short", "--strict-markers"]`) [VERIFIED: `pyproject.toml:54-70`] |
| Quick run command | `uv run pytest tests/test_builder.py tests/test_advanced_functionality.py tests/test_final_states.py tests/test_transition_modes.py tests/test_graph_invariants.py -x -q -k "declarative or deprecat or from_dict or clone or snapshot or internal or final or construction"` |
| Full suite command | `uv run pytest tests/ -x -q` [VERIFIED: `Taskfile.yml:26-33`] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BUILD-01 | Builder-first examples/API hierarchy; direct and from_dict positioning | docs + executable examples | `uv run pytest tests/test_readme_examples.py -x -q && task docs-check && task docs-test` | ✅ extend existing |
| BUILD-02 | Decorated states create canonical topology without manual mirroring; guard/handler exactly once; async auto-detection | unit/integration | `uv run pytest tests/test_builder.py -x -q -k "declarative"` | ✅ extend existing |
| BUILD-03 | Four symbols warn once at caller and keep behavior/type/atomicity | unit | `uv run pytest tests/test_builder.py tests/test_final_states.py -x -q -k "deprecat or quick or from_states or simple_fsm"` | ✅ extend existing |
| BUILD-06 | All adapters reject identical invalid final/mode rows atomically and preserve graph version | property/invariant | `uv run pytest tests/test_graph_invariants.py tests/test_builder.py tests/test_final_states.py tests/test_transition_modes.py -x -q -k "construction or final or internal or mode"` | ✅ extend existing |
| BUILD-07 | True-only internal round-trip; legacy defaults; clone final/mode/subclass/container parity | integration | `uv run pytest tests/test_advanced_functionality.py tests/test_final_states.py tests/test_transition_modes.py -x -q -k "from_dict or roundtrip or clone or internal or final"` | ✅ extend existing |
| BUILD-08 | Exact snapshot-v1 schema; restore termination/mode derives from receiving topology | unit/integration | `uv run pytest tests/test_graph_invariants.py tests/test_final_states.py -x -q -k "snapshot or restore"` | ✅ extend existing |
| BUILD-01..08 | Runtime/stub carrier layout, no bypass/hot-path work, pure/native semantic parity | structural/native | `uv run pytest tests/test_mypyc_guard.py tests/test_graph_invariants.py -x -q -k "construction or declarative or persistence or adapter or hot_path"` plus the established fresh-native closure | ✅ extend existing |

### Required Test Matrix

1. **Decorator contract:** default/explicit true/false mode, rejection of `0`, `1`, strings, and truthy objects; priority/timing retained; caller source-list mutation cannot alter metadata; runtime/stub signatures match; metadata/handler frozen slot field sets include mode.
2. **Declarative builder:** initial and later state import; source constraint omitted/single/list applicable to the exact owner; incomplete direct-only declaration remains compatible but creates no invented edge; unknown target fails before publication; final source and invalid internal target fail through canonical errors; explicit/declarative equal-priority conflicts and exact duplicates follow canonical rules; failed build remains repairable; successful build is cached.
3. **Exactly once:** counters for sync/async decorator guard, handler, direct entry guard, state permission, and lifecycle; expected rejection remains at the declarative guard seam; internal handlers run once while state lifecycle stays skipped.
4. **Warning contract:** one record per invocation under `simplefilter("always")`; exact `DeprecationWarning`; exact fixed message; filename/line is the test call site; no payload repr; returned machine preserves prior behavior and subclass/classmethod result type; warnings do not appear on nondeprecated surfaces.
5. **Dictionary contract:** external omission, explicit false, true-only output, legacy no-fields defaults, final+internal combination, priority groups, timing/ref preservation, exact container/scalar negatives, unknown/final/internal mismatch indexed errors, JSON round-trip, sync/async inherited constructor parity, no partial candidate/version escape.
6. **Clone/snapshot:** State/CallbackState/DeclarativeState subclass identity, final marker, internal entry identity value but distinct entry/group/table containers, independent callback registries, same callable collaborators, async type, reset initial state, no live history/current copy; snapshot exact two-key schema and receiver-owned termination/topology.
7. **Structural/native:** adapter regions contain one canonical apply and no normalize/commit bypass; declaration import absent from selectors/lifecycle; warning code absent from dispatch; exact record fields in AST/stubs; same oracle from asserted pure and fresh native origins; singleton benchmark remains above policy floor.

### Sampling Rate

- **Per task commit:** the requirement-specific targeted command above plus blocking `task typecheck-mypy` for any `core.py`/stub change.
- **Per wave merge:** targeted five-file construction/persistence suite, `task typecheck-mypy`, visible `task typecheck-ty`, and non-mutating Ruff checks.
- **Phase gate:** strict docs/doctest, slots policy, pure semantic oracle, fresh compiled semantic oracle with fail-safe shadow restoration, singleton performance gate, final exact pure-source assertion, then full sequential suite.

### Wave 0 Gaps

- [ ] Add a central Phase 30 parity helper/oracle (either a dedicated `tests/test_construction_parity.py` or a clearly isolated section in `tests/test_builder.py`) that can be invoked unchanged in pure and native modes.
- [ ] Extend `tests/test_mypyc_guard.py` exact field sets for `_DeclarativeHandlerMetadata` and `_DeclarativeHandler`; the current expected verbatim fields omit `"internal"`. [VERIFIED: `tests/test_mypyc_guard.py:500-563`]
- [ ] Add warning attribution tests; no current production warning exists on the four surfaces. [VERIFIED: `src/fast_fsm/core.py:1198-1359,6953-7012`]
- [ ] Add exact dictionary container/scalar and true-only mode tests; existing output expectations for external rows must remain unchanged. [VERIFIED: `tests/test_graph_invariants.py:678-692`]
- No framework/config/fixture installation gap exists; current pytest, async, property, docs, and native harnesses are sufficient. [VERIFIED: `pyproject.toml:11-36,54-70`; `Taskfile.yml:26-60,120-145,185-255`]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `uv` | All Python/test/build commands | ✓ | `0.12.12` | None; repository requires uv. |
| Python | Runtime/test matrix | ✓ | `3.12.10` locally; project floor `>=3.10` | Hosted supported-Python CI for other versions. [VERIFIED: `pyproject.toml:6`] |
| `task` | Quality/docs/native workflows | ✓ | `3.53.1` | Invoke the underlying documented uv commands if necessary. |
| mypy/mypyc | Blocking compiled compatibility | ✓ | `1.17.1` | None for phase completion. |
| pytest | Semantic tests | ✓ | `8.4.1` | None. |
| Sphinx | Focused public docs | ✓ | `9.1.0` | None. |

The initial sandboxed `uv run` probes could not access the user cache; the same read-only probes succeeded under the already-approved uv execution boundary. This is an execution-environment permission issue, not a missing dependency. [VERIFIED: local probes this session]

**Missing dependencies with no fallback:** none.

**Missing dependencies with fallback:** none.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| — | None. All factual claims are grounded in locked context, opened repository source/artifacts, local tool probes, or official Python/mypyc documentation. | — | — |

## Open Questions

1. **How should one class-level declaration apply to multiple source-state instances?**
   - What we know: runtime matching reads the handlers on the canonical source object and checks whether its own name matches `from_state`. [VERIFIED: `src/fast_fsm/core.py:5651-5670`]
   - What's unclear: current tests include a declaration on one `DeclarativeState("idle")` whose `from_state` names other generic states, but that row is manually mirrored and its handler cannot resolve from those generic states. [VERIFIED: `tests/test_builder.py:1129-1155`]
   - Recommendation: preserve state ownership. Import one request from each staged declarative object only when the metadata applies to that object's name; to cover a plural source constraint with handler execution, stage declarative instances for each source. Do not add a machine-wide handler table or a bound-handler field to every hot-path entry in this phase.

2. **What should a destination-less declaration do in builder topology?**
   - What we know: `to_state` is optional and direct `handle_event*()` compatibility is locked. [VERIFIED: `src/fast_fsm/core.py:5591-5612`; locked D-08]
   - What's unclear: a destination-less event handler cannot define an FSM edge.
   - Recommendation: retain it for direct compatibility and skip topology derivation. Document that builder-imported declarations must be topology-complete; do not invent a self-transition because external versus internal self semantics are explicit.

3. **Should explicit `internal: false` be accepted in dictionaries?**
   - What we know: D-13 permits absence or explicit false as external, and agent discretion allows the exact input choice provided both read as external.
   - Recommendation: accept exact false. It is natural JSON, enables hand-authored configs, and costs no output compatibility because false remains omitted.

## Sources

### Primary (HIGH confidence)

- `.planning/phases/30-builder-first-construction-persistence-parity/30-CONTEXT.md` — D-01 through D-20, phase boundary, discretion, and deferrals.
- `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md` — BUILD-01/02/03/06/07/08 and Phase 30 success criteria.
- `src/fast_fsm/core.py`, `core.pyi`, and `__init__.py` — live runtime, typing, exports, builder, persistence, clone, and snapshot behavior.
- `tests/test_builder.py`, `test_graph_invariants.py`, `test_final_states.py`, `test_transition_modes.py`, `test_advanced_functionality.py`, and `test_mypyc_guard.py` — active behavioral and structural patterns.
- Phase 26–29 CONTEXT/VERIFICATION/SUMMARY artifacts — settled canonical construction, final, internal, rejection, and evidence contracts.
- `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, `.specify/memory/spr-core-api.md`, `Taskfile.yml`, `pyproject.toml`, and `setup.py` — repository constraints and quality/build boundaries.

### Secondary (MEDIUM confidence)

- [Python warnings documentation](https://docs.python.org/3/library/warnings.html) — `stacklevel`, default deprecation filtering, and warning test capture.
- [mypyc native classes documentation](https://mypyc.readthedocs.io/en/stable/native_classes.html) — declared native layouts and interpreted-subclass boundary.

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — verified from project configuration and live version probes.
- Architecture: HIGH — traced through current source and verified Phase 26–29 contracts.
- Persistence/clone/snapshot: HIGH — source and active tests expose exact current gaps and retained invariants.
- Deprecation mechanics: HIGH for project decisions, MEDIUM for external warning mechanics because official docs were fetched through web fallback rather than Context7.
- Pitfalls/threats: HIGH — each maps to a concrete current seam or locked compatibility/security requirement.

**Research date:** 2026-09-17
**Valid until:** 2026-10-17 (stable milestone-local code contract; refresh if Phase 30 source changes before planning)
