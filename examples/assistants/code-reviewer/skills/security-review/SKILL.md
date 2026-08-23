---
name: security-review
description: Security pass - injection, boundaries, data handling, secrets.
---

# Security review

Trace every external input to its sinks. Flag command, path, and query
injection; off-by-one and boundary errors; mutation of caller-owned data;
secrets or tokens in code or logs. For each finding name the attack or
failure path concretely and the smallest fix that closes it.
