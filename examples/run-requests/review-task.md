# Review task

Review this release-tooling module for correctness and security defects.

Report every defect you find as a structured finding: severity, category,
file, line, a short title, and an actionable rationale. Do not modify any
file. Do not approve a change whose tests you could not see pass.

Category values are precise kebab-case defect-type slugs (for example
`command-injection`, `off-by-one`, `null-dereference`) — never generic
labels like `correctness`. Reserve `critical`/`high` severities for
demonstrated defects at a specific location. Emit the structured review
exactly once, after your review is complete — a progress note, or an empty
findings list from an unfinished review, is not a valid result.
