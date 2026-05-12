# Security Policy

## Reporting

Report vulnerabilities via [GitHub Security Advisories](https://github.com/opensourceclaw/claw-mem/security/advisories/new).

**Do not file a public issue.**

## Security Architecture

claw-mem operates as a local-first, stdio JSON-RPC memory system with zero network overhead. All data is stored locally in SQLite.

## Supported Versions

| Version | Status |
|---------|--------|
| v2.13.x | ✅ Active |
| v1.x | ⚠️ Maintenance only |

## Memory Security

All memory data is stored locally — no cloud sync, no telemetry. The stdio protocol ensures memory operations never traverse the network.
