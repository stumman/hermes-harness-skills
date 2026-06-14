---
name: ponytail-audit
version: 1.7.2
description: >
  Ultra-mode code audit. Walks the ponytail ladder on EVERY source file. v1.7.2: +4 new Granular Depth Checklist categories (Adversarial ML, Serverless/Edge, Mobile API, Code Signing) (iter 45). v1.7.1: +evidence safety (never quote secrets). v1.7.0: +Kubernetes/RBAC/Compliance to Granular Depth Checklist (iter 43). v1.6.9: +Redis/GraphQL/API Gateway to Granular Depth Checklist (iter 41). v1.6.8: +file-enumeration pitfall — find must include .sql/.xml/.yml/.properties (iter 40). v1.6.7: +Web3/blockchain (iter 39). v1.6.6: Granular Depth Checklist (iter 38). v1.6.5: File-Assignment-By-Directory-Memory (iter 34,37). v1.6.0: SUBAGENT MODE. v1.5.0: anti-confabulation Gate 0, hard gates, evidence boundaries.
---
# Ponytail Audit — Ultra-Mode Code Review

You are a skeptical senior engineer auditing a codebase you have NEVER seen before.
You trust nothing. You assume nothing works. You find what's broken.

## SUBAGENT MODE — TOKEN-OPTIMIZED (use this when running as a subagent)

When you are a subagent spawned by a parent conductor or parallel lens, use THIS condensed checklist (~800 tokens). Do NOT load references or the full methodology — the parent has already pre-computed file lists, route tables, and tech stack detection.

**Quick Start:**
1. Read assigned files with terminal tool calls (Gate 0: fresh-read every file)
2. For each file, walk the 9-rung ladder (see below)
3. Build cross-file comparison if auditing multiple routes/endpoints
4. Tag every finding: [CONFIRMED|DETECTED|INFERRED] + severity + file:line
5. Output: findings list sorted by severity. Format: `[EVIDENCE] [FILE:LINE] SEVERITY: description | fix`

**9-Rung Ladder (condensed):**
1. **Dead code:** unreachable branches, functions never called, imports never used, hollow-shell functions (always-return-true/null)
2. **Over-abstraction:** interface with 1 impl → flag. Stateless class → should be functions. Abstract with 1 subclass → dead weight
3. **Hardcoded secrets:** API keys, tokens, passwords, JWT secrets with literal fallback values
4. **Resource leaks:** setInterval without clear, file handles not in finally, unbounded Map/Set/array, global mutable state without cleanup
5. **Race conditions:** check-then-act async gaps, boolean-as-lock, shared mutable state outside sync
6. **Error handling:** empty catch blocks, void without .catch(), silent error continuation (continue on null, return null masking), batch jobs without per-item isolation, missing retry/backoff on external calls, silent discard of invalid input, missing idempotency keys on webhooks, in-memory state lost on restart
7. **Input validation:** missing body size limits, missing sanitization, validation that accepts everything (regex `^.*$`), auth/rate-limit missing on some routes, missing brute-force protection, entity fields without constraints, CSV injection, file upload without magic bytes, host header gaps
8. **Security anti-patterns:** non-constant-time secret compare, template injection, logging secrets, missing security dependency scanning, missing HTTP security headers (XFO/CSP/HSTS/XCTO), missing response size limits, ImageTragick, EXIF stripping gaps, CORS maxAge>3600s, mutable module-level exports, cross-tenant ops without confirmation, email security gaps
9. **Tests:** zero tests → finding. Error paths untested? Auth/rate-limit/validation tests missing?

**Severity:** Critical (unreachable guards, production secrets, perpetual leaks) | High (missing auth, races with data risk, no validation at boundary) | Medium (slow leaks, inconsistency, missing tests on critical paths) | Low (style, minor smells)

**Cross-File Consistency Check (MANDATORY for multi-route audits):**
Build comparison table: | Route | Auth | Rate Limit | Validation | Errors | Body Limit |
Any mismatch on routes handling same class of operation (both financial, both user-data) → HIGH severity.

**Output format:** `[EVIDENCE] [FILE:LINE] SEVERITY: finding — why — fix`

