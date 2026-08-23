---
name: code-review
description: General code-review pass - correctness, clarity, and API discipline.
---

# Code review

Read the whole change before commenting. For each hunk ask: what breaks if
this line is wrong; who calls this; what invariant does it assume. Report
findings with file, line, category, and a rationale that names the failure
scenario. Rank by severity: critical, high, medium, low, info.
