# Working method

1. Read the task statement, then the change in full before judging.
2. Apply the code-review skill for the general pass, the security-review
   skill for injection/boundary/data-handling analysis, and the
   test-analysis skill for coverage and oracle quality.
3. Record each finding with: id, severity, category, file, line, title,
   rationale. The category is a precise kebab-case defect-type slug naming
   the specific defect class (for example `command-injection`, `off-by-one`,
   `input-mutation`, `race-condition`, `null-dereference`) — never a generic
   label like `correctness`, `robustness`, or `code-quality`.
4. Report each underlying defect once, at its primary location, under its
   most specific category. Reserve `critical` and `high` for specific,
   demonstrated defects at a specific location; systemic or supporting
   observations (coverage gaps, style, defense-in-depth) are `medium` or
   lower.
5. Summarise agreement between what the tests claim and what the code does.
6. Produce the structured review exactly once, in the requested output
   schema, only after the review is complete — never a partial or progress
   report.
