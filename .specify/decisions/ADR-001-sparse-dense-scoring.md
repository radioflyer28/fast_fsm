# ADR-001: Sparse vs. Dense FSM Scoring in EnhancedFSMValidator

**Status**: Accepted  
**Date**: 2026-03-05  
**Deciders**: project maintainer + AI pair

---

## Context

`EnhancedFSMValidator` produces an overall score and letter grade for an FSM.
One of its issue categories is "missing transitions" — state/event combinations
that have no registered transition.

For a fully-connected FSM this is a genuine design smell. But many well-designed
FSMs are *intentionally sparse*: a traffic light has no `emergency_stop` handler
in the `green` state by design, not by oversight. Under the original single-score
model, a structurally sound but sparse FSM consistently received a "D" grade,
which:

1. Was misleading — users trusted the grade, concluded their FSM was broken,
   and either added junk transitions or disabled the validator entirely.
2. Conflated two independent concerns: *structural correctness* (unreachable
   states, dead ends, non-determinism) with *completeness* (transition coverage).

The validator needed to distinguish deliberate sparsity from accidental omissions
without requiring the user to annotate their intent.

---

## Decision

We classify every FSM as either **sparse** or **dense** at analysis time using
heuristics on the transition density, then split the score into two independent
axes:

- **`structural_score`** — measures reachability, dead-end states, and
  determinism. Never penalised by missing transitions. This drives `grade`.
- **`completeness_score`** — measures transition coverage. Informational only;
  does not affect the grade.

Classification rule (in `_analyze_structure`):

```python
design_style = "sparse" if density < 0.4 and possible_transitions > 6 else "dense"
```

For sparse FSMs, missing-transition issues are emitted as `"info"` severity
instead of `"warning"`, so they appear in reports without inflating the score.

`overall_score` mirrors `structural_score`; `grade` is based on structural only.

---

## Considered Alternatives

### Option A: Auto-classify with split scoring ✅ Chosen

Described above. Auto-detection via density heuristic; no user annotation needed.

**Pros:**
- Zero user burden — works correctly out of the box for the common case
- Structural correctness and completeness remain independently readable
- Grade reflects what users actually care about (is the FSM *broken*?)

**Cons / tradeoffs:**
- The density threshold (0.4) and minimum-transitions guard (> 6) are
  heuristic. A micro-FSM with 4 states and 50% coverage could be
  misclassified. Acceptable given the guard clause.
- Slightly more complex report output (two scores instead of one).

---

### Option B: Single score with sparse warning ❌ Rejected

Keep one overall score but emit an informational note when the FSM appears
sparse, explaining why it scored low.

**Why rejected:** Still produces a "D" grade that users act on. The warning
explaining it is easy to miss and doesn't prevent the misleading outcome.

---

### Option C: User-supplied `sparse=True` flag ❌ Rejected

Allow `EnhancedFSMValidator(fsm, sparse=True)` to opt out of completeness
penalisation.

**Why rejected:** Puts burden on the user to correctly classify their own
design. Users building sparse FSMs often don't know that's the framing;
they just know the validator is yelling at them. Auto-detection is strictly
better UX here.

---

### Option D: Suppress all completeness issues for sparse FSMs ❌ Rejected

Same as chosen option but downgrade to silence (`"debug"`) rather than `"info"`.

**Why rejected:** Hides potentially useful information. A sparse FSM that is
*also* missing a transition the developer intended to add should still surface
that as a visible (if low-priority) item. `"info"` severity threads this needle.

---

### Option E: Upper-triangular transition matrix ❌ Rejected (related)

Considered for the machine-readable output alongside the scoring redesign.

**Why rejected:** An upper-triangular matrix is only meaningful for undirected
graphs. FSMs are directed and frequently have cycles (A→B and B→A are distinct,
and A→A is valid). An upper-triangular representation silently drops or
misrepresents these edges. A full N×N adjacency matrix was used instead.

---

## Consequences

**Positive:**
- Sparse FSMs that are structurally correct now receive accurate grades (A/B/C).
- The completeness story is still fully visible — just separated from the
  structural story.
- Existing dense FSM users see no change in behaviour or score interpretation.

**Negative / watch-outs:**
- The density threshold is a heuristic. Edge cases exist (very small FSMs).
  If misclassification becomes frequent, the threshold should be made
  configurable via a constructor kwarg rather than changing the default.
- `get_validation_score()` now returns more keys. Any downstream serialization
  that assumed a fixed key set needs updating.

**Follow-up work:**
- Consider exposing `design_style_threshold` as an optional constructor kwarg
  for users who want to tune the boundary (tracked separately).
- `completeness_score` is currently not factored into `grade` at all. If user
  feedback suggests completeness should have *some* weight for dense FSMs,
  a weighted blend (`0.8 * structural + 0.2 * completeness`) is the natural
  next step.
