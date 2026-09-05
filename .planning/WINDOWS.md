---
schema_version: 1
open_count: 1
waived_count: 0
fixed_count: 2
total_count: 3
last_updated: 2026-09-05T02:17:23.737Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 16 | deviation | tests/test_builder.py |  | Compiled mypyc constructor boundary requires a mode-neutral TypeError assertion. | fixed |  | 2026-08-30T05:20:02.323Z | 2026-08-30T05:20:30.064Z |
| 2 | 20 | deviation | tools/release_evidence.py |  | Removed unsupported uv pip install --no-project flag from isolated artifact install. | fixed |  | 2026-09-05T01:11:18.422Z | 2026-09-05T01:11:59.484Z |
| 3 | 20 | unrun-verify | evidence/release-baseline.json |  | Baseline freshness requires the reviewed uv 0.12.6 binary; local host only has uv 0.12.9. | open |  | 2026-09-05T02:17:23.737Z |  |

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
  },
  {
    "id": 2,
    "kind": "deviation",
    "phase": "20",
    "file": "tools/release_evidence.py",
    "line": null,
    "description": "Removed unsupported uv pip install --no-project flag from isolated artifact install.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-05T01:11:18.422Z",
    "resolved_at": "2026-09-05T01:11:59.484Z"
  },
  {
    "id": 3,
    "kind": "unrun-verify",
    "phase": "20",
    "file": "evidence/release-baseline.json",
    "line": null,
    "description": "Baseline freshness requires the reviewed uv 0.12.6 binary; local host only has uv 0.12.9.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-05T02:17:23.737Z",
    "resolved_at": null
  }
]
````
