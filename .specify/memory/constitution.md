<!--
Sync Impact Report
==================
Version change: 1.2.0 → 1.3.0
Bump type: MINOR — added mypyc selective compilation as an
architectural decision with compilation boundary rules.

Added sections:
  - Architecture & Anti-Patterns > Selective mypyc Compilation
    (which modules compile, inheritance constraint, build commands)

Modified sections:
  - Architecture & Anti-Patterns (new anti-pattern row:
    "Compiling condition base classes")

Removed sections: none

Templates requiring updates:
  - .specify/templates/plan-template.md ✅ no changes needed (generic)
  - .specify/templates/spec-template.md ✅ no changes needed (generic)
  - .specify/templates/tasks-template.md ✅ no changes needed (generic)
  - .github/copilot-instructions.md ✅ updated (mypyc gotcha added)
Follow-up TODOs: none
-->

# Fast FSM Constitution

## Mission

Fast FSM is a high-performance, memory-efficient finite state machine
library for Python. It exists to deliver 5–20× faster transitions and
~1000× lower memory usage than popular alternatives while maintaining
a clean, intuitive API — enabling use in latency-sensitive control
loops, IoT devices, game engines, and large-scale simulations where
general-purpose FSM libraries are too slow or too heavy.

## Core Principles

### I. Performance Is Non-Negotiable

Every public API path MUST maintain O(1) time complexity for core
operations (`trigger()`, `can_trigger()`, `add_state()`,
`add_transition()`). All classes that participate in the hot path
MUST use `__slots__` to eliminate `__dict__` overhead. New features
MUST NOT degrade existing throughput below ~250,000 transitions/sec
on commodity hardware. Performance claims MUST be verifiable via the
benchmark suite (`benchmarks/`).

**Rationale:** Fast FSM exists specifically to outperform alternatives
by 5–20×. Losing that advantage removes the library's reason to exist.

### II. Memory Efficiency Through Slots

Every class in `src/fast_fsm/` MUST use `__slots__` unless there is a
documented, justified exception. Dynamic attribute assignment on core
objects is prohibited. When callback storage is needed on a state,
use `CallbackState` (which has dedicated slots) rather than adding
`__dict__` to `State`.

**Rationale:** Slots optimization delivers ~1000× better memory
efficiency than dict-based class hierarchies, enabling use on
memory-constrained targets (IoT, embedded, large-scale simulations).

### III. Backward Compatibility

Public API changes MUST NOT break existing callers without a
deprecation cycle: deprecated in minor release, removed no earlier
than the next major release. All condition and callback signatures
MUST accept `*args, **kwargs` to preserve forward-compatible call
conventions. New convenience methods (factory functions, builders)
are additive — they MUST NOT alter existing constructor behavior.

**Rationale:** Users integrate FSMs into production control loops. A
breaking change can cascade into runtime failures that are expensive
to diagnose.

### IV. Test-Driven Quality

Every new feature or bug fix MUST include tests that exercise the
change. Tests MUST pass before code is merged to `main`. The full
suite (`uv run pytest tests/ -x -q`) is the merge gate — it MUST
remain green. Statistical or timing-sensitive tests MUST use
tolerances wide enough to avoid flakiness. Property-based testing
via Hypothesis is encouraged for combinatorial state-space coverage.

**Rationale:** A library consumed as a dependency has a higher
correctness bar than an application. Silent regressions in FSM
dispatch logic can cause subtle, hard-to-debug failures downstream.

### V. Simplicity & Minimal Abstraction

Prefer fewer abstraction layers over flexible extensibility. The
core module (`core.py`) SHOULD remain a single file unless it exceeds
~2,500 lines. Helpers (validation, conditions) live in their own
modules but MUST NOT introduce circular imports. Every public symbol
MUST be listed in `__init__.py.__all__` and have a docstring. Avoid
frameworks and metaprogramming in the hot path.

**Rationale:** Simplicity enables auditability, reduces onboarding
time, and keeps the call stack shallow — which directly supports
Principle I (performance).

**When principles conflict, the priority order is:**
**Performance > Memory Efficiency > Backward Compatibility > Simplicity.**
A change that improves simplicity but degrades performance is rejected.
A change that breaks backward compatibility for a performance gain
requires a deprecation cycle (Principle III still applies).

## Architecture & Anti-Patterns

The following anti-patterns are specific failure modes that recur in
FSM library development. Contributors MUST understand them.

