---
phase: 15-release-baseline-evidence-harness
reviewed: 2026-08-29T22:16:49Z
depth: standard
files_reviewed: 25
files_reviewed_list:
  - .github/copilot-instructions.md
  - .github/workflows/ci.yml
  - .github/workflows/docs.yml
  - .github/workflows/release.yml
  - .specify/memory/spr-core-api.md
  - CHANGELOG.md
  - MANIFEST.in
  - README.md
  - Taskfile.yml
  - docs/dev/contributing.md
  - docs/dev/releasing.md
  - docs/dev/testing.md
  - docs/index.rst
  - docs/release-corrections/v0.2.3.md
  - evidence/release-baseline.json
  - pyproject.toml
  - setup.py
  - src/fast_fsm/core.py
  - src/fast_fsm/visualization.py
  - tests/test_advanced_functionality.py
  - tests/test_build_modes.py
  - tests/test_release_evidence.py
  - tools/__init__.py
  - tools/build_modes.py
  - tools/release_evidence.py
findings:
  critical: 4
  warning: 3
  info: 0
  total: 7
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-08-29T22:16:49Z  
**Depth:** standard  
**Files Reviewed:** 25  
**Status:** issues_found

## Summary

The exact-SHA hosted run `33276980655` passing all 29 jobs and the live v0.2.3
correction establish that the submitted happy path ran successfully. They do not
exercise several contradiction cases at the evidence boundary. Direct review and
targeted local reproductions found four release-blocking correctness/security
defects and three robustness/portability defects. In particular, the slots audit
can certify a class that has an instance dictionary, and the wheel inspector can
certify an archive whose embedded package name and version contradict its filename.

`uv.lock` was supplied in the workflow scope but is excluded from source review by
the review policy for generated lock files.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: A subclass without `__slots__` is falsely certified as slot-protected

**Classification:** BLOCKER  
**File:** `/Users/akriz/code/fast_fsm/tools/release_evidence.py:442-500`  
**Issue:** `_is_inherited_slot_protected()` treats the presence of a slotted local
ancestor as sufficient protection for a subclass. Python does not preserve that
property automatically: a subclass that omits its own `__slots__` receives an
instance `__dict__`, even when its base has `__slots__ = ()`. The validator then
labels that subclass `inherited-slot-protected` and permits it into the release
manifest. A focused reproduction using synthetic `ClassDeclaration` objects
returned a successful inventory while `hasattr(Child(), "__dict__")` was `True`.
This defeats the fail-closed slots-policy contract for future classes.

**Fix:** Require every non-exempt subclass to declare its own `__slots__`, and
reject declarations that include `__dict__`. Also account for any base that has
already introduced an instance dictionary. Add a regression equivalent to:

```python
class Base:
    __slots__ = ()

class Child(Base):
    pass

with pytest.raises(EvidenceError, match="Child"):
    validate_slots_inventory(scan_classes(source_root), {})
```

### CR-02: Wheel verification accepts contradictory distribution identity

**Classification:** BLOCKER  
**File:** `/Users/akriz/code/fast_fsm/tools/release_evidence.py:241-327`  
**Issue:** `_wheel_filename_tags()` discards the distribution name and version,
while `inspect_wheel()` reads only the `Version` header and never compares it to
the filename, the `.dist-info` directory, the expected package, or the release
identity. `_archive_metadata()` likewise accepts metadata from any dist-info
directory. A generated file named `fast_fsm-0.2.3-py3-none-any.whl` containing
`evil-9.9.dist-info` and `METADATA` with `Name: evil` and `Version: 9.9` was
accepted and classified as a valid pure wheel. The manifest can therefore certify
an unrelated or mis-versioned artifact.

**Fix:** Parse and normalize the full wheel filename identity, then require one
consistent identity across filename, dist-info directory, `METADATA Name`,
`METADATA Version`, and the expected release identity. Add negative tests for
each mismatch. For example, the verifier should enforce:

```python
if normalize_name(metadata_name) != normalize_name(PACKAGE_NAME):
    raise EvidenceError("Wheel package name contradicts release identity")
if Version(metadata_version) != Version(filename_version):
    raise EvidenceError("Wheel version contradicts filename")
```

### CR-03: Release and Pages credentials are exposed to mutable action tags

**Classification:** BLOCKER  
**Files:**

- `/Users/akriz/code/fast_fsm/.github/workflows/release.yml:38-138`
- `/Users/akriz/code/fast_fsm/.github/workflows/docs.yml:18-21`
- `/Users/akriz/code/fast_fsm/.github/workflows/docs.yml:36-61`
- `/Users/akriz/code/fast_fsm/.github/workflows/ci.yml:18-276`

