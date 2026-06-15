# Symptom-Based CWE Routing

When you observe a symptom in the code, route through this table to identify the vulnerability class and CWE.

| Symptom | Category | Deep Topic | CWE |
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

## Expert Intuitions — patterns base models consistently miss

Scan every audit for these:

- **Auth bypass via HTTP verb switching:** `GET /admin` is blocked, but `POST /admin` or `HEAD /admin` is not. Check all HTTP verbs.
- **Parameter pollution:** `?role=user&role=admin` — which value wins? Check how the framework resolves duplicate params.
- **Content-Type negotiation attacks:** server accepts JSON, attacker sends XML, parser uses a different validation path.
- **Normalization bypass:** `/admin` blocked but `/./admin` or `/admin%00` or `/ADMIN` passes.
- **Type juggling:** `"0e123456" == "0e654321"` is true in PHP loose comparison. Check for `==` on hashes.
- **Prototype pollution in JSON merge:** `{"__proto__": {"isAdmin": true}}` merged into a config object.
- **Ghost-bits in URL parsing:** malformed URLs that parsers disagree on — one sees `/public`, another `/admin`.
- **Null byte injection in filenames:** `avatar.php%00.jpg` — one validator sees `.jpg`, the filesystem sees `.php`.
- **Integer overflow in size checks:** `if (len + offset < MAX)` can overflow to bypass when len is near INT_MAX.
- **TOCTOU with symlinks:** check file is safe, attacker replaces symlink, open opens a different file.
- **Canonicalization gaps:** `getCanonicalPath()` returns the resolved path, but validation ran on the unresolved path first.
- **CORS null origin bypass:** `Access-Control-Allow-Origin: null` with `Allow-Credentials: true` lets any sandboxed iframe make credentialed requests.
