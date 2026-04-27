# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

claw-mem is a **Local-First Three-Tier Memory System** for OpenClaw. It provides persistent memory for AI assistants with extremely low latency (<10ms average).

## Key Commands

```bash
# Python tests
pytest tests/

# Build TypeScript plugin
cd claw_mem_plugin
npm install
npm run build

# Plugin integration tests
cd claw_mem_plugin
npm test
```

## Architecture

```
OpenClaw Plugin (TypeScript)
        ↓ spawn + stdio JSON-RPC
claw-mem Python Bridge
        ↓ Python Function Call
claw-mem Core (MemoryManager, Three-Tier Retrieval, SQLite)
```

## Three-Tier Memory

- **Episodic Memory**: Conversation history, event sequences
- **Semantic Memory**: Extracted facts, concepts
- **Procedural Memory**: Skills, workflows, operation steps

## Configuration

Key settings in OpenClaw:
- `autoRecall`: Auto-inject memories before interaction
- `autoCapture`: Auto-store important facts after conversations
- `topK`: Max memories to recall (default: 10)
- `attentionEngine`: Weighted DAG for memory prioritization

## Performance

- Initialize: ~4ms
- Store: ~8ms
- Search: ~5ms
- Average: ~6ms

## Important Notes

- Local-first design: Zero network overhead, stdio JSON-RPC
- Full CJK (Chinese/Japanese/Korean) text support
- Integrates with OpenClaw via plugin architecture
