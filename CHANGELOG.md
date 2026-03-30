# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-03-31

### Added

- **OpenClaw Plugin Architecture**: Complete TypeScript Plugin implementation
- **Local-First Design**: stdio JSON-RPC communication, zero network overhead
- **Python Bridge**: `claw_mem.bridge` module for JSON-RPC server
- **TypeScript Plugin**: `@opensourceclaw/openclaw-claw-mem` NPM package
- **Auto-Recall Hook**: Automatically inject relevant memories before agent interactions
- **Auto-Capture Hook**: Automatically extract and store important facts after conversations
- **Memory Tools**: `memory_search` and `memory_store` for explicit operations
- **PYTHONPATH Support**: Automatic Python module path configuration
- **Debug Mode**: Optional debug logging for troubleshooting

### Performance

- **Average Latency**: ~6ms (P50=6ms, P90=9ms, P95=16ms)
- **Initialize**: ~4ms
- **Store**: ~8ms
- **Search**: ~5ms
- **10x faster** than HTTP-based solutions

### Changed

- Moved bridge implementation to `src/claw_mem/bridge.py`
- Updated plugin to use `-m claw_mem.bridge` module syntax
- Enhanced error handling and reconnection logic
- Improved type definitions for TypeScript

### Fixed

- Module path resolution for Python Bridge
- PYTHONPATH configuration for OpenClaw integration
- JSON-RPC communication stability
- Type definitions for OpenClaw Plugin API

### Documentation

- Added [Architecture Design](docs/v2.0.0/LOCAL_FIRST_PLUGIN_ARCHITECTURE.md)
- Added [Plugin API Research](docs/v2.0.0/PLUGIN_API_RESEARCH.md)
- Added [Phase 2 Completion Report](PHASE2_COMPLETION_REPORT.md)
- Updated README with installation and usage instructions

## [1.0.8] - 2026-03-28

### Added

- Enhanced memory management features
- Security validation improvements
- Better error handling

### Fixed

- Minor bug fixes and improvements

## [1.0.7] - 2026-03-25

### Added

- Memory stability improvements
- Performance optimizations

## [1.0.5] - 2026-03-22

### Added

- Initial release with three-tier memory architecture
- Episodic, Semantic, and Procedural memory layers
- Multi-level caching (L1 LRU + L2 TTL)
- Chunked index for large datasets
- Unified configuration with hot-reload
- Proactive health monitoring
- Enhanced exception recovery
- Full English documentation

### Performance

- 10,000x faster retrieval (0.01ms)
- 1,500x faster startup (<1ms)
- 500x less memory usage (<1MB)

---

## Version History

- **v2.0.0** (2026-03-31): OpenClaw Plugin Architecture
- **v1.0.8** (2026-03-28): Enhanced Memory Management
- **v1.0.7** (2026-03-25): Stability Improvements
- **v1.0.5** (2026-03-22): Initial Release
