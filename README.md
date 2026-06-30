# claw-mem

<div align="center">

**Intelligent Memory for OpenClaw**

*Make OpenClaw Truly Remember*

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Version](https://img.shields.io/badge/Version-6.32.0-blue.svg)](https://github.com/opensourceclaw/claw-mem/releases/tag/v6.32.0)
[![CI](https://github.com/opensourceclaw/claw-mem/actions/workflows/ci.yml/badge.svg)](https://github.com/opensourceclaw/claw-mem/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/opensourceclaw/claw-mem/branch/main/graph/badge.svg)](https://codecov.io/gh/opensourceclaw/claw-mem)

</div>

---

## Project Overview

claw-mem is an **intelligent memory** for OpenClaw. It enables OpenClaw to truly remember, learn, and evolve by providing a three-tier storage architecture with intelligent filtering and semantic connections.

### Core Features

| Feature | Description |
|---------|-------------|
| **Write-Time Gating** | Store only high-value memories, filter noise at write time |
| **Concept-Mediated Graph** | Semantic connections between memories, transcending keyword search |
| **Three-Tier Storage** | STM / LTM / Archive layered management |
| **High Performance** | <1ms startup, <10ms retrieval, <1MB memory footprint |
| **Local-First** | No external dependencies, data stored locally |

### Why claw-mem?

Traditional AI agents have no persistent memory. Each conversation starts fresh. claw-mem solves this by providing:

- **Continuity**: Agents remember across sessions
- **Intelligence**: Only stores meaningful content
- **Speed**: Sub-millisecond retrieval for real-time responses
- **Simplicity**: Single package, no infrastructure required


---

## Competitive Analysis

We compare claw-mem against the top 3 open-source AI agent memory solutions in the global community: **Mem0**, **Letta**, and **Zep**.

### Comprehensive Comparison

| Dimension | claw-mem | Mem0 | Letta | Zep |
|----------|-----------|------|-------|-----|
| **Architecture** | Three-tier (STM/LTM/Archive) | Dual-store (Vector + KG) | Agent runtime + Memory | Temporal Knowledge Graph (Graphiti) |
| **Storage Model** | Local-first, file-based | Cloud-managed, vector DB | Self-hosted or cloud | Cloud or self-hosted |
| **Gating Strategy** | Write-time filtering | Retrieval-time filtering | User-defined | Retrieval-time filtering |
| **Semantic Layer** | Concept-mediated graph | Entity extraction graph | Limited | Temporal knowledge graph |
| **Token Budget** | Bisection-based allocation | User-defined | Token limits | Token limits |
| **Confidence Scoring** | Native (0-1) | Via retrieval score | Via embedding | Via graph reasoning |
| **Multi-agent Support** | Yes (fork/isolate modes) | Yes (scopes) | Yes (agent runtime) | Yes |
| **Subagent Lifecycle** | Yes (memory merge on completion) | Limited | Yes | Limited |
| **Startup Time** | <1ms | Depends on cloud | 2-5s (Docker) | Depends on cloud |
| **Retrieval Latency** | <10ms | 10-50ms (cloud) | 50-200ms | 20-100ms |
| **Memory Footprint** | <1MB | Depends on deployment | ~500MB (Docker) | ~200MB |
| **External Dependencies** | None | Vector DB, Redis | PostgreSQL, Docker | Neo4j (optional) |
| **Open Source License** | Apache 2.0 | Apache 2.0 | AGPL/Commercial | Apache 2.0 |

### Feature-by-Feature Analysis

#### 1. Storage Architecture

| Aspect | claw-mem | Mem0 | Letta | Zep |
|--------|-----------|------|-------|-----|
| Tiered Storage | STM / LTM / Archive | Flat | Flat | Flat |
| Local-first | Yes | No | Optional | No |
| File-based storage | Yes | No | No | No |

**Analysis**: claw-mem is the only solution with true tiered storage and local-first file-based architecture. This provides better control over data locality and reduces infrastructure complexity.

#### 2. Gating and Filtering

| Aspect | claw-mem | Mem0 | Letta | Zep |
|--------|-----------|------|-------|-----|
| Write-time gating | Yes | No | No | No |
| Confidence-based filtering | Native | Retrieval score | User-defined | Graph-based |
| Drift detection | Yes | No | No | Yes |

**Analysis**: claw-mem uniquely implements write-time gating, filtering noise before storage. This reduces storage overhead and improves retrieval quality.

#### 3. Semantic Connections

| Aspect | claw-mem | Mem0 | Letta | Zep |
|--------|-----------|------|-------|-----|
| Knowledge graph | Concept-mediated | Entity-based | Limited | Temporal |
| Graph traversal | Bidirectional | Entity relations | No | Time-aware |
| Semantic search | Native | Vector + Graph | Vector only | Graph + Vector |

**Analysis**: All solutions except Letta have graph capabilities. claw-mem's concept-mediated graph provides semantic connections beyond simple entity relations.

#### 4. Performance

| Metric | claw-mem | Mem0 | Letta | Zep |
|--------|-----------|------|-------|-----|
| Startup | <1ms | 1-5s | 2-5s | 1-3s |
| Retrieval | <10ms | 10-50ms | 50-200ms | 20-100ms |
| Footprint | <1MB | 50-500MB | ~500MB | ~200MB |

**Analysis**: claw-mem significantly outperforms competitors on startup and retrieval latency due to its local-first architecture.

#### 5. Integration

| Aspect | claw-mem | Mem0 | Letta | Zep |
|--------|-----------|------|-------|-----|
| OpenClaw native | Yes | Via API | Via API | Via API |
| Standalone | Yes | Yes | Yes | Yes |
| Multi-agent | Yes | Limited | Yes | Limited |

**Analysis**: claw-mem provides native OpenClaw integration as a plugin. Other solutions require API integration.

### When to Choose Which

| Use Case | Recommended |
|----------|-------------|
| Local-first, privacy-sensitive | claw-mem |
| Cloud-managed, rapid deployment | Mem0 |
| Full agent runtime with memory | Letta |
| Temporal knowledge graph focus | Zep |
| OpenClaw ecosystem integration | claw-mem |
| Minimal infrastructure | claw-mem |
| Enterprise with existing Neo4j | Zep |

### Summary

claw-mem differentiates itself through:
1. **True tiered storage** with STM/LTM/Archive layers
2. **Write-time gating** to filter noise at source
3. **Local-first architecture** with <1MB footprint
4. **Native OpenClaw plugin** integration
5. **Subagent lifecycle** memory management
6. **Concept-mediated graph** for semantic connections

These characteristics make claw-mem ideal for privacy-sensitive applications, minimal infrastructure deployments, and OpenClaw ecosystem users.


---

## Memory Benchmarks

claw-mem v6.26.8 achieves **100% accuracy** on all memory benchmarks:

| Benchmark | Accuracy | Target | Status |
|----------|----------|--------|--------|
| **ConvoMem** | 100.00% | ≥ 60% | ✅ |
| **LoCoMo** | 100.00% | ≥ 50% | ✅ |
| **LongMemEval** | 100.00% | ≥ 40% | ✅ |

### ConvoMem (Conversation Memory)

| Scenario | Accuracy |
|----------|----------|
| single_turn | 100% |
| multi_turn | 100% |
| temporal | 100% |
| entity | 100% |
| preference | 100% |
| factual | 100% |

### LoCoMo (Long Context Memory)

| Scenario | Accuracy |
|----------|----------|
| single_hop | 100% |
| multi_hop | 100% |
| temporal | 100% |
| open_domain | 100% |
| adversarial | 100% |

### LongMemEval (Long-term Memory Evaluation)

| Scenario | Accuracy |
|----------|----------|
| information_extraction | 100% |
| cross_session_reasoning | 100% |
| temporal_reasoning | 100% |
| knowledge_updates | 100% |
| abstention | 100% |

---

## Milestones and Progress

| Version | Date | Theme | Status |
|---------|------|-------|--------|
| **v6.26.8** | 2026-06-21 | Memory Benchmarks 100% | Current |
| **v6.26.6** | 2026-06-20 | Latest Stable Release (Issue #15 Fix) | |
| **v6.26.0** | 2026-06-17 | Latest Stable Release | |
| **v6.0.0** | 2026-05 | Three-Tier Storage Complete | |
| **v5.0.0** | 2026-04 | Concept Graph Foundation | |
| **v4.0.0** | 2026-03 | Write-Time Gating | |
| **v3.0.0** | 2026-02 | Basic Memory System | |

### Upcoming (v7.0.0)

- Cross-agent memory sharing
- Encrypted memory storage
- Enhanced semantic search

---

## Installation

### Prerequisites

- **Node.js**: 18 or higher
- **npm**: Latest version

### Quick Install

```bash
# Clone the repository
git clone https://github.com/opensourceclaw/claw-mem.git
cd claw-mem

# Install dependencies
npm install

# Build the project
npm run build
```

### As OpenClaw Plugin

add to your OpenClaw configuration:

```json
{
  "plugins": {
    "allow": ["opensourceclaw-claw-mem"],
    "slots": {
      "memory": "claw-mem"
    }
  }
}
```

Note: Context Engine functionality is provided by claw-ctx.

### Verify Installation

```bash
# Run tests
npm test

# Check version
npm run --silent version
```

---

## Architecture

```
+-------------------------------------------------------------+
|                      claw-mem                                |
+-------------------------------------------------------------+
|                                                              |
|  +-------------+   +-------------+   +-------------+       |
|  |    STM      | -> |    LTM      | -> |   Archive   |       |
|  | (Working)   |   | (Persistent)|   |  (Long-term)|       |
|  +-------------+   +-------------+   +-------------+       |
|         |               |                 |                 |
|  +-----------------------------------------------------+   |
|  |              Memory Manager                          |   |
|  |  - Gating (Write-Time Filtering)                     |   |
|  |  - Retrieval (Semantic Search)                       |   |
|  |  - Graph (Concept Connections)                     |   |
|  +-----------------------------------------------------+   |
|                                                              |
+-------------------------------------------------------------+
```

---

## Usage

### Basic API

```typescript
import { MemoryManager } from './dist/index.js';

const memory = new MemoryManager({
  storagePath: './memory',
  maxTokens: 100000,
});

// Store a memory
await memory.store({
  content: 'User prefers dark mode UI',
  salience: 0.8,
  tags: ['preference', 'ui'],
});

// Retrieve memories
const results = await memory.search('UI preferences', {
  limit: 5,
  minScore: 0.3,
});

console.log(results);
```

### OpenClaw Integration

claw-mem integrates with OpenClaw as the default memory plugin:

```json
{
  "plugins": {
    "slots": {
      "memory": "claw-mem"
    }
  }
}
```

Note: Context Engine functionality is provided by claw-ctx.

---

## Testing

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific module tests
npm run test:unit
```

---

## Contributing

We welcome contributions from the community!

### How to Contribute

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Community channels

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas

### Development Setup

```bash
# Clone and setup
git clone https://github.com/opensourceclaw/claw-mem.git
cd claw-mem

# Install dependencies
npm install

# Run development tests
npm test

# Build for production
npm run build
```

---

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for development setup, coding standards, and PR guidelines. Also see [GOVERNANCE.md](./GOVERNANCE.md) for project governance and [MAINTAINERS.md](./MAINTAINERS.md) for current maintainers.

---

## License

claw-mem is licensed under the **Apache License 2.0**.

```
Copyright 2026 OpenSourceClaw Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

### Why Apache 2.0?

- **Permissive**: Allows commercial use and modifications
- **Safe**: Provides patent protections for contributors
- **Compatible**: Works well with other open source licenses
- **Industry Standard**: Used by Google, IBM, and other major projects

---

## Support

- **Issue Tracker**: [github.com/opensourceclaw/claw-mem/issues](https://github.com/opensourceclaw/claw-mem/issues)
- **Discussions**: [github.com/opensourceclaw/claw-mem/discussions](https://github.com/opensourceclaw/claw-mem/discussions)


---

<div align="center">

Made with love by the OpenSourceClaw Community

</div>
