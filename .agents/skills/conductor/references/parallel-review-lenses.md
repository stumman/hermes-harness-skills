# Parallel Review Lenses

For code reviews and audits on multi-file changes, dispatch 5 review lenses as parallel subagents instead of sequential review.

- **Lens 1 — Correctness & Robustness:** Does the code do what it claims? Error handling, edge cases, plan conformance.
- **Lens 2 — Security & Trust:** Auth, injection, secrets, crypto, supply chain. Routes through security-sentinel patterns.
- **Lens 3 — Architecture & Design:** Right boundaries? Inward deps? Contract fidelity? Over-abstraction?
- **Lens 4 — Performance & Scalability:** N+1 queries, sync I/O, memory leaks, algorithmic complexity.
- **Lens 5 — Tests & Coverage:** Test integrity, coverage gaps, weakened assertions, missing error-path tests.

Each lens gets: full plan/spec + detected tech stack + relevant skill content. Results are synthesized into a consolidated report.

## Lens-specific context (in addition to shared pre-computed context)

- **L1 (Correctness):** file-to-lens assignment, plan/spec, acceptance criteria, error handling conventions
- **L2 (Security):** auth middleware locations, trust boundaries, secret stores, crypto libraries used
- **L3 (Architecture):** dependency graph, module boundaries, ADRs, directory structure
- **L4 (Performance):** DB query files, external service calls, loop/map locations, memory-intensive paths
- **L5 (Tests):** test file inventory, coverage reports, test framework, mock/stub conventions

## Quality-gated lens merging

Default is 5 separate lenses. If the codebase is small (< 15 files), merge L3+L4 (Architecture+Performance) into one subagent to save one spawn. Gate: if the merged lens produces lower-quality output (fewer findings, less specific), revert to separate lenses next time. Only merge when empirically verified — injecting more context into a merged call worsens compression rather than relieving it.
