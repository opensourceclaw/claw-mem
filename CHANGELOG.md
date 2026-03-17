# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.5.0] - 2026-03-18

### Added
- Three-layer memory architecture (Working/Short-term/Long-term)
- Three memory types (Episodic/Semantic/Procedural)
- Keyword-based retrieval with type filtering
- Write validation for security (rejects unsafe content)
- Checkpoint manager for snapshots
- Audit logger for tracking all memory operations
- Auto-save on session end
- Markdown-based storage compatible with OpenClaw formats

### Security
- Write validation with pattern matching (English + Chinese)
- Audit logging for all memory operations
- Checkpoint creation for rollback support

### Documentation
- README.md with usage examples
- SKILL.md for OpenClaw integration
- CODE_OF_CONDUCT.md (Apache standards)
- CONTRIBUTING.md (Apache standards)
- LICENSE (Apache 2.0)
- NOTICE (attribution)

### Technical
- Pure Python implementation (~900 lines)
- Zero configuration required
- Compatible with existing OpenClaw memory formats
- Apache 2.0 licensed

---

## [Unreleased]

### Planned

- Semantic search with vector embeddings
- Relationship indexing
- Checkpoint rollback feature
- Automatic memory organization
- Cloud sync support
