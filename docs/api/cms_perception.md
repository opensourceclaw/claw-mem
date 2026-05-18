# CMS Perception Layer API

**Version**: v3.0.0-rc.1

## Overview

The CMS Perception Layer provides real-time memory capacity monitoring,
automatic context warnings, and importance-based memory prioritization.

**Default: disabled** (`enable_cms=False`).

## CapacityMonitor

```python
from claw_mem.cms import CapacityMonitor

monitor = CapacityMonitor(
    memory_manager=mm,
    token_threshold=8000,
    memory_threshold=1000,
    warning_level=0.8,
)
stats = monitor.get_stats()     # CapacityStats snapshot
trend = monitor.get_trend()     # CapacityTrend analysis
should = monitor.should_warn()  # Bool: should emit warning?
```

### CapacityStats

| Field | Type | Description |
|-------|------|-------------|
| `total_memories` | int | Total memory count |
| `total_tokens` | int | Estimated token count |
| `by_type` | dict | Per-type breakdown |
| `utilization` | float | 0.0-1.0 ratio |
| `threshold` | int | Configured limit |

### CapacityTrend

| Field | Type | Description |
|-------|------|-------------|
| `samples` | list | Recent CapacityStats snapshots |
| `growth_rate` | float | Growth rate (memories/operation) |
| `estimated_time_to_full` | float | Seconds until threshold |

## ContextWarningHook

```python
from claw_mem.cms import ContextWarningHook

hook = ContextWarningHook(
    capacity_monitor=monitor,
    cooldown_seconds=300,
)
event = hook.check_and_emit()    # Optional[WarningEvent]
hook.on_memory_stored("mem_id")  # Hook after store()
```

### WarningEvent

| Field | Type | Description |
|-------|------|-------------|
| `severity` | str | "info" / "warning" / "critical" |
| `message` | str | Human-readable warning |
| `utilization` | float | Current utilization |
| `threshold` | float | Warning threshold |
| `total_memories` | int | Memory count |

## ImportanceEvaluator

```python
from claw_mem.cms import ImportanceEvaluator

evaluator = ImportanceEvaluator(memory_manager=mm)

score = evaluator.evaluate("mem_id")  # Single memory
scores = evaluator.evaluate_batch(["a", "b"])  # Batch
important = evaluator.get_important_memories(threshold=0.5, limit=50)

evaluator.record_access("mem_id")  # Track access count
```

### ImportanceScore

| Field | Type | Description |
|-------|------|-------------|
| `memory_id` | str | Memory identifier |
| `base_score` | float | Type-based score (0.2-1.0) |
| `access_boost` | float | Access frequency boost (0-0.3) |
| `recency_boost` | float | Recency boost (0-0.2) |
| `total_score` | float | Combined score (0-1.5) |
| `content_type` | str | Detected type |

### Scoring Formula

```
total = base(content_type) + access_boost + recency_boost

base:        critical=1.0, preference=0.8, decision=0.7,
             fact=0.5, task=0.4, chat=0.2
access:      +0.1 per 5 accesses, capped at 0.3
recency:     0.2 * (1 - age_days/30), capped at 0.2
```

## MemoryManager Integration

```python
mm = MemoryManager(
    enable_cms=True,
    cms_token_threshold=8000,
    cms_memory_threshold=1000,
    cms_warning_level=0.8,
)

stats = mm.get_capacity_stats()
scores = mm.get_importance_scores(["mem_1", "mem_2"])
important = mm.get_important_memories(threshold=0.5, limit=20)
```

## Bridge RPC

| Method | Params | Returns |
|--------|--------|---------|
| `get_capacity_stats` | None | CapacityStats dict |
| `get_importance_scores` | `memory_ids: List[str]` | `{id: ImportanceScore dict}` |
| `get_important_memories` | `threshold: float, limit: int` | `[ImportanceScore dict]` |