**Issue:** Nearly every third-party action is referenced by a mutable major or
release tag. Most seriously, `softprops/action-gh-release@v2` executes in a job
with `contents: write`, and the docs workflow grants `pages: write` and
`id-token: write` at workflow scope, so the build job and its mutable actions
inherit deployment privileges they do not require. A moved or compromised tag can
therefore alter release artifacts, create releases, or obtain a Pages OIDC token.
The full-SHA pin already used for `arduino/setup-task` shows that immutable action
references are supported by the repository.

**Fix:** Pin every executable action to a reviewed full commit SHA and retain the
human-readable version as a comment. Set workflow-level permissions to read-only,
then grant Pages/OIDC only to `deploy_docs` and `contents: write` only to the
smallest release-publishing job. Add a workflow contract test that rejects
non-local `uses:` values not ending in a 40-character SHA.

```yaml
permissions:
  contents: read

jobs:
  deploy_docs:
    permissions:
      pages: write
      id-token: write
```

### CR-04: The manifest claims benchmark evidence that the collector never records

**Classification:** BLOCKER  
**Files:**

- `/Users/akriz/code/fast_fsm/tools/release_evidence.py:872-937`
- `/Users/akriz/code/fast_fsm/evidence/release-baseline.json:26-36`
- `/Users/akriz/code/fast_fsm/README.md:3-24`
- `/Users/akriz/code/fast_fsm/README.md:465-477`
- `/Users/akriz/code/fast_fsm/docs/index.rst:4-7`
- `/Users/akriz/code/fast_fsm/docs/dev/testing.md:117-129`

**Issue:** `collect_manifest()` collects tests, coverage, wheels, slots, and tool
versions, but never invokes a benchmark or accepts a benchmark result. Its
`performance_contract` contains only the 200,000 ops/sec floor and a prose string.
Nevertheless, both user and developer docs say the manifest records
"environment-labeled benchmark observations." The same docs retain unsupported
`5–20x`, `~1000x`, and history `<= 2x` performance claims. Thus the canonical
evidence artifact cannot substantiate the claims the phase says it owns, and a
freshness pass can succeed without any performance observation.

**Fix:** Record a structured, environment-labeled observed benchmark result (and
the command/mode used to obtain it) in the manifest. Exclude volatile values from
stable freshness comparison if deterministic regeneration is required, but still
require the observation to be present and valid. Until that evidence exists,
remove the benchmark-observation statements and unsupported comparative numbers
from README and Sphinx landing pages.

## Warnings

### WR-01: The developer testing example raises before constructing the FSM

**Classification:** WARNING  
**File:** `/Users/akriz/code/fast_fsm/docs/dev/testing.md:74-96`  
**Issue:** The example calls `StateMachine("traffic", initial_state=red)`, but the
constructor's first positional argument is already `initial_state`; running the
example raises `TypeError: argument for __init__() given by name
('initial_state') and position (1)`. The ordinary fenced block is not executed by
the doctest gate, so CI passes while publishing broken contributor guidance.

**Fix:** Use `StateMachine(red, name="traffic")`, remove the unused imports, and
convert the example to executable `{testcode}`/`{testoutput}` markup (or add an
equivalent documentation contract test).

### WR-02: Local pure-source gates run imports before checking for native shadows

**Classification:** WARNING  
**File:** `/Users/akriz/code/fast_fsm/Taskfile.yml:26-52,270-284`  
**Issue:** The local `test*` tasks describe themselves as pure Python but only set
`FAST_FSM_BUILD_MODE=pure`; that environment variable cannot stop an existing
`core*.so`/`core*.pyd` from winning import resolution. `release-gate` runs tests
and both documentation builds before its first `verify-source` call, which occurs
inside the final `release-baseline-check`. On a dirty compiled worktree, earlier
steps can therefore validate the native module while being labeled pure, and the
gate fails only after doing the wrong work.

**Fix:** Make `pure-source-check` the first command/dependency of `release-gate`,
and make independently runnable pure `test*`/docs tasks preflight before importing
the package. Add a Taskfile contract test that asserts the preflight precedes every
pure test or documentation command.

### WR-03: Canonical evidence tasks are POSIX-only and leak temporary directories

**Classification:** WARNING  
**File:** `/Users/akriz/code/fast_fsm/Taskfile.yml:118-142`  
**Issue:** Both canonical baseline tasks depend on POSIX shell syntax, `mktemp`,
and `find`, so they do not run under the default Windows Task shell despite Windows
being a supported release platform. They also never remove the generated
temporary directory. This makes the documented canonical interface platform
dependent and leaves wheel artifacts behind on every invocation.

**Fix:** Move temporary wheel construction/discovery into the Python evidence CLI
using `tempfile.TemporaryDirectory`, or add explicit per-platform Task variants
with guaranteed cleanup. Keep exactly one-wheel validation in the Python layer so
the same failure semantics apply on Windows, macOS, and Linux.

---

_Reviewed: 2026-08-29T22:16:49Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
