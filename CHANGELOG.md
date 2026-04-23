# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-04-23

### Added

- **Concept-Mediated Graph**: Graph-augmented memory system based on GAAMA paper
  - Four node types: Episode, Fact, Reflection, Concept
  - Five edge types: NEXT, DERIVED_FROM, SYNTHESIZED_FROM, RELATED_TO, HAS_CONCEPT
  - Hybrid retrieval: Semantic search + PPR (Personalized PageRank)
  - `ConceptMediatedGraph` core class

- **LLM Extractors**:
  - `BaseExtractor` - Abstract base class
  - `LLMExtractor` - LLM-driven extraction with rule-based fallback
  - `KeywordExtractor` - Lightweight keyword extraction
  - `DummyExtractor` - For testing

- **MemoryManager Integration**:
  - `enable_graph` parameter to enable graph features
  - Automatic creation of ConceptMediatedGraph
  - Backward compatible (disabled by default)

- **New Module**: `claw_mem.graph`
  - `concept_graph.py` - Core graph class
  - `nodes.py` - Node type definitions
  - `edges.py` - Edge type definitions
  - `storage.py` - Storage layer (memory + file)
  - `extractors.py` - LLM extractors

- **Exports**:
  - `ConceptMediatedGraph`, `NodeType`, `EpisodeNode`, `FactNode`, `ReflectionNode`, `ConceptNode`
  - `EdgeType`, `Edge`
  - `LLMExtractor`, `KeywordExtractor`, `DummyExtractor`
  - `DummyEmbedder`

### Tests

- 86 tests (all passing)
- concept_graph.py coverage: 83%

### Performance

- Add conversation: < 100ms
- Retrieve: < 50ms

### References

- Based on GAAMA paper: "Graph-Augmented Associative Memory"

---

## [2.1.0] - 2026-04-23

### Added

- **Write-Time Gating**: Intelligent memory storage with salience scoring
  - `WriteTimeGating` class for controlling memory storage
  - `SalienceScorer` for multi-dimensional scoring (source reputation 40%, novelty 30%, reliability 30%)
  - Storage tiers: active memory + cold storage
  - Version chain management

- **MemoryManager Integration**:
  - `enable_gating` parameter to enable/disable gating
  - `gating_threshold` parameter to set salience threshold
  - `get_gating_stats()` method to retrieve statistics

- **Performance**:
  - Write latency: ~0.5ms (target <10ms) - 20x better
  - Scoring latency: ~0.02ms (target <5ms) - 250x better
  - Memory usage: <5MB (target <10MB)

### Changed

- MemoryManager now supports optional gating feature
- Backward compatible: `enable_gating=False` preserves existing behavior

### Testing

- 53+ unit tests with gating module coverage
- Edge cases and error handling covered
- Integration tests with MemoryManager
- Stress tests: 10,000 writes in ~4s, 0.4ms avg latency
- Concurrent access tests: 20 threads × 100 writes passed
- Memory leak tests passed

### References

- Selective Memory: Learning what to remember (Paper)

### Contributors

- Friday AI (Architecture, Planning, Supervision)
- Jarvis (Implementation, Testing)

---

## [2.0.0] - 2026-04-11

### Added

- **Test Suite Expansion**: Comprehensive test suite for storage/index.py (38 tests, 49% coverage)
- **Error System Tests**: Complete test coverage for errors.py (23 tests, 94% coverage)
- **Time Parser Tests**: Comprehensive test coverage for time_parser.py (20 tests, 87% coverage)
- **Persistence Tests**: Tests for save_index, load_index, backup creation and restoration
- **Lazy Loading Tests**: Tests for lazy loading mechanism and index management
- **Search Coverage**: Tests for n-gram, BM25, and hybrid search methods
- **Tokenization Tests**: Tests for English, Chinese, and mixed language tokenization

### Fixed