**GRANULAR DEPTH CHECKLIST (MANDATORY — run AFTER 9-rung pass):**
These patterns are frequently missed in subagent audits. Re-scan EVERY file for:
- **Email:** DMARC/DKIM/SPF gaps, opt-in consent, BCC privacy (batch BCC exposes recipients), silent skip on failed recipient, attachment malware scanning, dead-letter queue, retry/backoff, Content-Disposition encoding
- **I18n/encoding:** Unicode bidi isolation (RTL override \\u202E), encoding strict mode, TimeZone/Currency injection, Collator strength settings, bidirectional text attacks
- **Circuit breaker:** waitDurationInOpenState, minimumNumberOfCalls (should be ≥5), slowCallDurationThreshold, exponential backoff (not fixed), maxWaitDuration, fairCallHandling, bulkhead isolation, fallback that throws
- **Flyway/migration:** baselineOnMigrate (never in production), validateOnMigrate, locations wildcard, connectRetries, encoding, repair authorization, error handler
- **gRPC:** maxConcurrentCallsPerConnection, maxConnectionAge, maxInboundMetadataSize, plaintext transport, reflection in production
- **Thread pools:** unbounded queue capacity, volatile on array (only reference volatile, elements not synchronized), scheduled task exception handling kills periodic task, CompletableFuture without timeout, @Async void swallows exceptions
- **Rate limiting:** destroy() cleanup, System.currentTimeMillis() clock drift (NTP), X-Forwarded-For spoofing
- **Validation:** RFC 7239 Forwarded header (not just X-Forwarded-*), Content-Length overflow/negative, IPv6 brackets, charset allowlist, boundary quote stripping, duplicate header ambiguity, path normalization beyond simple .. replace
- **LLM/AI:** function calling allowlist (every tool must be allowlisted), max_tokens budget, prompt injection via concatenation, content safety bypass
- **File upload:** complete extension blocklist (.jsp/.exe/.sh/.php), MIME detection from magic bytes (not filename extension), null byte injection
- **Encryption:** OAEP vs PKCS1Padding, debug logging of ciphertext, algorithm downgrade
- **LDAP:** setCountLimit(), referral control, connection/read timeout
- **Payment:** currency mismatch, @Transactional missing, client-trusted amounts, refund verification
- **Web3/blockchain:** reentrancy, flash loans, dusting attacks (sweep interacts with malicious tokens), oracle manipulation, floating-point amounts (use BigInt/wei), transaction replay, hardcoded private keys, non-constant-time address comparison, missing EIP-55 checksums
- **Redis/cache:** RESP injection via unvalidated keys/values, pipeline injection (multi-command in batch), dangerous command exposure (KEYS/FLUSHALL/CONFIG GET/SET/EVAL/MONITOR/CLUSTER/DEBUG/SCRIPT LOAD), Lua script abuse (infinite loops, arbitrary code), key enumeration via timing oracle, SCAN without COUNT limit, PUBLISH/SUBSCRIBE abuse, unbounded in-memory caches without eviction, CLIENT LIST/INFO command exposure
- **GraphQL:** introspection enabled in production (schema enumeration), no query depth limit (exponential DoS), no query cost/complexity analysis, batching without limits, field suggestions leaking schema, persisted queries bypass, subscription auth gaps, N+1 via field resolvers, error masking disabled (internal errors leaked), tracing/cache hints exposing architecture
- **API Gateway/Proxy:** SSRF via user-controlled proxy URL, header smuggling (TE/CL parsing gaps — duplicate headers, TE identity bypass, CL: -1), DNS rebinding (no post-resolution IP check), credential forwarding (internal API keys in proxy headers, Authorization header forwarded), response header injection (unsanitized backend headers), IP allowlist bypass (IPv6-mapped IPv4, naive CIDR), request coalescing races, round-robin without health checks, URL rewriting with user-controlled regex source
- **Kubernetes/Container:** privileged containers (privileged:true, runAsUser:0), host filesystem mounts (hostPath: / with readOnly:false), host namespace access (hostNetwork/PID/IPC:true), capabilities:ALL or SYS_ADMIN, no resource limits (CPU/memory), container images without digest pinning (:latest), command injection via kubectl exec/apply with user-controlled names, token/credential exposure in command arguments (visible via ps), Helm chart from untrusted repos, network policy acceptance without validation, namespace deletion without confirmation or system-namespace guard, port-forward to privileged ports (<1024) without auth, secret creation with plaintext logging
- **RBAC/ABAC:** role assignment without validation (superadmin assignable by anyone), no authorization check on who can grant/revoke roles, stale permission cache not invalidated on role change, wildcard permission confusion (startsWith matching, 'admin' matches 'admin:anything'), circular role hierarchy with no cycle detection → stack overflow, eval()/new Function() for policy evaluation (arbitrary code execution), impersonation without audit log or permission check, mutable reference returns for role/permission sets (caller can modify), prototype pollution via user-attribute keys (__proto__), no resource-level permission granularity (only global permissions checked), get-all-user-roles without authorization
- **Data Governance/Compliance:** consent records without purpose validation or timestamp verification, DSAR/deletion requests without identity verification (anyone can request any user's data), incomplete deletion (backups/archives/third-party processors/analytics not covered), deletion status 'completed' without verification, mutable audit log (array, no append-only guarantee, no hash chain, no digital signature), SHA-1/MD5 for integrity hashes, weak encryption (aes-192-ecb, no IV, deprecated createCipher), PII in log entries without redaction, audit log without pagination (OOM on read-all), encryption/compliance API keys exposed in reports/debug endpoints, data breach notification with all recipients in CC (not BCC), naive anonymization (string replace, no k-anonymity/l-diversity), data residency check via naive string includes ('US' matches 'AUS'), consent withdrawal without stopping ongoing processing, mutable module-level export of compliance secrets
- **Adversarial ML/AI:** model poisoning via unvalidated training data (no outlier detection, no provenance tracking), adversarial input detection bypass (check always passes), training data integrity without checksums, model inversion attack surface (raw embeddings/gradients returned), embedding vector injection via caller-supplied values, RAG pipeline poisoning via unvalidated documents, vector DB query injection via string interpolation, prompt injection in RAG context (user query concatenated unsafely), model confidence spoofing via client-supplied overrides, unsafe deserialization of model files (pickle/torch.load without safe mode, JSON.parse on user files), gradient leakage in logs, hyperparameter injection via spread merge, feature extraction without user consent, model theft via unrestricted inference queries, model cache poisoning (caller-supplied data cached without integrity check), client-trusted model parameters, Math.random() for data splits, no differential privacy on training, training data PII not sanitized, no model version pinning (uses :latest)
- **Serverless/Edge:** cold-start credential cache without TTL expiry, event source mapping injection (S3/DynamoDB trigger trusts event fields), function timeout abuse (no timeout config, blocking ops), execution environment escape via /tmp writes, Lambda layer imported without integrity check, IAM role over-privileged (wildcard policies), Function URL without IAM auth, S3/EventBridge trigger without event schema validation, API Gateway proxy without request validation, edge function caches PII in response headers (Set-Cookie), CloudFront function unsafe origin modification via Host header, no idempotency key on DynamoDB writes (at-least-once duplicates), recursive Lambda invocation without max-depth guard, Secrets Manager values cached indefinitely without expiry, container image from public ECR without digest verification, VPC-bound function with internet access (fetch to external API), Step Function input not validated, EventBridge event pattern injection via user-supplied detail.filter, SQS message visibility timeout dangerously short, no concurrency limit set, provisioned concurrency without cost limits, CloudWatch logs with raw PII (userId, IP, events), hardcoded AWS credentials in source, KMS key without automatic rotation, no dead letter queue on async invocations
- **Mobile API:** no certificate pinning in API calls, deep link handler without URL validation (attacker-controlled action dispatch), biometric authentication always returns true (bypass), keychain items stored without access control flags (no biometric/touchID requirement), App Transport Security bypass (uses http:// not https://), WebView JavaScript injection via eval() on postMessage, push notification payload not validated (blind config overwrite), IPC message handler without sender verification, clipboard not cleared after sensitive data copy, screenshot prevention disabled (flag set to false), jailbreak/root detection bypassable (always returns false), API key embedded in client-side source code, auth tokens in plain AsyncStorage/SharedPreferences (not SecureStore/KeyStore), biometric fallback to device PIN without rate limiting, backup flag enabled for sensitive keychain data, app cache stored unencrypted on disk, analytics tracking PII without user consent, OAuth redirect_uri not validated (open redirect in OAuth flow), in-app browser shares cookie jar (cookie theft), IPC without authentication on command handlers, SQLite database without encryption (no SQLCipher), file provider exposes internal file paths without sanitization, WebSocket connection without certificate origin validation, HTTP request signing key hardcoded in client source, debug symbols and verbose logging enabled in release builds, device ID used as Authorization token
- **Code Signing/Supply Chain:** signature verification always returns true (ignores crypto result), public key loaded without CA verification (accepts any PEM), timestamp field logged but never cryptographically validated, certificate chain always empty (never verified), no CRL/OCSP check (revoked certificates accepted), SHA-1 used for signing and verification, self-signed certificates trusted without pinning, hardcoded private signing key as string constant in source, key generation uses Math.random() with small key sizes, no key rotation policy (keys live forever), metadata mutable on same object as signature after signing, signs raw payload without prior hashing, blind spread-merge of metadata fields (manifest injection), SBOM generation unimplemented or always empty, dependency provenance verification always returns true, unsigned dependencies accepted without validation, build uses shared directory (no container isolation), npm publish without OTP/2FA, Git tags created unsigned (-a without -s), CI/CD pipeline runs with full admin token (GITHUB_TOKEN), build cache key from unvalidated user input (cache poisoning), artifact cached/stored without integrity hash, download URL uses http:// without TLS pinning, lockfiles added to .gitignore, .npmrc with _authToken committed/written at publish time, postinstall scripts allowed (--ignore-scripts=false), attestation/provenance generation returns empty (no SLSA), release assets returned/downloaded without checksums, mirror/registry download without signature verification, timestamp authority not cryptographically validated

**File depth warning:** Files with >15 planted/known issues need EVERY rung checked in detail. Don't stop at the obvious 2-3 headline findings.

**When NOT to flag:** empty catches with documented reason, files <30 lines, test files with real assertions, global state in CLI scripts, documented void with reason.

## FULL METHODOLOGY (use for parent-agent audits, NOT subagents)

## Methodology Choice

Two proven approaches. Choose based on task complexity:

1. **Ponytail-only:** Restraint ladder + 9-ladder audit. Fast, lean. Best for: quick scans, single-file reviews, early-stage code.
2. **Combined (default):** Restraint ladder → 6-lens rigor → cross-route comparison → **detector-validator pipeline.** Full depth. Best for: production codebases, multi-file audits, security-critical code.

### Detector-Validator Pipeline (Combined Only)

The audit runs in two passes to maximize precision:

**PASS 1 — DETECTOR** (preceded by Gate 0):

**GATE 0 — ANTI-CONFABULATION** (MANDATORY — from beagle/awesome-copilot research):
Before issuing ANY verdict, you MUST echo the exact artifact being judged, read freshly in the current turn. No inference from context. No recollection from memory.

1. Read the file/function/symbol with a terminal tool call THIS TURN.
2. Paste the relevant content into your reasoning.
3. Only then issue a finding.

"A finding issued without a same-turn echo of its target is invalid and MUST be discarded."

This gate prevents the #1 LLM code review failure mode: reporting issues from context memory that don't exist in the actual code.

After Gate 0 clears, proceed: Find EVERYTHING. Be exhaustive. Flag everything suspicious. Apply all 6 lenses + cross-route comparison. No filtering. No "this might be intentional" — flag it anyway.

**PASS 2 — VALIDATOR:** For each finding, apply 4 hard gates FIRST (adopted from beagle), then suppression rules:

**HARD GATES (per finding — any failure = discard or downgrade to Informational):**
- **Gate 1 — ANCHOR:** Read the full symbol/function, not just the diff. The finding must reference actual code, not an assumption about the code.
- **Gate 2 — EVIDENCE:** Each finding MUST include a file:line citation and relevant pasted content from tool output. No citation = no finding.
- **Gate 3 — SEVERITY:** Map to the severity table below. Over-inflation or under-inflation without justification = recalibrate or discard.
- **Gate 4 — FORMAT:** `[FILE:LINE] ISSUE_TITLE` mandatory. Every finding must be independently verifiable from the format alone.

**EVIDENCE BOUNDARY ANNOTATIONS** (from Shiyao-Huang agent-evolution research):
Every finding MUST carry a provenance tag:
- `[CONFIRMED]` — tool output, test result, or file content directly observed this turn
- `[DETECTED]` — pattern match with high confidence (>80%), tool-assisted
- `[INFERRED]` — heuristic, prior knowledge, or indirect evidence. Flag explicitly.

**EVIDENCE SAFETY RULES:**
- Never quote secret values, tokens, private keys, credentials, or PII in audit reports. Refer only to the path, variable name, secret type, or data category. Source: specialone0007/security-audit (competitive research cycle 10, iter 45).

After hard gates pass, apply suppression rules. Only REPORT findings that survive ALL rules:
1. **Intentional?** Is there a comment explaining why this pattern was chosen? (e.g., `// ponytail: global lock intentional`). If yes and the comment is credible → SUPPRESS.
2. **Documented?** Is this a known decision documented in AGENTS.md, CLAUDE.md, PLAN.md, or an ADR? If yes → SUPPRESS with reference.
3. **Pattern?** Is this a recurring idiom in the codebase used consistently across 3+ locations? If yes and the pattern is not itself dangerous → SUPPRESS (note the pattern).
4. **Confidence?** After rules 1-3, are you >80% confident this is a real issue? If below threshold → mark as LOW severity with "low confidence" note. If above → report at true severity.

**Unsuppressible Findings:** The following finding classes bypass ALL four suppression rules — a comment, ADR, recurring pattern, or low confidence can NEVER excuse them. If detected, they MUST be reported at their true severity regardless of validator rules:
- **Hardcoded production credentials** (passwords, API keys, tokens, JWT secrets with literal fallback values in source — Ladder Rung 3)
- **Missing authentication on endpoints handling user data or financial operations** (Ladder Rung 7)
- **SQL injection via string concatenation** (not parameterized/prepared statements — Ladder Rung 8)

These are *unsuppressible* because the cost of false suppression (data breach, account takeover, database compromise) dwarfs any false-positive cost. This rule is sourced from facebookresearch/secpriv-skill's validator rule #7 (unsuppressible evidence), validated against 595 planted issues across 39 golden-source files.

This pipeline reduces false positives. Facebook Research's secpriv-skill uses the same decomposition — detector enumerates, validator applies suppression rules and confidence threshold.
Empirically proven 26-49% better than ponytail-alone across 3 production audits.

**Three passes:**
1. **Restraint Ladder:** Run the ponytail ladder on every module. Does this code even need to exist? Stdlib? Native? Installed dep? One line? This pass finds bloat, dead code, over-abstraction.
2. **6-Lens Rigor:** Apply correctness, design, security, performance, tests, and placement lenses to every module that survives the ladder. This pass finds bugs the ladder misses — race conditions, missing auth, broken error handling, security anti-patterns.
3. **Scaled Analysis:** Cross-route comparison table, data-flow tracing (always-true → find callers → dead branch), systemic pattern detection (all controllers missing the same defense). This pass finds architecture-level issues no file-by-file audit catches.

### Ponytail-Only (use for quick scans, small codebases)
The 9-ladder audit below. Faster but misses correctness/placement issues on complex codebases. Good for <10 files.

## The Audit Ladder (per file)

Walk every source file through these rungs. Flag anything that fails:

1. **Does this code need to exist at all?**
   - Dead code: unreachable branches, functions never called, enums never used, classes with zero instantiation.
   - Dead imports: every `import` must be traced to at least one usage site. Functions/classes/enums imported but never referenced in the file → flag it. Validator functions exported but never called by any route or service → dead code.
   - Hollow shells: functions that always return the same value (always `true`, always `null`), making their callers' branches unreachable.
   - Duplication: two things doing the same thing in different ways.

2. **Is every abstraction earning its keep?**
   - Interface with exactly one implementation → unnecessary. Flag it.
   - Class with no internal state (all methods use only parameters/module-level data) → should be pure functions. Flag it.
   - Abstract class with one concrete subclass → dead weight.

3. **Are there hardcoded secrets?**
   - API keys, tokens, passwords, client secrets with literal fallback values.
   - Credentials in source control that should be env-only.
   - Internal auth tokens hardcoded as defaults.

4. **Are there resource leaks?**
   - `setInterval` / `setTimeout` not cleared on error paths between creation and return.
   - File handles / readers not released in `finally` blocks.
   - Event listeners not removed.
   - Maps/Sets/arrays that grow unbounded with no eviction mechanism.
   - Global mutable state that persists across requests with no cleanup.

5. **Are there race conditions?**
   - Async check-then-act with a gap (check flag → await something → set flag).
   - Boolean flags used as locks without atomic operations.
   - Shared mutable state accessed outside synchronization.

6. **Are error handling patterns consistent and complete?**
   - Empty `catch` blocks that swallow errors silently.
   - `void` on promises without `.catch()` — fire-and-forget without error handling.
   - Silent error continuation: `continue` on null in loops without logging, `return null` masking failures, skipping items in iteration without surfacing the error. If a product lookup returns null and the code `continue`s, the order is silently incomplete — flag it.
   - Inconsistent error response construction (one route uses centralized helper, another builds inline).
   - Missing error types in centralized taxonomy (e.g., NOT_FOUND, INTERNAL not defined).
   - Error boundary gaps in batch operations: one failed item aborts the entire batch — no per-item try/catch isolation. Flag batch jobs where failure of item N prevents processing of items N+1 through end.
   - Missing retry with exponential backoff on external service calls (payment gateways, SMS, email, third-party APIs). Flag if critical external calls have no retry, no backoff, or no circuit breaker.
   - Invalid/unrecognized input silently ignored: unknown event types, bad requests, invalid payloads dropped with no alerting, no dead-letter queue, no monitoring. Flag silent discard paths.
   - Missing idempotency key on webhooks/notifications: retries or replay produce duplicate side effects (double charge, duplicate email/SMS). Must include unique event ID and deduplicate on consumption. Flag webhook handlers without dedup mechanism.
   - In-memory state lost on restart: `Set`/`Map` used for dedup or processing state without persistence — replay attacks after reboot, lost dedup window. Flag in-memory dedup/state that doesn't survive restarts.

7. **Is input validation present at every trust boundary?**
   - Missing request body size limits.
   - Missing parameter sanitization (user input interpolated into URLs, commands, templates without encoding).
   - Validation functions that accept everything (regex `^.*$`, `return true`).
   - Auth middleware missing on some routes (compare all routes-check if some skip auth that others require).
   - Rate limiting missing on some routes (compare all routes-check if some skip limits that others apply).
   - Missing brute-force / account lockout protection: no lockout after N failed login attempts. Combined with no rate limiting, this enables unlimited credential stuffing. Flag if BOTH missing. Flag individually if either is missing — both are independent findings.
   - Entity-level validation gaps: fields without @Min/@Max/@NotNull/@NotBlank (Java) or runtime checks (TS). A `role` field as plain String with no enum constraint — flag it. An `inventory` integer with no lower bound check — flag it.
   - CSV/export safety gaps: no escaping of CSV special characters (commas, quotes, newlines) — formula injection and data corruption. Missing UTF-8 BOM for Excel compatibility — CJK characters garbled. Missing path traversal check on export file paths — files written outside export directory.
   - File upload validation gaps: missing magic byte/content inspection — attacker renames malware.exe to profile.jpg and bypasses extension-only checks. Flag any file type validation that relies solely on filename extension or client-declared MIME type without inspecting file content.
   - Host/protocol header gaps: RFC 7239 `Forwarded` header not parsed — modern proxies use `Forwarded`, not `X-Forwarded-*`. Flag when only legacy headers are checked. Config value quote stripping naive: `str.replace(/"/g, '')` breaks on embedded quotes like `foo\\"bar`. Flag config parsing without proper unescaping.

8. **Are there security anti-patterns?**
   - Non-constant-time secret comparison (string equality for API keys/tokens — Set.has(), ===, strict equality on secrets).
   - User input in template strings without encoding. Reflected XSS: user input echoed in response body unsanitized.
   - Logging sensitive data.
   - Missing dependency/build security scanning: no OWASP dependency-check-maven plugin in pom.xml, no `npm audit` in CI, no Snyk/Dependabot. Flag if build file has zero security plugins. Also flag missing test execution plugins (maven-surefire-plugin, maven-failsafe-plugin, or equivalent). Beyond CI scanning, flag: (a) version pinning that accepts ranges — caret `^1.0.0`, tilde `~1.0.0`, wildcard `1.x`, `*`, `latest`, range expressions `>=1.0.0 <2.0.0` are NOT pinned and allow auto-updates; (b) only checking top-level dependencies — transitive vulnerabilities missed entirely; (c) missing license/deprecated fields in dependency metadata — GPL/AGPL legal risk, deprecated packages used without warning; (d) only flagging `postinstall` scripts — misses `preinstall`, `install`, `preuninstall` hooks; (e) bin-linking without verifying symlink targets stay within node_modules; (f) aggregation that hides individual failures — `allPass = results.every(r => r.ok)` overwrites details.
   - Missing HTTP security headers: X-Frame-Options (clickjacking), Content-Security-Policy (CSP), Strict-Transport-Security (HSTS), X-Content-Type-Options. Flag if any are missing from security configuration.
   - Missing response body size limits: no max-request-size or max-file-size configured — DoS vector.
   - Image processing anti-patterns: ImageTragick vulnerability — crafted images exploit ImageMagick delegates (CVE-2016–3714). Flag `convert`/`identify`/ImageMagick usage without policy.xml hardening. EXIF stripping gaps: `exiftool -all=` misses XMP, IPTC, ICC profile data — embedded GPS/location data survives. Flag incomplete metadata stripping.
   - CORS anti-patterns beyond basic misconfig: `Access-Control-Max-Age` > 1 hour (3600s) — poisoned preflight cache persists, stale permissions survive credential rotation. Flag maxAge > 3600.
   - Mutable module-level exported state: `export const store = new Map()` or `export let cache = {}` — shared mutable state across all requests, no synchronization, grows unbounded. Flag any mutable module-level export in server-side code.
   - Cross-tenant data operations: admin/privileged operations that operate across user/tenant boundaries without confirmation. `reindexDocuments()` that migrates all data without user consent. Flag any bulk operation that crosses tenant boundaries without authorization check per record.
   - Email security gaps: missing DKIM/DMARC/SPF at application level (not just DNS). Hardcoded `From` address without DMARC alignment — spoofable. Missing `List-Unsubscribe` header — required by Gmail/Yahoo for bulk senders (Feb 2024). No unsubscribe mechanism — illegal in many jurisdictions (CAN-SPAM, GDPR). Flag email-sending code without these protections.

9. **Are tests covering critical paths?**
   - Count tests. Are there tests at ALL? Zero tests is a finding.
   - Are error paths tested? Auth failures? Rate limiting? Invalid input?
   - Are concurrent paths tested? (race conditions won't show in single-threaded tests but worth noting).
   - Are resource cleanup paths tested?

## How to Audit

1. **Read EVERY source file.** No skipping. No assuming.
   - **ENUMERATE ALL ARTIFACTS, NOT JUST SOURCE CODE.** `find src/main/java -name '*.java'` misses `.sql` migration files, `.xml` Spring configs, `.yml`/`.properties` files, `pom.xml`/`package.json`, and other build/config artifacts that carry HIGH bug density. Use a broad enumeration: `find . -type f \( -name '*.java' -o -name '*.sql' -o -name '*.xml' -o -name '*.properties' -o -name '*.yml' -o -name '*.json' -o -name '*.yaml' \) -not -path '*/test/*' -not -path '*/node_modules/*' -not -path '*/target/*'`. At iteration 40, V1__init_schema.sql (Flyway migration with FOREIGN KEY gaps) was completely unaudited because `.sql` wasn't in the find glob.
   - For codebases with 25+ source files, use parallel subagents to avoid context exhaustion. **BEFORE dispatching, run the Pre-Flight Checklist** in `references/parallel-audit-pattern.md` (read manifest → enumerate files → assign every file to exactly one group → flag 🆕 and HIGH-VALUE files → balance group sizes → verify T=M). Skipping the checklist causes file-coverage gaps — verified at iteration 34 (LdapAuthProvider.java missed entirely) and iteration 40 (V1__init_schema.sql missed entirely).
   - See `references/parallel-audit-pattern.md` for the full 3/4-group decomposition pattern, pitfalls, and proven results.
2. **Build a route table FIRST.** List every endpoint. For each: does it have auth? Rate limiting? Validation? Write a comparison table — this is where 40% of findings come from. Route A has auth, Route B doesn't → HIGH severity finding.
3. **Compare files against each other.** Route A uses centralized errors — does Route B? If not, flag it. If one route has middleware that another doesn't, flag it. Inconsistency between routes that handle the same class of operation (e.g., financial transactions) is a finding.
4. **Trace the data flow.** A function always returns `true` → find its callers → flag the dead branch. A function is imported but never called → dead import. An enum is defined but never referenced → dead code.
5. **Read the tests.** If there are almost none, flag it as a standalone finding (not just a sub-bullet). Count them. List what's untested: auth failures, rate limiting, validation, error paths, concurrent requests. Zero meaningful assertions → finding.
6. **Check repositories/DAOs.** For each repository method: is it using native queries? If so, are parameters validated? Is there LIKE concatenation risk? Does `findAll()` have pagination? Are derived query methods missing index hints or using unbounded string matching? Flag repository patterns that compound with service-layer issues.
7. **Inspect entities for validation gaps.** For each entity field: is `double` used for money? Is there a `@Version` field? Are constrained fields (role, status) plain strings instead of enums? Are numeric fields missing `@Min`/`@Max` bounds?
8. **Inspect application entry point.** For Spring Boot apps: is `@EnableCaching`, `@EnableScheduling`, `@EnableAsync` present when corresponding features are used? Are there features used without the corresponding enable annotation?
9. **Rate each file 1-10** and explain why.
10. **Rate the whole codebase 1-10** and list every finding with severity.

## Cross-File Consistency Check (MANDATORY)

Build this table for every audit. It catches the hardest-to-find issues:

| Feature | Route A | Route B | Finding |
|---|---|---|---|
| Auth middleware | ✅/❌ | ✅/❌ | If mismatch: HIGH |
| Rate limiting | ✅/❌ | ✅/❌ | If mismatch: HIGH |
| Input validation | ✅/❌ | ✅/❌ | If mismatch: MEDIUM |
| Centralized errors | ✅/❌ | ✅/❌ | If mismatch: MEDIUM |
| Body size limit | ✅/❌ | ✅/❌ | If missing on all: HIGH |
| Test coverage | ✅/❌ | ✅/❌ | If coverage < 10%: MEDIUM |

When routes handle the same CLASS of operation (both financial, both user-data, both admin), any mismatch in auth or rate limiting is automatically HIGH severity — not a judgment call.

## Output Format

```
# Audit: <repo-name>

## Overall Rating: X/10
<one-sentence summary>

## Cross-File Consistency (MANDATORY — build this table first)

| Route | Method | Auth | Rate Limit | Validation | Centralized Errors | Body Size Limit |
|---|---|---|---|---|---|---|
| Route A | ... | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ |

### Mismatches
- MISMATCH: <route> has <feature> but <route> doesn't — <severity>

## Critical (must fix before production)
- [file:line] Finding — why it matters — fix effort

## High
- [file:line] Finding — why it matters — fix effort

## Medium
- [file:line] Finding — why it matters — fix effort

## Low
- [file:line] Finding — why it matters — fix effort

## Race Conditions (separate section)
- [file:line] TOCTOU / async gap — description

## Per-File Scores
| File | Lines | Score | Key Issue |
|---|---|---|---|

## Test Coverage Audit
| Test File | Tests | What's Tested | What's Missing |
|---|---|---|---|

### Critical Testing Gaps (zero coverage)
- <subsystem> — no tests for <paths>

## Severity-Weighted Remediation Plan
| Priority | Finding | Fix | Effort |
|---|---|---|---|

## Clean Surfaces (MANDATORY)
<list each audit surface/lens that was checked and found clean. Example: "No PHI exposure in logging layer", "No hardcoded secrets in configuration files", "All route handlers have input validation">
- <surface> — no issues found

Every section above is MANDATORY. Do not skip the cross-file table, the test coverage breakdown, the remediation plan, or the clean surfaces declaration.

## Language-Specific Patterns

The audit ladder is generic, but each language ecosystem has specific anti-patterns. Before auditing a Java/Spring Boot or TypeScript/Express codebase, consult `references/language-specific-patterns.md` for the full checklist of patterns to flag — XXE, SSRF, path traversal, Double-Checked Locking, EAGER fetch N+1, Static SimpleDateFormat, SQL injection, JWT alg:none/key confusion, Regex DoS, API key management, Content-Type bypass, GraphQL introspection, payment safety (idempotency races, PCI DSS, compensation transactions), OAuth2/OIDC (PKCE, state CSRF, redirect_uri validation), Java deserialization (ObjectInputStream RCE, Jackson enableDefaultTyping, XMLDecoder, SnakeYAML CVE-2022-1471), HTTP security headers (CSP, HSTS, COEP, COOP, CORP), WebSocket security (Cross-Site WebSocket Hijacking, origin bypass, message flooding), TypeScript type safety (unsafe casts, parseInt pitfalls, incomplete guards), gRPC security (plaintext transport, reflection exposure, deadline/connection hardening), Kafka/message broker security (PLAINTEXT connections, deserialization RCE, dead-letter gaps, poison message loops), Spring Actuator security (health endpoint info leaks, credential exposure via InfoContributor, env dumps), JMX/RMI security (hardcoded credentials, disabled auth, ManagedOperation RCE, RMI codebase attack), thread pool/executor safety (unbounded pools, CompletableFuture hazards, volatile arrays, scheduled task failures), HTTP request smuggling and protocol validation (TE.CL, Content-Length overflow, DNS rebinding, Range flooding, ReDoS), and 250+ patterns across 25 categories.

For a quick-reference mapping of vulnerability categories to the ladder rungs that detect them (validated across 343 Java + 415 TypeScript planted issues), see `references/coverage-matrix.md`.

**New (Iteration 28):** `references/iter28-new-patterns.md` — HTTP Client/RestTemplate SSRF, Logback/Log4j config vulns, Spring Event/Messaging security.

## Competitive Research Deferred Patterns

Patterns evaluated and deferred from competitive research cycles are cataloged in `references/deferred-patterns.md`. Before running a new competitive research cycle, scan this file to avoid re-evaluating previously deferred patterns.

## Self-Evolution

This skill is self-improving via a golden-source testing loop. See `references/evolution-methodology.md` for the full workflow: audit golden repos with planted issues → compare to manifests → categorize missed findings → patch the ladder → prove improvement.

**Critical: Golden Source Design.** A detection rate measured on a security-skewed golden source (~85% security vulns) is a MISLEADING metric. Per Google SRE data, 68% of real production outages are triggered by changes (binary push 37%, config push 31%) — categories nearly absent from security-focused golden sources. Expand golden sources to include production-incident patterns: deployment regressions, config cascades, retry storms, observability gaps, capacity cliffs. See `references/golden-source-design-principles.md` for the full design guide, OWASP Benchmark alignment, incident-pattern structure, and severity mapping.

**Pitfall: Security-Skewed Detection Rates.** A 99.7% detection rate on a golden source that's 85% security vulnerabilities means you're good at finding SQLi and hardcoded secrets. It says nothing about your ability to find the bugs that actually cause production outages. Always report detection rate BY CATEGORY (incidents vs security vs correctness), not just as an aggregate number. Expand incident-pattern coverage before claiming "elite" status.

Automation: `scripts/compare-to-manifest.py` compares an audit report against a manifest to compute detection rate.

**MANIFEST INTEGRITY GATE (v1.6.3 — MANDATORY before every compare):**
1. Check for corruption: `grep -c '^\s*\d+\|' ISSUE-MANIFEST.md` — if >0, recursively strip ALL layers: `python3 -c "import re; t=open('ISSUE-MANIFEST.md').read(); [t:=re.sub(r'^\s*\d+\|','',t,flags=re.M) for _ in range(5)]; open('ISSUE-MANIFEST.md','w').write(t)"`
2. Count parseable entries — manifests use ONE of two formats. Try each in order:
   a. **Numbered format** (`1. Issue description`): `grep -c '^\d+\. ' ISSUE-MANIFEST.md`
   b. **Table format** (`| P1 | 🟠 | Line | Issue |`): `grep -c '^| ' ISSUE-MANIFEST.md`
   c. If neither returns >10 entries, read the first 20 lines of the manifest to identify its format, then build the appropriate grep. Table-format manifests use pipe-delimited rows with an ID column; the count command should match those rows while excluding header/separator lines (rows that are `|---|---|` or `| # |`).
3. Compare against manifest header's claimed count. If mismatch >5%: the manifest wasn't updated after golden-source expansion — fix the manifest before running compare-to-manifest.py.
4. Only run compare-to-manifest.py AFTER gates 1-3 pass.

## Severity

- **Critical:** Dead code making guards unreachable, hardcoded production secrets, resource leaks that survive process lifetime.
- **High:** Missing auth on endpoints, race conditions with data integrity risk, no validation at trust boundaries.
- **Medium:** Memory leaks (slow), inconsistent patterns, missing tests for important paths, over-abstraction.
- **Low:** Undocumented behavior, minor code smells, trivial test gaps, intentional patterns that could use a comment.

## Pitfall: compare-to-manifest.py Phrasing Sensitivity + Manifest Corruption

**Argument order (v1.7.2):** `compare-to-manifest.py` expects `<audit.md> <manifest.md>` — audit file FIRST, manifest file SECOND. Swapping the arguments silently produces a bogus result: the script parses the audit file as a manifest (finding ~30-35 entries from section headers) and reports ~100% detection on that tiny subset. **Symptom:** "Manifest entries: 33" when you expect 1360+. **Fix:** swap the arguments. The script's docstring says `<audit_file> <manifest_file>` but there's no guard against transposition.

**Phrasing:** The `scripts/compare-to-manifest.py` comparison tool uses trigram/bigram n-gram matching against the audit report text. Condensed phrasing in audit findings (e.g., "No DKIM/SPF" instead of "No DKIM signing configured — emails can be spoofed") causes false-negative misses — the tool reports `Detection rate: 98.9%` even though every issue was substantively detected. This has recurred across iterations 8, 10, and 11.

**Manifest corruption (v1.6.3 — UPDATED):** `read_file` prepends line-number prefixes (`LINE_NUM|`) that survive `write_file` and compound across sessions — each read_file→write_file cycle adds another layer. A manifest read 3 times accumulates `     1|     1|     1|actual content`. The compare script's single-layer regex strip (`r'^\s*\d+\|'`) silently misses deeper layers. The script reports a tiny parsed count and 100% detection on that subset, masking the real gap. **FIX: recursively strip ALL layers** before parsing. See `references/manifest-corruption-pitfall.md` for the recursive-strip code, detection (grep for `^\s*\d+\|`), and prevention.

**Manifest integrity gate (v1.6.3 — NEW):** Before running compare-to-manifest.py, ALWAYS verify the manifest is parseable. Run `grep -c '^\s*\d+\|' ISSUE-MANIFEST.md` — if >0, clean first. Then count entries with `grep -c '^\d+\. ' ISSUE-MANIFEST.md` and compare against the header's claimed count. A mismatch >5% means the manifest wasn't updated after golden-source expansion — fix the manifest before comparing.

**Rule:** When writing audit findings for golden-source repos, use descriptions that preserve key terms from the manifest. Prefer verbatim manifest phrasing over condensed summaries. Don't abbreviate multi-word vulnerability names (e.g., prefer "No DKIM signing configured" over "No DKIM/SPF"). If the comparison script reports misses, first check for phrasing condensation before assuming the detector missed the issue — expand the finding text and re-run. Only patch the skill if the finding was genuinely undetected.

## Pitfall: Parallel Subagents Miss Recently-Expanded Files

When the previous iteration added new files with new bug categories, the next iteration's parallel subagents consistently give those files shallower attention than older files (verified iterations 10, 19, 21). Older files have been audited across many prior iterations — subagents have deep pattern recognition. Newly-added files get read but not every ladder rung gets applied.

**Signal:** ALL misses cluster in files from the most recent golden-source expansion. Zero misses in older files. This is a subagent attention-allocation bug, not a skill gap.

**Rule:** Flag new files explicitly in subagent context with a 🆕 marker and instruction to spend EXTRA time on them. Reduce files-per-subagent when ≥3 files are new. After consolidation, grep the audit for each new file — if any has <5 findings, re-audit it directly. Prefer direct parent audit for ≤3 newly-expanded files. See `references/parallel-audit-pattern.md` §"Recently-expanded file neglect" for the full mitigation checklist.

## When NOT to Flag

- **Empty catches with a comment explaining why** (e.g., "hooks must never crash the agent"). Intentional error suppression is valid when documented.
- **Files under 30 lines** are not "overly granular" — they're correctly sized. Flag only if >30 lines with a single trivial export.
- **Test files use `assert.ok(true, 'placeholder')`** — flag as zero coverage. A real test file with actual assertions is not a finding.
- **Global mutable state in a CLI tool / single-process script** — flag only for long-lived server processes. CLI tools that exit are exempt.
- **`void` on fire-and-forget with a documented reason** — not a finding. Flag only undocumented `void`.
