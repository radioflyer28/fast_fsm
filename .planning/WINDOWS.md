---
schema_version: 1
open_count: 0
waived_count: 0
fixed_count: 1
total_count: 1
last_updated: 2026-08-30T05:20:30.064Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 16 | deviation | tests/test_builder.py |  | Compiled mypyc constructor boundary requires a mode-neutral TypeError assertion. | fixed |  | 2026-08-30T05:20:02.323Z | 2026-08-30T05:20:30.064Z |

````json
[
  {
    "id": 1,
    "kind": "deviation",
    "phase": "16",
    "file": "tests/test_builder.py",
    "line": null,
    "description": "Compiled mypyc constructor boundary requires a mode-neutral TypeError assertion.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-08-30T05:20:02.323Z",
    "resolved_at": "2026-08-30T05:20:30.064Z"
  }
]
````
