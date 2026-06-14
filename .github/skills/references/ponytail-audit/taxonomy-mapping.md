# Canonical Taxonomy Mapping

Map ponytail-audit finding categories to industry-standard taxonomies.
Use these IDs when reporting findings for interoperability with security tools.

## CWE Mappings

| ponytail-audit Category | CWE ID | CWE Name |
|---|---|---|
| SQL injection | CWE-89 | SQL Injection |
| Hardcoded secrets/credentials | CWE-798 | Use of Hard-coded Credentials |
| Weak password hashing (SHA-256) | CWE-916 | Use of Password Hash With Insufficient Computational Effort |
| Missing authentication | CWE-306 | Missing Authentication for Critical Function |
| Missing authorization | CWE-862 | Missing Authorization |
| Race condition (TOCTOU) | CWE-367 | Time-of-check Time-of-use Race Condition |
| Timing attack | CWE-208 | Observable Timing Discrepancy |
| Insecure random | CWE-338 | Use of Cryptographically Weak PRNG |
| Path traversal | CWE-22 | Path Traversal |
| XXE | CWE-611 | Improper Restriction of XML External Entity Reference |
| CORS misconfiguration | CWE-942 | Permissive Cross-domain Policy |
| Session fixation | CWE-384 | Session Fixation |
| Insecure cookie | CWE-614 | Sensitive Cookie in HTTPS Session Without 'Secure' Attribute |
| Stack trace exposure | CWE-209 | Generation of Error Message Containing Sensitive Information |
| Log injection | CWE-117 | Improper Output Neutralization for Logs |
| Deserialization of untrusted data | CWE-502 | Deserialization of Untrusted Data |
| Missing CSRF | CWE-352 | Cross-Site Request Forgery |
| JWT alg:none | CWE-327 | Use of a Broken or Risky Cryptographic Algorithm |
| SSRF | CWE-918 | Server-Side Request Forgery |
| Prototype pollution | CWE-1321 | Improperly Controlled Modification of Object Prototype Attributes |
| Regular expression DoS | CWE-1333 | Inefficient Regular Expression Complexity |
| Memory leak (unbounded collection) | CWE-401 | Missing Release of Memory after Effective Lifetime |
| Double for money | CWE-682 | Incorrect Calculation (financial precision) |
| Information disclosure | CWE-200 | Exposure of Sensitive Information to an Unauthorized Actor |
| Missing rate limiting | CWE-770 | Allocation of Resources Without Limits or Throttling |
| N+1 query | CWE-1072 | Data Resource Access without Use of Connection Pooling |
| Missing @Transactional | CWE-664 | Improper Control of a Resource Through its Lifetime |
| Dead code / unreachable guard | CWE-561 | Dead Code |

## OWASP Top 10:2025 Mappings

| ponytail-audit Category | OWASP 2025 |
|---|---|
| SQL injection | A03: Injection |
| Hardcoded secrets | A04: Cryptographic Failures |
| Weak hashing | A04: Cryptographic Failures |
| Missing auth | A01: Broken Access Control |
| Missing authz | A01: Broken Access Control |
| CORS misconfig | A01: Broken Access Control |
| Session fixation | A01: Broken Access Control |
| Insecure cookie | A01: Broken Access Control |
| XXE | A06: Security Misconfiguration |
| Insecure random | A04: Cryptographic Failures |
| Deserialization | A08: Software and Data Integrity Failures |
| Path traversal | A01: Broken Access Control |
| SSRF | A10: SSRF |
| Information disclosure | A06: Security Misconfiguration |
| JWT alg:none | A04: Cryptographic Failures |
| Stack trace exposure | A06: Security Misconfiguration |

## Usage

When reporting a finding, OPTIONALLY include the CWE/OWASP ID in the report:
```
- [file:line] SQL injection (CWE-89, OWASP A03): query string uses ${var} instead of $1 parameter
```

This is OPTIONAL — only include if it adds value. Don't force taxonomy IDs on findings where the mapping is unclear. The precision of the finding matters more than the taxonomy tag.
