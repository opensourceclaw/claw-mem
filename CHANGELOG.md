# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0rc14] - 2026-05-19

### Added

- **CMS Phase 3**: State Machine (`cms/state_machine.py`, `cms/context_switcher.py`, `cms/recovery.py`)
- **MemoryConfig dataclass** for API simplicity — replaces 32-parameter `__init__`
- 46 CMS tests + 46 values/ tests + 6 adapters/ tests (+98 total)

### Changed

- **Field name standardization**: `content` and `memory_type` as canonical; `text`/`type` deprecated aliases
- **Retriever consolidation**: Mode mapping (`bm25→keyword`, `entity→semantic`) with deprecation warnings
- **Workspace-scoped index**: `InMemoryIndex` uses workspace path instead of global `~/.claw-mem/`
- Version badge: `3.0.0rc4` → `3.0.0rc14`

### Deprecated

- `bm25`, `hybrid`, `entity`, `hybrid_entity` search modes → use `keyword` or `semantic`
- 6 retriever imports (bm25_retriever, entity_retriever, heuristic_retriever, etc.)

## [3.0.0rc13] - 2026-05-19

### Fixed

- Workspace-scoped index directory for test isolation
- Singleton cleanup: `get_synonym_expander()` / `get_compressor()` reset after tests

## [3.0.0rc12] - 2026-05-19

### Fixed

- CI failures: import paths, missing watchdog dependency, black formatting
- English migration P0-P2 complete

## [2.18.0] - 2026-05-18

### Added

**CompressionSpectrum Enhancement — Default Enabled + Engram Sync**

- **Default Enabled**: `enable_compression_spectrum=True` by default
  - Users can now use compression without explicit configuration
  - Still configurable: `enable_compression_spectrum=False` to disable

- **Configurable Thresholds**: All compression thresholds are now configurable
  - `compression_trigger_access`: Episode → Skill threshold (default: 5)
  - `compression_trigger_apply`: Skill → Rule threshold (default: 3)
  - `compression_trigger_verify`: Rule → Principle threshold (default: 2)
  - Runtime configuration via `configure_thresholds()`

- **Engram Sync**: Compressed memories are automatically indexed in Engram
  - `CompressionSpectrum._sync_to_engram()` for automatic indexing
  - Skills, Rules, and Principles all indexed after compression
  - Non-blocking sync with graceful error handling

- **Enhanced Stats**: `get_compression_stats()` now includes
  - `enabled`: Current enable state
  - `thresholds`: All threshold values
  - `skills`, `rules`, `principles`: Count of compressed memories

- **Bridge RPC**: Three new RPC methods
  - `get_compression_stats`: Get compression statistics
  - `manual_compress`: Manually trigger compression
  - `configure_compression`: Runtime threshold configuration

### Changed

- `CompressionSpectrum.__init__`: Accepts threshold parameters
- `MemoryManager.__init__`: New parameters for compression thresholds
- `MemoryManager.get_compression_stats()`: Enhanced return value

### Tests

- 40 compression tests (all passing)
  - `test_compression_config.py`: 7 tests for configuration
  - `test_compression_trigger.py`: 8 tests for trigger conditions
  - `test_compression_engram.py`: 7 tests for Engram sync
  - `test_compression_integration.py`: 6 integration tests
  - `test_compression.py`: 12 existing tests (maintained)

## [2.17.0] - 2026-05-18

### Added

**Engram + Spreading Activation — Full Integration**

- **EngramIndex** (`retrieval/engram.py`): O(1) N-gram hash inverted index
  - SHA-256 based n-gram hashing for deterministic indexing
  - Jaccard similarity scoring with frequency weighting
  - Batch indexing support (`index_batch()`)
  - Memory stats and estimation

- **SpreadingActivation** (`retrieval/spreading.py`): Graph-based activation spreading
  - BFS traversal from seed nodes across four-orthogonal subgraphs
  - Configurable decay factor, depth limit, threshold pruning
  - Intent-aware edge type filtering (temporal/causal/semantic/entity)

- **DecoupledRetriever** (`retrieval/decoupled.py`): Unified retrieval pipeline
  - Query → Engram → Spreading → Ranking → Top-K
  - Multi-factor ranking: activation (50%) + freshness (30%) + type weight (20%)
  - Target: search() < 5ms

- **CompressionSpectrum** (`compression/spectrum.py`): Four-tier memory compression
  - Episodes → Skills → Rules → Principles abstraction
  - Trigger-based compression (access/apply/verify counts)
  - Rule-based extraction (no LLM dependency in MVP)
  - Default: disabled (enable_compression_spectrum=False)

### Changed

- **MemoryManager Integration**:
  - `store()`: Auto-index into EngramIndex on successful store
  - `search()`: Prioritizes DecoupledRetriever pipeline over legacy search
  - New parameters: `enable_engram`, `enable_spreading`, `engram_ngram_size`, `spreading_max_depth`
  - New methods: `get_engram_stats()`, `rebuild_engram()`, `get_spreading_stats()`, `get_compression_stats()`

### Tests

- 144 tests (all passing)
  - `test_engram.py`: 18 tests for EngramIndex and EngramHasher
  - `test_spreading.py`: 14 tests for SpreadingActivation and spreading_bfs
  - `test_compression.py`: 12 tests for CompressionSpectrum
  - `test_integration_v215.py`: 13 integration tests
  - Plus existing 87 tests from previous versions

---

## [2.12.5] - 2026-05-10

### Fixed

