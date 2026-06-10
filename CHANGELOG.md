# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.19.0] - 2026-06-10

### Added
- **`src/emergence/`** — New module for emergent memory detection across federated pool
- **`PatternMiner`**: Frequency analysis, tag correlation (lift), cross-agent pattern discovery
- **`EmergenceDetector`**: Scoring (novelty/utility/consensus), gating (emergent/borderline/noise), detection pipeline
- **`TrendAnalyzer`**: Time-series trend tracking, rising/falling tag detection with linear regression slope

### Tests
- 17/17 emergence tests passing (4 test files)
- EDITH acceptance: Conditional Pass ✅

## [6.18.0] - 2026-06-10

### Added
- **`FederationRegistry`**: Dynamic member management — register/unregister/discover/heartbeat
- **`ConflictResolver`**: 4 conflict resolution strategies — LWW / merge / keep-both / ask-human
- **`PrivacyFilter`**: Privacy-preserving memory sharing — PII redaction + sensitivity scoring (local/shared/public levels)
- **`MemoryPool.search()`**: Keyword search across shared pool with filters (agentId, tags, time range, confidence)
- **`MemoryPool.rankByRelevance()`**: Relevance ranking by query term match count + confidence boost
- **`MemoryPool.getByAgent()` / `getByTags()`**: Targeted queries by agent or tags
- **`CrossAgentSync` version tracking**: Monotonically increasing version per agent, `SyncBatch` return type
- **`CrossAgentSync.detectConflicts()`**: Batch conflict detection against pool
- **`MemoryFederation`**: Rewritten to integrate all components — registry, pool, sync, conflict resolver, privacy filter

### Changed
- `src/memory/federation.ts` — Full rewrite with component integration
- `src/memory/pool.ts` — Added search, rankByRelevance, getByAgent, getByTags
- `src/memory/sync.ts` — Version tracking, SyncBatch return, detectConflicts
- `src/memory/index.ts` — Export new classes and types

### Tests
- 34/34 memory module tests passing (7 test files)
- FederationRegistry: lifecycle + discover + heartbeat
- ConflictResolver: all 4 strategies
- PrivacyFilter: PII redaction + sensitivity scoring
- Integration: end-to-end federation flow

## [6.17.2] - 2026-06-10

### Performance
- **`KeywordRetriever.search()`**: Add n-gram cache to avoid recomputing document n-grams on every search (12.8× faster at 2000 docs)
- **`KeywordRetriever.search()`**: Add BM25 pre-filtering — only compute n-gram Jaccard on top BM25 candidates instead of all documents

### Changed
- **`KeywordRetriever`**: Add `ngramCache` (Map<string, Set<string>>) with dirty flag, rebuilt on index/addDocument/clear

### Performance Results
| Operation | Before | After | Improvement |
|-----------|-------:|------:|:-----------:|
| KeywordRetriever 500 docs | 16.65ms | 2.05ms | 8.1× |
| KeywordRetriever 2000 docs | 51.90ms | 4.05ms | 12.8× |
| KeywordRetriever 5000 docs | — | 4.55ms | < 10ms ✅ |
| InMemoryIndex 5000 docs | — | 0.44ms | < 10ms ✅ |
| BM25 scoring 5000 docs | — | 2.68ms | < 10ms ✅ |
| EpisodicStorage store | — | 0.92ms | < 50ms ✅ |

### Tests
- All 46 benchmark tests passing (7 test files)
- All retrieval tests passing (1 pre-existing failure unrelated)

## [6.17.1] - 2026-06-10

### Fixed
- **`MemoryBenchmarkRunner`**: Fix `isMemoryManager` detection logic — use `fewShotLearn` instead of `delete` to distinguish MemoryManager from RunnerDeps
- **`MemoryBenchmarkRunner`**: Add `buildIndex()` call after corpus pre-population to ensure FTS index reflects new data
- **`MemoryBenchmarkRunner`**: Fix search adapter to use `"episodic"` memory type for better FTS search results

### Changed
- **`MemoryBenchmarkRunner`**: Pre-populate retrieval corpus with matching content for FTS-based retrieval evaluation

### Tests
- All 46 benchmark tests passing (7 test files)
- 732/735 overall tests passing (3 pre-existing failures unrelated to benchmark)

## [6.5.0] - 2026-06-05

### Added
- **`DriftHistoryStore`**: 漂移历史持久化storage
  - `record(drift)` + `recordBatch(drifts)`: 记录漂移事件
  - `getHistory(sessionId?)` / `getHistoryInRange(start, end)`: 查询
  - `getAverageDrift()` / `getAverageDriftForSession()`: 平均值
  - `getDriftTrend()`: 趋势分析 (increasing/decreasing/stable)
  - `getSummary()`: 综合摘要
  - `isDriftIncreasing()`: 漂移上升判断
  - JSON 文件持久化 + retentionDays 自动清理
- **integration**: 可供 DriftAwareRetriever 使用历史漂移数据

## [6.0.2] - 2026-06-05

### Fixed
- Add `start_session` and `end_session` RPC methods to bridge.ts
- Resolved "Failed to start session" warning in logs

## [6.0.1] - 2026-06-05

### Fixed
- Correct build script path for TypeScript compilation
- Add more contracts for robust plugin integration

## [6.0.0] - 2026-06-02

### Changed

- **Context Engine extraction**: Moved Context Engine implementation to standalone plugin claw-ctx v1.0.0
- Plugin `kind` remains `"memory"` only (no longer dual-kind)
- Removed `context_engine.ts` and related tests

### Migration

If using Context Engine, install claw-ctx and configure:

```json
{
  "plugins": {
    "slots": {
      "memory": "claw-mem",
      "contextEngine": "claw-ctx"
    }
  }
}
```

## [5.1.0] - 2026-05-31

### Added

- **Tiered ConstitutionStore** (`src/constitution.ts`) — Three-layer persistent identity store:
  - L0: File-system sources (AGENTS.md, IDENTITY.md, MEMORY.md, TOOLS.md, USER.md)
  - L1: Auto-detected rules via `scanAndSuggest()` (5 regex patterns, no LLM needed)
  - L2: Direct RPC storage via bridge
  - All layers immune to decay and compression
- **Stage 0 session injection**: `MemoryManager.injectConstitution()` runs before any memory retrieval
- **Bridge RPC endpoints**: `get_constitution`, `scan_and_suggest_rule`, `promote_constitution_rule`, `delete_constitution_rule`
- **Legacy migration**: `_migrateCriticalRulesToConstitution()` — one-time upgrade from `critical_rules.json`
- **End-of-session scanning**: Non-fatal scan for new constitution candidates
- **Classifier**: New `constitution` ContentType (importance 1.0, highest priority)
- **Tests**: 8 constitution tests, 209 total, all passing

### Changed

- `MemoryManager` constructor now initializes `ConstitutionStore` and runs migration
- `bridge.ts` handles 4 new RPC methods
- Working memory uses `type: "constitution"` to identify constitution entries
- Python implementation removed (v5.1 is 100% TypeScript)
