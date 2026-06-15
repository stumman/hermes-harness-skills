---
name: security-sentinel
description: >
  Audit and write code against a threat model — injection, authN/authZ,
  secrets, crypto, deserialization, supply chain — flagging vulnerabilities
  by severity with fixes. Use when asked to do a security review, find
  vulnerabilities, threat-model a change, or harden internet-facing code.
---

# Security Sentinel

Assume input is hostile and the attacker is patient. Most vulnerabilities are ordinary code that forgot someone untrusted controls part of the data.

## Procedure

1. Identify trust boundaries: where external/user-controlled data enters. Treat everything crossing a boundary as suspect until validated and, where used in another context, encoded.
2. Walk each finding against the threat lens below.
3. Route observed symptoms to a vulnerability class and CWE via [symptom→CWE routing + expert intuitions](./references/cwe-routing.md) — consult on every audit and whenever a symptom is ambiguous.
4. Report each finding (see Reporting).

## Threat lens

- **Injection.** Parameterize queries (SQL/NoSQL/LDAP); NEVER build commands or queries by string concatenation. Encode output for its sink (HTML, shell, header). Avoid `eval`/dynamic exec on untrusted input.
- **AuthN/AuthZ.** Authenticate, then authorize EVERY sensitive action server-side. Check object-level ownership (the classic IDOR/BOLA gap). NEVER trust client-side checks or hidden fields.
- **Secrets.** NEVER place credentials, tokens, or keys in code, logs, or error messages. Read from config/secret stores. Don't log request bodies or PII.
- **Crypto.** Use vetted libraries and current algorithms; NEVER roll your own. Hash passwords with a slow KDF (argon2/bcrypt/scrypt). Use CSPRNGs for tokens.
- **Deserialization & parsers.** Don't deserialize untrusted data into arbitrary types; disable external entities in XML; bound sizes to resist DoS.
- **Supply chain.** Flag risky/abandoned/over-permissioned dependencies; defer version/lockfile mechanics to `dependency-steward`.

## Reporting

For each finding state: the vulnerability class, how it could be exploited, severity (Critical/High/Medium/Low), and a concrete fix. Prefer fixes that close the class, not just the instance. When in doubt about regulated data, flag it for human/compliance review rather than guessing.
