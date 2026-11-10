# Security Policy

At **Búho Zurdo**, we take the security and integrity of our open-source software seriously. Because `jsonmask` is specifically designed for sanitizing sensitive data (PII, credentials, access tokens) across applications, telemetry pipelines, and logs, we prioritize rapid investigation and remediation of security reports.

---

## Supported Versions

Only the latest active minor release receives security updates and patches:

| Version | Supported          | Status               |
| :------ | :----------------: | :------------------- |
| `0.3.x` | :white_check_mark: | Current Active Major |
| `0.2.x` | :x:                | End of Life (EOL)    |
| `< 0.2` | :x:                | End of Life (EOL)    |

We recommend upgrading to the latest published release on PyPI:

```bash
pip install --upgrade buhozurdo-jsonmask
```

---

## Reporting a Vulnerability

> [!CAUTION]
> **Please do not report security vulnerabilities through public GitHub issues, pull requests, or public discussions.**

### 1. Primary Method: GitHub Security Advisories (Preferred)

We use GitHub's private vulnerability reporting system. Please submit reports through the advisory portal:

👉 **[Submit a Security Advisory on GitHub](https://github.com/buhozurdo/jsonmask/security/advisories/new)**

This opens a confidential workspace where we can collaborate with you to triage, reproduce, and fix the issue before public disclosure.

### 2. Alternative Method: Direct Security Email

If you cannot submit via GitHub, you may email our security team directly:

- **Email:** [security@buhozurdo.com](mailto:security@buhozurdo.com)
- **Fallback:** [dev@buhozurdo.com](mailto:dev@buhozurdo.com)
- **Subject line:** `[SECURITY] jsonmask: <Short Description>`

---

## What to Include in Your Report

To help us triage and reproduce the issue quickly, please include:

1. **Description:** Clear explanation of the potential vulnerability (e.g. data leakage, ReDoS in regex engine, unhandled path traversal, hash collision/leak).
2. **Affected Components:** Affected classes or methods (`Masker`, `PathMatcher`, `HashStrategy`, `RegexStrategy`, CLI, etc.).
3. **Proof of Concept (PoC):** Minimal Python code snippet, JSON payload, or terminal reproduction steps demonstrating the issue.
4. **Impact Assessment:** The worst-case scenario and expected privileges or environment required to exploit the issue.
5. **Proposed Fix (Optional):** If you have an idea or patch for the fix, please include it in your report.

---

## Response Timeline & Disclosure Policy

When a security report is received:

- **Initial Acknowledgement:** Within **48 hours**, confirming receipt and assigning a security coordinator.
- **Triage & Validation:** Within **5 business days**, providing validation of the vulnerability and CVSS severity assessment.
- **Remediation & Patching:** Developed and tested within a private security advisory repository.
- **Coordinated Disclosure:** A CVE identifier (if eligible) and a GitHub Security Advisory will be published simultaneously with a patched release on PyPI. Reporters will be credited in the release notes and advisory (unless anonymity is requested).

---

## Best Practices for Secure Deployment

When using `jsonmask` in production systems:

1. **Use Strong Cryptographic Salts:** When using `HashStrategy` or pseudonymization rules, always configure a secure, high-entropy salt via the `JSONMASK_SALT` environment variable or the rule's `salt` option. This prevents rainbow table correlation across log streams.
2. **Audit Custom Regular Expressions:** When using `RegexStrategy` or custom regexes, ensure patterns avoid nested quantifiers that could be vulnerable to Regular Expression Denial of Service (ReDoS).
3. **Strict Order in Logging Pipelines:** Ensure `jsonmask` filters or handlers are attached as early as possible in your logging pipeline so raw records are masked before serialization or disk write.
4. **Keep Dependencies Updated:** Enable Dependabot or automated dependency scanning to receive timely updates.
