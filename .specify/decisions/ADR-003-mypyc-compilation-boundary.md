# ADR-003: mypyc compilation boundary — `core.py` only, `conditions.py` stays interpreted

**Status**: Accepted  
**Date**: 2026-03-06  
**Deciders**: project maintainer + AI pair

---

## Context

Fast FSM uses [mypyc](https://mypyc.readthedocs.io/) to compile Python
source to C extensions, yielding measurable throughput gains on the hot
path. The question is: **which modules to compile, and why not all of them?**

The complicating factor is the mypyc constraint that **compiled classes
cannot be subclassed from interpreted Python**. The library's public API
includes several abstract base classes that users are expected to subclass:
`Condition`, `FuncCondition`, `AsyncCondition`, `State`.

`State` addresses this via `@mypyc_attr(allow_interpreted_subclasses=True)`,
which allows interpreted subclasses at the cost of some performance. The
question is why the same approach was not applied to `conditions.py`.

---

## Decision

Only `core.py` is compiled. `conditions.py` and `condition_templates.py`
remain uncompiled interpreted Python.

The `@mypyc_attr(allow_interpreted_subclasses=True)` decorator is applied
to `State` and `DeclarativeState` in `core.py`, but is NOT applied to
classes in `conditions.py`.

**Compilation table:**

| Module | Compiled | Rationale |
|---|---|---|
| `core.py` | **Yes** | Contains the entire hot path: `StateMachine`, `State`, `trigger()` |
| `conditions.py` | **No** | User subclassing base; cascade problem (see below) |
| `condition_templates.py` | **No** | Inherits from `conditions.py`; cannot compile parent without compiling child |
| `validation.py` | **No** | Design-time only; no hot-path benefit |

---

## Considered Alternatives

### Option A: Compile `core.py` only ✅ Chosen

Described above.

**Pros:**
- `conditions.py` stays fully interpreted — users can subclass `Condition`,
  `FuncCondition`, `AsyncCondition` from pure Python without any mypyc
  interaction.
- `condition_templates.py` inherits from uncompiled classes — no cascade
  problem.
- `core.py` contains the actual hot path; conditions are evaluated once
  per transition, but the dispatch machinery runs on every call.
- Clean boundary: the compiled/uncompiled split maps directly to the
  import DAG split (`conditions → core`).

**Cons / tradeoffs:**
- Condition evaluation itself is not accelerated. For FSMs with very
  expensive guard conditions, this is not the bottleneck anyway.
- `allow_interpreted_subclasses=True` on `State` means the compiled
  `State` classes pay a small interop penalty for interpreted subclasses.

---

### Option B: Compile everything with `allow_interpreted_subclasses=True` on all bases ❌ Rejected

Apply `@mypyc_attr(allow_interpreted_subclasses=True)` to `Condition`,
`FuncCondition`, `AsyncCondition` and compile `conditions.py` alongside
`core.py`.

**Why rejected:**
The cascade problem. `condition_templates.py` contains factory functions
that return `FuncCondition` subclasses. If `FuncCondition` is compiled
with `allow_interpreted_subclasses=True`, the subclasses in
`condition_templates.py` must also be compiled (you cannot have a compiled
parent optimized for interpreted subclasses and then compile a child —
mypyc does not support this mixed mode). Compiling `condition_templates.py`
means users who create custom condition templates by inheriting from it
now face the same subclassing constraint. The cascade has no natural
stopping point.

Additionally, `allow_interpreted_subclasses=True` disables several mypyc
optimizations on the annotated class. Applying it to `Condition` would
degrade performance for every `FuncCondition` call even in compiled mode.

---

### Option C: Compile `core.py` and `conditions.py`, leave `condition_templates.py` uncompiled ❌ Rejected

Compile only `conditions.py` alongside `core.py`, accepting that
`condition_templates.py` must remain interpreted.

**Why rejected:**
Same cascade problem in reverse. `condition_templates.py` subclasses
`FuncCondition`. If `FuncCondition` is compiled without
`allow_interpreted_subclasses=True`, the interpreted subclasses in
`condition_templates.py` crash at import time. If compiled WITH it,
we lose optimizations and still can't prevent users from hitting the
constraint when they write custom templates that inherit from
`condition_templates.py` helpers.

The fundamental issue is that `conditions.py` defines the root of a
subclassing hierarchy that users extend. Compiling a subclassed root
without compiling the entire tree is fragile.

---

### Option D: Compile nothing; ship pure Python only ❌ Rejected

Remove mypyc entirely and rely on Python-level optimization only.

**Why rejected:**
mypyc compilation of `core.py` yields a measurable throughput gain on
the hot path (the `trigger()` dispatch loop). The library's performance
claim (5-20x faster than alternatives) partly depends on this. Removing
compilation would require revalidating all benchmark comparisons.

The compilation is also optional by design (`FAST_FSM_PURE_PYTHON=1`
skips it; the library falls back gracefully if mypyc or a C compiler
is unavailable). Pure Python mode is preserved; mypyc is an acceleration
layer, not a requirement.

---

### Option E: Move `Condition` base class into `core.py` ❌ Rejected

Consolidate everything into `core.py`, compile the whole file, and
apply `allow_interpreted_subclasses=True` to `Condition` there.

**Why rejected:**
- Breaks the import DAG. `conditions.py` currently imports from nothing
  in the library; `core.py` imports from `conditions.py`. Merging them
  creates a single massive file with no clean layering.
- ~2,500 line limit on `core.py` (Principle V) would be exceeded.
- `condition_templates.py` would still inherit from compiled classes,
  and the cascade problem reappears.
- The module split exists precisely to keep user-subclassable ABCs
  separate from the compiled hot path. Merging destroys that invariant.

---

## Consequences

**Positive:**
- Users can subclass `Condition`, `FuncCondition`, `AsyncCondition` from
  plain Python — no mypyc knowledge required.
- `condition_templates.py` works without modification in both compiled
  and uncompiled modes.
- The library always works uncompiled (pure Python fallback) — compilation
  is strictly additive.

**Negative / watch-outs:**
- Condition evaluation code itself is not accelerated by mypyc. This is
  acceptable because conditions are caller-supplied logic, not dispatch
  infrastructure.
- Any new user-subclassable base class added to `core.py` (e.g., a future
  `Hook` or `Middleware` ABC) must use `@mypyc_attr(allow_interpreted_subclasses=True)`.
  Forgetting this will silently work in pure Python mode and crash only
  when the compiled extension is loaded (fast_fsm-ldp).
  **`tests/test_mypyc_guard.py` enforces this automatically via AST analysis.**

**Follow-up work:**
- If a future profiling pass shows condition evaluation is a bottleneck,
  consider providing a compiled `FuncCondition`-equivalent in `core.py`
  (as a non-subclassable helper, not a base class) as an opt-in
  acceleration path (fast_fsm-spf).
