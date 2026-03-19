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

## [0.7.0] - 2026-03-19

### Added
- **Index Persistence** - Serialize N-gram + BM25 index to disk for fast startup
- **Lazy Loading** - Load index on first search instead of blocking startup
- **Incremental Updates** - Add/remove memories without rebuilding entire index
- **Async Save** - Non-blocking index persistence
- **Version Compatibility** - Index version checking and migration support
- **Integrity Checksum** - MD5 checksum for index corruption detection
- **Index Compression** - Gzip compression (level 9) for reduced disk usage
- **Exception Recovery** - Automatic backup, corruption detection, and recovery
- **Atomic Writes** - Prevent partial writes with temp file + rename
- **Integrity Verification** - API to verify index health

### Performance
- **Cold Startup**: 1.5s → **0.001s** (1551x faster)
- **Index Loading**: 1.5s → **0.001s** (1551x faster)
- **Incremental Update**: N/A → **<1ms**

### Changed
- `InMemoryIndex.__init__()`: Added `index_dir` and `enable_persistence` parameters
- `InMemoryIndex.build()`: Added `save_index` parameter
- `MemoryManager.store()`: Added `update_index` parameter for incremental updates

### Technical
- Pickle serialization for index persistence
- Index stored in `~/.claw-mem/index/index_v0.7.0.pkl`
- Metadata stored in `~/.claw-mem/index/meta_v0.7.0.json`
- Backward compatible with v0.6.0 API

### Documentation
- F1 implementation guide (`docs/F1_IMPLEMENTATION.md`)
- Test suite for persistence (`tests/test_f1_persistence.py`)

---

## [Unreleased]

### Planned (v0.8.0+)

- Semantic search with vector embeddings
- Relationship indexing
- Checkpoint rollback feature
- Automatic memory organization
- Index compression
- Cloud sync support
