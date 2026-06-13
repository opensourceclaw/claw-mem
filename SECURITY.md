# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 6.x     | :white_check_mark: |
| 5.x     | :white_check_mark: |
| < 5.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in claw-mem, please report it responsibly.

**Email**: security@claw-mem.dev (or open a private security advisory on GitHub)

**Response Time**: We will acknowledge your report within 72 hours and provide a timeline for resolution.

**Process**:

1. Submit vulnerability details via email or GitHub Security Advisory
2. Our team triages and confirms the issue
3. A fix is developed and tested privately
4. A security release is published with an advisory
5. Public disclosure follows the release

## Security Patch Releases

Security patches are released as patch versions (e.g., v6.19.1) and backported to the latest supported major versions.

## Encryption and Key Management

- claw-mem stores data locally on disk; no network transmission occurs
- Sensitive memory content should be encrypted at the application layer before storage
- Do not store API keys or credentials in memory content without encryption

## Best Practices

- Keep claw-mem updated to the latest patch version
- Use filesystem permissions to restrict access to the workspace directory
- Review memory exports before sharing
