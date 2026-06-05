# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.5.0] - 2026-06-05

### Added
- **`DriftHistoryStore`**: 漂移历史持久化存储
  - `record(drift)` + `recordBatch(drifts)`: 记录漂移事件
  - `getHistory(sessionId?)` / `getHistoryInRange(start, end)`: 查询
  - `getAverageDrift()` / `getAverageDriftForSession()`: 平均值
  - `getDriftTrend()`: 趋势分析 (increasing/decreasing/stable)
  - `getSummary()`: 综合摘要
  - `isDriftIncreasing()`: 漂移上升判断
  - JSON 文件持久化 + retentionDays 自动清理
- **集成**: 可供 DriftAwareRetriever 使用历史漂移数据

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