- **Plugin Registration Fix**: `register` function changed back to synchronous, compatible with OpenClaw plugin API
- **Bridge Initialization Race**: Store `bridge.start()` Promise, hooks await internally to ensure bridge is ready
- **Event Parsing**: Enhanced `extractQueryFromEvent` and `extractFactsFromEvent`
- **Error Handling**: Added ready check and enhanced logging

---

## [2.16.0] - 2026-05-17

### Added

**Session Continuity Fix - Phase 1** — Core fixes for preserving context across session boundaries

- **Content Classifier Module** (`src/claw_mem/classifier.py`): Extracted classification logic into standalone module
  - `classify_content()`: Rule-based classification into decision/preference/task_context/fact/chat
  - `ContentClassification` dataclass with type, importance, should_save, reasoning fields
  - `DETECTION_RULES` dictionary for extensible keyword-based detection
  - English and Chinese (ZH) keyword support for all content types
  - `extract_important_content()`: Extract important items from message lists
  - `generate_session_summary()`: Structured session summarization
  - `detect_content_type()`: Single-content type detection

- **`after_agent_turn` Hook** (TypeScript plugin): Real-time important content capture
  - Captures and stores important content (decisions, preferences) after each agent turn
  - Uses bridge `extract_important_content` for classification
  - Only stores items with importance >= 0.5
  - Async, non-blocking — errors logged gracefully

### Changed

- **bridge.py**: Refactored session continuity handlers to delegate to `classifier` module
  - Removed inline `_DECISION_PATTERNS`, `_PREFERENCE_PATTERNS`, etc. class attributes
  - `_handle_extract_important_content` now calls `extract_important_content()`
  - `_handle_generate_session_summary` now calls `generate_session_summary()`
  - `_handle_detect_content_type` now calls `detect_content_type()`

### Tests

- 48 tests (all passing) in `tests/test_session_continuity.py`
  - Content classifier: decisions, preferences, task context, facts, chat (EN + ZH)
  - `extract_important_content`: multi-type extraction, source tracking, importance scores
  - `generate_session_summary`: overview, decisions, preferences, tasks extraction
  - `detect_content_type`: per-content classification
  - Bridge integration patterns for all three session continuity RPC methods

---

## [2.13.0] - 2026-05-10

### Added

**Critical Rule Memory Type** — Never compress, always inject

- **`critical_rule` Memory Type**: New memory tier stored independently from episodic/semantic/procedural
  - Stored in `~/.claw-mem/critical_rules.json` for cross-workspace persistence
  - Never touched by compression — survives all compaction operations
  - Always prepended to search results (does not count toward limit)
  - Always injected into promptBuilder context with "⚠️ Critical Rules" header
- **New API**: `store_critical_rule()` / `get_critical_rules()` / `delete_critical_rule()` on MemoryManager
- **New Bridge RPC**: `get_critical_rules`, `store_critical_rule`, `delete_critical_rule`
- **Plugin**: `promptBuilder` fetches critical rules on every turn and prepends them to injected context
- **Search**: New `include_critical` parameter on `search()` (default: `True`)

### Tests

- 13 tests (all passing) in `tests/test_critical_rules.py`
- Store, get, delete critical rules
- Critical rules survive compression
- Search always includes critical rules (prepended, not counted toward limit)
- Cross-instance persistence

---

## [2.12.1] - 2026-05-05

### Added

**Auto-Configuration** - One-Click Installation

- **Plugin Auto-Config**: Automatically add plugin configuration to OpenClaw on installation
- **No Manual Setup**: Users can install and use immediately without manual configuration
- **contracts.tools**: Declare plugin tool contracts for OpenClaw 2026.5.4+

---

## [2.3.0] - 2026-04-27

### Added

- **Write-Time Gating** (写时门控)
  - `GatingFilter` - 基于重要性评分决定是否存储
  - `AdaptiveThreshold` - 根据记忆数量动态调整阈值
  - `SalienceScorer` - 多维度显著性评分 (来源声誉40%, 新颖性30%, 可靠性30%)
  - 支持自定义评分函数

- **MemoryManager Integration**:
  - `enable_gating` 参数启用写时门控
  - `gating_threshold` 设置显著性阈值
  - 自动判断存储层级 (active/cold)
  - 冷存储跳过索引以优化性能
  - `get_gating_stats()` 获取门控统计

- **New Module**: `claw_mem.gating`
  - `write_time_gating.py` - 核心门控类
  - `GatingResult`, `GatingFilterResult` - 结果数据结构
  - `InMemoryStorage`, `DiskStorage` - 分层存储
  - `VersionChain` - 版本链管理

### Tests

- 82 tests (all passing)
- Gating 模块覆盖率: ~85%
- 集成测试: 16 tests

### Performance

- 门控过滤延迟: < 10ms
- 自适应阈值延迟: < 1ms
- MemoryManager store 延迟: < 50ms

### Architecture

```
WriteTimeGating
├── SalienceScorer (显著性评分)
│   ├── Source Reputation (40%)
│   ├── Novelty (30%)
│   └── Reliability (30%)
├── GatingFilter (门控过滤器)
├── AdaptiveThreshold (自适应阈值)
└── Storage Tiers
    ├── Active Memory (高显著性)
    └── Cold Storage (低显著性)
```

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

## v2.12.1 (2026-05-07)

- chore: restructure directory layout to devclaw standard
- Move demo files to demos/, bridge.py to scripts/, experiment data to data/
- Create configs/, examples/ directories
