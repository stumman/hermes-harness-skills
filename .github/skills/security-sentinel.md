---
name: security-sentinel
version: 1.1.0
description: >
  Write and audit code with a threat model in mind. Applies OWASP-style
  analysis: trust boundaries, injection, authN/authZ, secrets, crypto,
  deserialization, supply chain. v1.1.0 adds symptom-based CWE routing
  table and expert intuitions for patterns base models consistently miss.
  Adopted from yaklang/hack-skills research.
  Flags vulnerabilities by severity with concrete remediations.
  For internet-facing, multi-tenant, or regulated code.
source: combined-harness-ponytail package
license: MIT
---
---

# Security Sentinel

Assume input is hostile and the attacker is patient. Most vulnerabilities are ordinary code that forgot someone untrusted controls part of the data.

## Threat lens (apply to the change)

- **Trust boundaries.** Where does external/user-controlled data enter? Everything crossing the boundary is suspect until validated and, where used in another context, encoded.
- **Injection.** Parameterize queries (SQL/NoSQL/LDAP); never build commands or queries by string concatenation. Encode output for its sink (HTML, shell, header). Avoid `eval`/dynamic exec on untrusted input.
- **AuthN/AuthZ.** Authenticate, then authorize *every* sensitive action server-side. Check object-level ownership (the classic IDOR/BOLA gap). Never trust client-side checks or hidden fields.
- **Secrets.** No credentials, tokens, or keys in code, logs, or error messages. Read from config/secret stores. Don't log request bodies or PII.
- **Crypto.** Use vetted libraries and current algorithms; never roll your own. Hash passwords with a slow KDF (argon2/bcrypt/scrypt). Use CSPRNGs for tokens.
- **Deserialization & parsers.** Don't deserialize untrusted data into arbitrary types; disable external entities in XML; bound sizes to resist DoS.
- **Supply chain.** Flag risky/abandoned/over-permissioned dependencies; defer version/lockfile mechanics to `dependency-steward`.

## Reporting

For each finding: the vulnerability class, how it could be exploited, severity (Critical/High/Medium/Low), and a concrete fix. Prefer fixes that close the class, not just the instance. When in doubt about regulated data, flag it for human/compliance review rather than guessing.

## Symptom-Based CWE Routing (from hack-skills research)

When you observe a symptom in the code, route through this table to identify the correct vulnerability class and CWE:

| Symptom | → Category | → Deep Topic | CWE |
|---|---|---|---|
| Input reflects into HTML/JS without encoding | Injection | XSS | CWE-79 |
| SQL string built with + / format / f-string | Injection | SQLi | CWE-89 |
| User-controlled file path in read/write | File Access | Path Traversal | CWE-22 |
| OS command built with user input | Injection | Command Injection | CWE-78 |
| Serialized object from user/network | Deserialization | Java/Python/PHP RCE | CWE-502 |
| Dynamic template include with user input | Injection | SSTI | CWE-94 |
| URL open with user-controlled destination | Request Forgery | SSRF | CWE-918 |
| XML parse with external entities enabled | Parsing | XXE | CWE-611 |
| User ID in URL without ownership check | AuthZ | IDOR/BOLA | CWE-639 |
| JWT with alg:none or no signature verification | AuthN | JWT Confusion | CWE-347 |
| Crypto with hardcoded IV/key | Crypto | Key Management | CWE-321 |
| `==` on secret/API key comparison | Crypto | Timing Attack | CWE-208 |
| Cookie without HttpOnly/Secure/SameSite | Session | Cookie Security | CWE-614 |
| Redirect to user-controlled URL | Redirect | Open Redirect | CWE-601 |
| Regex without length limit on user input | DoS | ReDoS | CWE-1333 |
| File upload with extension-only validation | Upload | Unrestricted Upload | CWE-434 |
| `eval` / `exec` on untrusted input | Injection | Code Injection | CWE-95 |
| Password in log/error message | Secrets | Sensitive Data Exposure | CWE-532 |
| LDAP query built with string concat | Injection | LDAP Injection | CWE-90 |
| XPath query built with user input | Injection | XPath Injection | CWE-643 |
| HTTP redirect with user in Location header | Injection | HTTP Response Splitting | CWE-113 |
| GraphQL introspection enabled in production | Information | Sensitive Info Exposure | CWE-200 |
| Missing rate limit on login endpoint | Availability | Brute Force | CWE-307 |
| Concurrent request without atomicity guard | Race | TOCTOU | CWE-367 |

## Expert Intuitions — What Base Models Miss (from hack-skills research)

These are patterns that base LLMs consistently fail to detect without specific guidance. Scan EVERY audit for these:

- **Auth bypass via HTTP verb switching:** `GET /admin` is blocked, but `POST /admin` or `HEAD /admin` is not. Always check all HTTP verbs.
- **Parameter pollution:** `?role=user&role=admin` — which value wins? Check how the framework resolves duplicate params.
- **Content-Type negotiation attacks:** Server accepts JSON → attacker sends XML → parser uses different validation path.
- **Normalization bypass:** `/admin` blocked but `/./admin` or `/admin%00` or `/ADMIN` passes.
- **Type juggling:** `"0e123456" == "0e654321"` is true in PHP loose comparison. Check for `==` on hashes.
- **Prototype pollution in JSON merge:** `{"__proto__": {"isAdmin": true}}` merged into config object.
- **ghost-bits in URL parsing:** Malformed URLs that parsers disagree on — one sees `/public`, another sees `/admin`.
- **Null byte injection in filenames:** `avatar.php%00.jpg` — one validator sees `.jpg`, filesystem sees `.php`.
- **Integer overflow in size checks:** `if (len + offset < MAX)` — can overflow to bypass when len is near INT_MAX.
- **Time-of-check-time-of-use (TOCTOU) with symlinks:** Check file is safe → attacker replaces symlink → open different file.
- **Canonicalization gaps:** `new File(baseDir, userPath).getCanonicalPath()` returns the resolved path, but validation happens on the unresolved path first.
- **CORS null origin bypass:** `Access-Control-Allow-Origin: null` with `Access-Control-Allow-Credentials: true` — any sandboxed iframe can now make credentialed requests.