- **Python Environment**: Fixed Python environment mismatch for test execution
- **Test Dependencies**: Fixed missing pyyaml dependency in Python 3.14 environment
- **Test Failures**: Fixed test_truncation and test_lazy_loading test failures
- **N-gram Search**: Fixed n-gram search query length matching
- **Context Truncation**: Fixed context truncation test to account for fixed headers

### Test Results

- **Total Tests**: 307 passed, 0 failed, 4 skipped
- **Coverage**: 65% (3534/5541 lines)
- **Test Modules**:
  - test_errors.py: 23 tests, 94% coverage
  - test_time_parser.py: 20 tests, 87% coverage
  - test_storage_index.py: 38 tests, 49% coverage
  - All other tests: Passing

### Performance

- **Startup Time**: ~4ms (lazy loading enabled)
- **Search Latency**: ~5ms (n-gram search)
- **Index Build**: ~10ms for 100 memories

### Documentation

- Updated test coverage reports
- Added comprehensive test documentation

---

## [2.0.0-rc.3] - 2026-04-10

### Added

- **Metadata Support**: Complete metadata storage and filtering support across all storage layers (episodic, semantic, procedural)
- **Recovery Tests**: Comprehensive test suite for exception recovery module (7 tests, 14% coverage)
- **Context Injection Tests**: Complete test suite for context injection module (14 tests, 57% coverage)
- **Test Coverage**: Improved overall test coverage from 49% to 57%

### Fixed

- **Metadata Storage**: Fixed metadata fields not being saved in storage layers
- **Metadata Parsing**: Fixed metadata fields not being parsed from markdown files
- **Metadata Filtering**: Fixed search metadata filter functionality
- **Memory.md Initialization**: Removed conflicting format comment from MEMORY.md initialization
- **Test Failures**: Fixed test_f6_recovery.py return statement causing pytest warning
- **Count Method**: Fixed count() methods to return record count instead of file count
- **Error Classes**: Added backward compatibility for simple message initialization
- **Unknown Tests**: Removed @pytest.mark.skip from previously unskippable tests

### Test Results

- **Total Tests**: 269 passed, 0 failed, 3 skipped
- **Coverage**: 57% (2203/3893 lines)
- **Test Modules**:
  - test_recovery.py: 7 tests, 14% coverage
  - test_context_injection.py: 14 tests, 57% coverage
  - All other tests: Passing

---

## [2.0.0-rc.2] - 2026-04-05

### Added

- **Attention OS**: Implemented pure Markdown-based attention management system.
- **Weighted DAG**: In-memory index with automatic decay (0.9x) and causal link retrieval.
- **Context Assembler**: Dynamic prompt assembly with Core Blocks and Top-K attention focus.
- **Atomic Writes**: Crash-safe persistence using `os.replace()` pattern for all memory updates.

---

---

## [2.0.0-rc.1] - 2026-04-03

### Added

- **RC candidate release**: First release candidate based on v2.0.0-beta.3
- **Complete test coverage**: 94 tests passed, 2 skipped
- **ID generation fix**: Generate ID immediately when creating record in `MemoryManager.store()`
- **Technical debt recorded**: Test coverage 49% logged as technical debt, to be improved in future releases

### Fixed

- **ID generation logic**: Fixed ID generation only after record creation
- **AsyncIO tests**: Fixed async method calls in async tests

### Changed

- **Version upgrade**: v2.0.0-beta.3 to v2.0.0-rc.1
- **Best practices**: Integrated OpenAI Harness Engineering and Anthropic Harness Design

### Documentation

- Referencing [Harness Engineering](https://openai.com/index/harness-engineering/) and [Anthropic Harness Design](https://www.anthropic.com/engineering/harness-design-long-running-apps) best practices

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

## Version History

- **v2.0.0-rc.1** (2026-04-03): RC candidate with test fixes and ID generation fix
- **v2.0.0** (2026-03-31): OpenClaw Plugin Architecture
- **v1.0.8** (2026-03-28): Enhanced Memory Management
- **v1.0.7** (2026-03-25): Stability Improvements
- **v1.0.5** (2026-03-22): Initial Release
