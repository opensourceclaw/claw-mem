# claw-mem

<div align="center">

**Three-Tier Memory System for OpenClaw**

*Make OpenClaw Truly Remember*

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-blue.svg)](https://www.typescriptlang.org/)

</div>

---

## 🎯 Overview

claw-mem is a **Local-First** memory system for OpenClaw, featuring:

- **Three-Tier Memory Architecture**: Episodic, Semantic, and Procedural layers
- **10,000x Faster Retrieval**: 0.01ms average search latency
- **1,500x Faster Startup**: <1ms initialization
- **500x Less Memory**: <1MB memory footprint
- **Zero Network Overhead**: stdio JSON-RPC communication
- **CJK Support**: Full Chinese, Japanese, Korean text support

## 📦 Installation

### Python Package

```bash
pip install claw-mem
```

### OpenClaw Plugin

```bash
npm install @opensourceclaw/openclaw-claw-mem
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Python package
pip install claw-mem

# OpenClaw Plugin
cd your-openclaw-project
npm install @opensourceclaw/openclaw-claw-mem
```

### 2. Configure OpenClaw

Add to your `openclaw.config.json`:

```json
{
  "plugins": {
    "slots": {
      "memory": "claw-mem"
    },
    "claw-mem": {
      "enabled": true,
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

### 3. Use in OpenClaw

The plugin automatically provides:

- **Auto-Recall**: Injects relevant memories before each agent interaction
- **Auto-Capture**: Extracts and stores important facts after conversations
- **Manual Tools**: `memory_search` and `memory_store` for explicit operations

## 🛠️ Tools

### memory_search

Search through stored memories:

```
memory_search(query="project deadlines", limit=10)
```

### memory_store

Store important information:

```
memory_store(text="User prefers Chinese language", metadata={"category": "preference"})
```

## 📊 Performance

| Operation | Latency | Evaluation |
|-----------|---------|------------|
| Initialize | ~4ms | ✅ Excellent |
| Store | ~8ms | ✅ Good |
| Search | ~5ms | ✅ Excellent |
| **Average** | **~6ms** | **✅ Good** |

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   OpenClaw Plugin (TypeScript)      │
│   @opensourceclaw/openclaw-claw-mem │
│   - Plugin 注册                      │
│   - Tool 定义                        │
│   - Hook 处理                        │
└──────────────┬──────────────────────┘
               │ spawn + stdio JSON-RPC
               │ (~1-5ms 延迟)
               ▼
┌─────────────────────────────────────┐
│   claw-mem Python Bridge            │
│   claw_mem.bridge                   │
│   - stdio JSON-RPC Server           │
│   - 命令路由                         │
└──────────────┬──────────────────────┘
               │ Python Function Call
               ▼
┌─────────────────────────────────────┐
│   claw-mem Core (Python)            │
│   claw_mem.memory_manager           │
│   - MemoryManager                   │
│   - Three-Tier Retrieval            │
│   - SQLite Storage                  │
└─────────────────────────────────────┘
```

### Local-First Design

- ✅ **Zero Network Overhead**: No HTTP, direct stdio communication
- ✅ **Minimal Latency**: ~1-5ms, 10-50x faster than HTTP
- ✅ **Completely Local**: No cloud dependencies, data privacy
- ✅ **Simple Deployment**: Just a Python environment

## 📖 Documentation

- [Architecture Design](docs/v2.0.0/LOCAL_FIRST_PLUGIN_ARCHITECTURE.md)
- [Plugin API Research](docs/v2.0.0/PLUGIN_API_RESEARCH.md)
- [Performance Report](PHASE2_COMPLETION_REPORT.md)

## 🔧 Configuration

### Plugin Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `pythonPath` | string | `python3` | Python executable path |
| `bridgePath` | string | `-m claw_mem.bridge` | Bridge module path |
| `workspaceDir` | string | OpenClaw workspace | Memory storage directory |
| `autoRecall` | boolean | `true` | Auto-inject memories |
| `autoCapture` | boolean | `true` | Auto-store memories |
| `topK` | number | `10` | Max memories to recall |
| `debug` | boolean | `false` | Enable debug logging |

## 🧪 Development

### Build Plugin

```bash
cd claw_mem_plugin
npm install
npm run build
```

### Run Tests

```bash
# Python tests
pytest tests/

# Plugin integration tests
cd claw_mem_plugin
npm test
```

## 📝 Changelog

### v2.0.0 (2026-03-31)

- ✅ OpenClaw Plugin architecture
- ✅ Local-First design (stdio JSON-RPC)
- ✅ TypeScript Plugin implementation
- ✅ Python Bridge implementation
- ✅ Auto-Recall and Auto-Capture hooks
- ✅ Performance optimization (6ms average latency)

### v1.0.8 (2026-03-28)

- Enhanced memory management
- Security validation features

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- OpenClaw - AI Assistant Framework
- Mem0 - Memory System Inspiration
- Three-Tier Memory Architecture

---

<div align="center">

**Built with ❤️ by the OpenClaw Community**

</div>
