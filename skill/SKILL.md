---
name: claw-mem
description: "Three-Tier Memory System for OpenClaw. Store and recall memories across sessions with Episodic, Semantic, and Procedural layers. BM25 + Heuristic retrieval."
homepage: https://github.com/opensourceclaw/claw-mem
metadata: {"clawdbot":{"emoji":"🧠","requires":{"bins":["python3"],"packages":["claw-mem"]}}}
---

# claw-mem: Three-Tier Memory System

Local-first memory system with three memory layers and intelligent retrieval.

## Prerequisites

```bash
pip install git+https://github.com/opensourceclaw/claw-mem.git
```

## Quick Start

### Search Memory

```bash
python3 {baseDir}/scripts/search.py "project deadlines" --limit 10
```

### Store Memory

```bash
python3 {baseDir}/scripts/store.py "User preference" --category preference
```

### Start Bridge (for OpenClaw integration)

```bash
python3 {baseDir}/scripts/bridge.py --workspace ~/.openclaw/workspace
```

## Memory Layers

| Layer | Purpose | Example |
|-------|---------|---------|
| **Episodic** | Event sequences | Session context |
| **Semantic** | Knowledge facts | User preferences |
| **Procedural** | Rules | Best practices |

## Retrieval Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `keyword` | Simple keyword match | Quick lookup |
| `bm25` | BM25 ranking | Relevance ranking |
| `hybrid` | BM25 + Keyword | Balanced retrieval |
| `enhanced_smart` | Full pipeline | Best quality |

Set mode via environment:
```bash
export CLAW_MEM_SEARCH_MODE=enhanced_smart
```

## Configuration

OpenClaw config (`openclaw.config.json`):
```json
{
  "plugins": {
    "slots": {
      "memory": "claw-mem"
    },
    "claw-mem": {
      "config": {
        "workspaceDir": "~/.openclaw/workspace",
        "autoRecall": true,
        "autoCapture": true,
        "topK": 10
      }
    }
  }
}
```

## Performance

| Operation | Latency |
|-----------|---------|
| Initialize | ~4ms |
| Store | ~8ms |
| Search | ~5ms |
| **Average** | **~6ms** |

## Advanced

See references for detailed documentation:
- [Architecture](references/architecture.md) - Three-tier design
- [Retrieval](references/retrieval.md) - Search algorithms
