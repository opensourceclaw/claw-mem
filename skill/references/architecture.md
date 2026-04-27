# Three-Tier Memory Architecture

## Overview

claw-mem implements a three-tier memory architecture inspired by human memory:

1. **Episodic Memory** - Event sequences and experiences
2. **Semantic Memory** - Facts and knowledge
3. **Procedural Memory** - Rules and procedures

## Layer Details

### Episodic (L1)
- Stores event sequences
- Time-ordered
- Auto-expires after TTL
- Used for: session context, recent interactions

### Semantic (L2)
- Stores facts and knowledge
- Importance-scored
- Persistent across sessions
- Used for: user preferences, project facts

### Procedural (L3)
- Stores rules and procedures
- Rule extraction from patterns
- Used for: workflows, best practices

## Storage

All layers use SQLite for persistence:
- `episodic.db` - Episodic events
- `semantic.db` - Semantic knowledge
- `procedural.db` - Procedural rules

## Working Memory

In-memory cache for fast access:
- LRU eviction
- TTL-based expiration
- Max 100 items by default