| Anti-Pattern | Why It's Harmful | Fast FSM Risk |
|---|---|---|
| **Adding `__dict__` to hot-path classes** | Eliminates the ~1000× memory advantage that justifies this library's existence. A single class without `__slots__` on the dispatch path invalidates every benchmark claim. | Core classes (`State`, `StateMachine`, `TransitionResult`, `Condition`) are the most common edit targets — vigilance is required. |
| **Python-level iteration where dict lookup suffices** | Replacing O(1) dictionary lookup with a linear scan over states or transitions degrades the core performance guarantee. | Transition dispatch MUST remain a single dict lookup, not a loop over candidates. |
| **Breaking `*args, **kwargs` signatures** | Removing variadic arguments from conditions or callbacks silently breaks every downstream caller that passes extra context. The failure is a `TypeError` at runtime, not a lint error. | All public callback/condition signatures are contractual interfaces. |
| **Logic-mocking in tests** | Mocking the computation under test (e.g., patching `trigger()` internals then asserting the mock value) produces a test that cannot fail regardless of implementation bugs. It tests Python's mock library, not the FSM. | FSM dispatch, condition evaluation, and state callbacks are the critical paths. Mock the *environment* (clock, RNG), never the *logic*. |
| **Circular imports between modules** | `core.py` ↔ `validation.py` or `core.py` ↔ `conditions.py` cycles break `import fast_fsm` for all users. | Keep the import DAG strict: `conditions` → `core` → `validation`. Validation imports core, never the reverse. |
| **Validation overhead on the hot path** | Validation is a design-time tool. Adding runtime checks inside `trigger()` or `can_trigger()` degrades throughput for all users, not just those who opt in to validation. | Validation MUST remain in `validation.py` and MUST NOT be called from core dispatch. |
| **Compiling condition base classes** | mypyc-compiled classes cannot be subclassed from interpreted Python. Compiling `conditions.py` would break every user who writes a custom `Condition` subclass. | `conditions.py` and `condition_templates.py` MUST remain uncompiled. Only `core.py` is compiled. |

### Selective mypyc Compilation

