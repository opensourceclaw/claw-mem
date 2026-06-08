# claw-mem

<div align="center">

**Intelligent Memory System for AI Agents**

*Make AI Agents Truly Remember*

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Version](https://img.shields.io/badge/Version-6.13.0-blue.svg)](https://github.com/opensourceclaw/claw-mem/releases/tag/v6.13.0)
[![CI](https://github.com/opensourceclaw/claw-mem/actions/workflows/ci.yml/badge.svg)](https://github.com/opensourceclaw/claw-mem/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/opensourceclaw/claw-mem/branch/main/graph/badge.svg)](https://codecov.io/gh/opensourceclaw/claw-mem)

</div>

---

## 🎯 Project Overview

claw-mem is an **intelligent memory system** for AI agents. It enables AI agents to truly remember, learn, and evolve by providing a three-tier storage architecture with intelligent filtering and semantic connections.

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

## 📈 Milestones & Progress

| Version | Date | Theme | Status |
|---------|------|-------|--------|
| **v6.13.0** | 2026-06 | Context Engine Integration | ✅ Current |
| **v6.0.0** | 2026-05 | Three-Tier Storage Complete | ✅ |
| **v5.0.0** | 2026-04 | Concept Graph Foundation | ✅ |
| **v4.0.0** | 2026-03 | Write-Time Gating | ✅ |
| **v3.0.0** | 2026-02 | Basic Memory System | ✅ |

### Upcoming (v7.0.0)

- Cross-agent memory sharing
- Encrypted memory storage
- Enhanced semantic search

---

## 🚀 Installation

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

```bash
# Install via OpenClaw
npx clawhub@latest install opensourceclaw-claw-mem
```

Or manually add to your OpenClaw configuration:

```json
{
  "plugins": {
    "slots": {
      "memory": "claw-mem"
    }
  }
}
```

### Verify Installation

```bash
# Run tests
npm test

# Check version
npm run --silent version
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      claw-mem                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │    STM      │ → │    LTM      │ → │   Archive   │       │
│  │ (Working)   │   │ (Persistent)│   │  (Long-term)│       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
│         ↓               ↓                 ↓                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Memory Manager                          │   │
│  │  - Gating (Write-Time Filtering)                     │   │
│  │  - Retrieval (Semantic Search)                       │   │
│  │  - Graph (Concept Connections)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📖 Usage

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
      "memory": "claw-mem",
      "contextEngine": "claw-mem"
    }
  }
}
```

---

## 🧪 Testing

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific module tests
npm run test:unit
```

---

## 🤝 Contributing

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
- **Discord**: Join our community chat (link in README)

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

## 📄 License

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

## 📞 Support

- **Issue Tracker**: [github.com/opensourceclaw/claw-mem/issues](https://github.com/opensourceclaw/claw-mem/issues)
- **Discussions**: [github.com/opensourceclaw/claw-mem/discussions](https://github.com/opensourceclaw/claw-mem/discussions)


---

<div align="center">

Made with ❤️ by the OpenSourceClaw Community

</div>
