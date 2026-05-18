# Configuration Guide

## MemoryManager Parameters

### Core Parameters

| Parameter | Default | Description |
|-----------|:-------:|-------------|
| `workspace` | auto-detect | Workspace directory path |
| `enable_graph` | True | MultiGraphMemory + DualLayer |
| `enable_engram` | True | O(1) n-gram hash index |
| `enable_spreading` | True | Graph expansion |
| `enable_decay` | True | Edge-level exponential decay |
| `enable_ground_truth` | True | Raw conversation storage |
| `enable_compression_spectrum` | True | Tiered compression |
| `enable_query_cache` | True | Search result cache |

### Decay Configuration

| Parameter | Default | Description |
|-----------|:-------:|-------------|
| `decay_config.half_life_temporal` | 7 | Temporal edges (days) |
| `decay_config.half_life_semantic` | 90 | Semantic edges (days) |
| `decay_config.purge_threshold` | 0.05 | Edge removal threshold |

### Spreading Configuration

| Parameter | Default | Description |
|-----------|:-------:|-------------|
| `spreading_max_depth` | 2 | BFS max depth |
| `spreading_decay_factor` | 0.5 | Per-hop decay |
| `spreading_threshold` | 0.1 | Activation cutoff |

### Compression Thresholds

| Parameter | Default | Description |
|-----------|:-------:|-------------|
| `compression_trigger_access` | 5 | Episodes accessed N times → Skill |
| `compression_trigger_apply` | 3 | Skill applied N times → Rule |
| `compression_trigger_verify` | 2 | Rule verified N times → Principle |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CLAW_MEM_SILENT` | Suppress diagnostic output |
| `CLAW_MEM_SEARCH_MODE` | Default search mode |
| `OPENCLAW_WORKSPACE` | Override workspace path |