Fast FSM uses [mypyc](https://mypyc.readthedocs.io/) to compile
performance-critical Python modules to C extensions. Compilation is
**selective** — only modules on the hot path are compiled; modules
that users subclass are deliberately left as interpreted Python.

**Compilation boundary:**

| Module | Compiled? | Rationale |
|--------|-----------|----------|
| `core.py` | **Yes** | Contains `StateMachine`, `State`, `trigger()` — the entire hot path. Compilation yields measurable throughput gains. |
| `conditions.py` | **No** | Defines `Condition`, `FuncCondition`, `AsyncCondition` — base classes that users subclass. mypyc-compiled classes cannot be subclassed from interpreted code. |
| `condition_templates.py` | **No** | Inherits from `Condition` (uncompiled). Compiling would require compiling the entire condition hierarchy. |
| `validation.py` | **No** | Design-time only; not on the hot path. No performance benefit. |

**Rules:**
- `core.py` is the ONLY module that gets compiled.
- `conditions.py` MUST stay uncompiled so users can subclass
  `Condition`, `FuncCondition`, and `AsyncCondition`.
- Tests MUST use composition (create instances, call methods), not
  inheritance of `State` or `StateMachine`, to remain compatible
  with the compiled build.
- The compilation is configured in `setup.py` via `mypycify()`
  and triggered by `uv run python setup.py build_ext --inplace`.
- The library MUST work correctly both with and without compilation.
  Compilation is an optimization, not a requirement.

## Performance Standards

These quantitative thresholds are the minimum acceptable baselines.
Regressions below these values block merges.

| Metric | Threshold | How to verify |
|--------|-----------|---------------|
| `trigger()` throughput | ≥ 200,000 ops/sec | `uv run python benchmarks/benchmark_fast_fsm.py` |
| `can_trigger()` throughput | ≥ 400,000 ops/sec | same benchmark suite |
| Base FSM memory | ≤ 0.5 KB | `tracemalloc` in benchmark |
| Per-state overhead | ≤ 64 bytes | measured via slots |
| Per-transition overhead | ≤ 128 bytes | measured via slots |
| Core operation complexity | O(1) | code review / design check |

Performance benchmarks MUST be run on the developer's machine before
claiming improvements. Results MUST NOT be committed as "official"
without noting hardware/OS context.

## Quality Gates

### Linting & Formatting (two-phase)

Phase 1 — auto-fix (never fails a build):
```
uv run ruff format <files>
uv run ruff check --fix <files>
```

Phase 2 — validate (blocks merge on failure):
```
uv run ruff check <files>
uv run ty check <files>
```

Configuration lives in `pyproject.toml`. Target: Python ≥ 3.12,
line length 88.

### Testing

- **Full command:** `uv run pytest tests/ -x -q`
- **Baseline:** 62 passed, 0 failures
- **Incremental testing:** run only the affected test file during
  development; full suite once before push.

| Source file changed | Primary test file |
|---------------------|-------------------|
| `core.py` | `test_basic_functionality.py`, `test_advanced_functionality.py` |
| `validation.py` | `test_basic_functionality.py` (validation tests) |
| `conditions.py` | `test_safety_kwargs.py` |
| `condition_templates.py` | `test_safety_kwargs.py` |
| README / examples | `test_readme_examples.py` |
| Performance-sensitive | `test_performance_benchmarks.py` |

**Anti-mocking discipline:**
- Tests that mock the logic under test and assert the mock's return
  value are *worse than no test* — they provide false confidence.
  See the **Logic-Mocking in Tests** anti-pattern in
  § Architecture & Anti-Patterns.
- Mock the *environment* (clock, RNG, I/O) to make tests
  deterministic. NEVER mock the *computation* being verified
  (transition dispatch, condition evaluation, state callbacks).

**Bug-fix regression tests:**
- When a bug is fixed, a test that reproduces the specific failure
  mode MUST be committed alongside the fix. This test MUST fail
  before the fix and pass after. The purpose is to prevent silent
  reintroduction of the same defect.

### Documentation

#### README and High-Level Docs
- `README.md` MUST stay current with API surface, installation
  instructions, and benchmark claims. It is the authoritative
  first-stop reference for new users.
- Public API changes (new classes, functions, builder kwargs) MUST
  be reflected in `README.md` before the branch is merged.

Public API additions MUST update:
1. Docstring on the symbol itself
2. `__init__.py.__all__` export list
3. `README.md` if the feature is user-facing
4. Relevant doc in `docs/` if it changes a documented pattern

#### Docstrings
- All public functions, classes, and methods MUST have docstrings.
- Use **Google-style** docstrings throughout. Do NOT use
  reStructuredText (reST/PEP 287) inline docstring syntax — it is
  harder to read during development and offers no advantage here.
  Google-style is rendered correctly by Sphinx via
  `sphinx.ext.napoleon` (ships with Sphinx; no extra install).
- **Types MUST NOT be duplicated in docstrings.** Use Python type
  annotations as the single source of truth. Configure
  `sphinx-autodoc-typehints` to inject types from annotations into
  rendered docs automatically.
- Every docstring MUST contain:
  - A concise one-line summary (imperative mood, e.g.,
    "Trigger a state transition").
  - `Args:` block when the function accepts non-obvious parameters.
  - `Returns:` block when the return value is non-trivial.
  - `Raises:` block when the function explicitly raises exceptions.
- Internal helpers (underscore-prefixed) SHOULD have at minimum a
  one-line summary.
- A stale docstring that contradicts the implementation is a bug,
  identical in severity to a stale comment.

**Sphinx extension stack** (when docs are generated):

| Extension | Purpose |
|---|---|
| `sphinx.ext.autodoc` | Pull docstrings into rendered docs |
| `sphinx.ext.napoleon` | Parse Google-style docstrings |
| `sphinx.ext.viewcode` | Link rendered docs back to source |
| `sphinx-autodoc-typehints` | Inject types from annotations (avoids duplication) |
| `sphinx.ext.intersphinx` | Cross-link to Python stdlib docs |

#### Inline Comments
- Comments MUST explain *why*, not *what*. Comments that merely
  restate the code add noise and MUST be removed.
- Non-obvious algorithmic choices or performance trade-offs MUST be
  annotated with a justification or reference.

## Governance

This constitution is the authoritative source for project standards.
It supersedes ad-hoc conventions, chat history, and undocumented
practices.

- **Amendments** require updating this file, bumping the version,
  and recording the change in the Sync Impact Report comment block
  at the top of this document.
- **Versioning** follows semantic versioning:
  - MAJOR: principle removed/redefined or backward-incompatible
    governance change
  - MINOR: new principle or materially expanded section
  - PATCH: wording clarifications, typo fixes
- **Compliance** is verified at code review time. The
  `.github/copilot-instructions.md` file operationalizes this
  constitution for AI agents — it owns *how*; this file owns *why*.
- **Complexity justification:** any deviation from these principles
  MUST be documented in the PR description with rationale.

### Document Responsibilities

Two documents govern development. Each owns a distinct layer —
content MUST NOT be duplicated across both. When they conflict,
this constitution takes precedence for standards; Agent Instructions
take precedence for mechanics.

| Document | Owns | Answers |
|---|---|---|
| This constitution | Principles, architectural decisions, quality standards, the bar | *Why* and *what* |
| [Agent Instructions](../.github/copilot-instructions.md) | Operational workflows, CLI commands, tool quirks, session mechanics | *How* to comply |

**Rules:**
- Content describing *what standard must be met* belongs here.
- Content describing *how to execute that standard* (exact commands,
  file paths, tool flags, platform workarounds) belongs in Agent
  Instructions.
- Agent Instructions MUST reference the constitution section they
  operationalize.
- Operational details (e.g., test file mappings, known failures)
  live in Agent Instructions and are updated there without requiring
  a constitution version bump.

**Version**: 1.3.0 | **Ratified**: 2026-03-03 | **Last Amended**: 2026-03-03
