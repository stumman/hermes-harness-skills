# Default Chains

Pick the closest and adapt. Stages in brackets are optional and used only when relevant.

**New feature / capability**
`spec-forge → recon → [architect] → contract-first → implement (+typescript-pro/java-pro) → test-engineer → critical-review → [security-sentinel] → docs-scribe → git-hygiene`

**Bug fix**
`debug → recon → implement → test-engineer (regression test first) → critical-review → git-hygiene`

**Refactor / cleanup**
`recon → refactor (under test guardrails from test-engineer) → critical-review → git-hygiene`

**Performance problem**
`perf-tuner (measure first) → recon → refactor/implement → test-engineer → critical-review`

**Security finding**
`security-sentinel → recon → implement → test-engineer → critical-review → git-hygiene`

**Migration / upgrade**
`modernizer → recon → architect → contract-first → implement → test-engineer → critical-review → docs-scribe`

**Dependency / build / pipeline work**
`dependency-steward and/or ci-cd-engineer → test-engineer → git-hygiene`
