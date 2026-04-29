---
name: claw-mem
description: OpenClaw Memory System - Make OpenClaw Truly Remember. Compatible with existing formats, enhanced memory management.
metadata: {"clawdbot":{"emoji":"🧠","requires":{"bins":["python3"]},"primaryEnv":"CLAWMEM_ENABLED"}}
---

# claw-mem - OpenClaw Memory System

**Make OpenClaw Truly Remember.**

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/opensourceclaw/claw-mem/claw-mem.git ~/.openclaw/workspace/skills/claw-mem
cd ~/.openclaw/workspace/skills/claw-mem
pip3 install -e .
```

### Enable

Add to `~/.openclaw/config.json`:

```json
{
  "skills": {
    "claw-mem": {
      "enabled": true
    }
  }
}
```

### Usage

claw-mem automatically integrates into every OpenClaw session:
1. **On Start** - Load relevant memories
2. **During Conversation** - Auto-store and retrieve
3. **On End** - Auto-save memories

No manual configuration required!

---

## 📁 Memory Storage

claw-mem is fully compatible with existing OpenClaw memory formats:

```
~/.openclaw/workspace/
├── MEMORY.md              # Core Memory (Semantic)
└── memory/
    ├── YYYY-MM-DD.md      # Daily Memory (Episodic)
    └── skills/            # Skill Memory (Procedural)
```

---

## 🏗️ Core Features

### 1. Three-Layer Memory Architecture

| Layer | Type | Storage Location | Expiry Policy |
|-------|------|-----------------|---------------|
| **L1** | Working Memory | Current Session | Transfer on End |
| **L2** | Short-term Memory | `memory/YYYY-MM-DD.md` | 30 days |
| **L3** | Long-term Memory | `MEMORY.md` + `skills/` | Permanent |

### 2. Three Memory Types

| Type | Description | Example |
|------|-------------|---------|
| **Episodic** | Daily conversations | "2026-03-17 User asked about Shanghai weather" |
| **Semantic** | Core facts | "User prefers DD/MM/YYYY date format" |
| **Procedural** | Skills/Processes | "Deployment: 1) Test 2) Build 3) Deploy" |

### 3. Hybrid Retrieval

- ✅ Keyword search
- ✅ Type filtering
- ✅ Time-based sorting
- ✅ Semantic search (optional)

### 4. Security Design

- ✅ Write validation (rejects imperative content)
- ✅ Checkpoints (regular snapshots)
- ✅ Audit logging (records modifications)

---

## ⚙️ Configuration (Optional)

claw-mem is zero-config by default, but you can customize:

```json
{
  "claw-mem": {
    "storage": {
      "workspace": "~/.openclaw/workspace",
      "episodic_ttl_days": 30
    },
    "security": {
      "enable_validation": true,
      "enable_checkpoint": true,
      "enable_audit_log": true
    },
    "retrieval": {
      "max_results": 10,
      "enable_semantic_search": false
    }
  }
}
```

---

## 🔧 API

### Python API

```python
from claw_mem import MemoryManager

# Initialize
memory = MemoryManager(workspace="~/.openclaw/workspace")

# Start session
memory.start_session("session_001")

# Store memory
memory.store("User prefers DD/MM/YYYY date format", type="semantic")

# Retrieve memory
results = memory.search("date format", type="semantic")

# End session
memory.end_session()
```

### OpenClaw Skill API

claw-mem automatically injects into OpenClaw sessions:

```yaml
# Automatically available in OpenClaw conversations
System: Loaded 5 relevant memories
User: Did I say anything about dates before?
Agent: Yes, you prefer DD/MM/YYYY date format.
```

---

## 📊 Performance Targets

*MVP version, data to be populated*

| Metric | Target | Current |
|--------|--------|---------|
| Startup Time | <1s | - |
| Memory Footprint | <100MB | - |
| Retrieval Latency | <100ms | - |
| Memory Persistence | 100% | - |

---

## 🤝 Contributing

Community contributions are welcome!

### Development Environment

```bash
git clone https://github.com/opensourceclaw/claw-mem/claw-mem.git
cd claw-mem
pip3 install -e ".[dev]"
pytest
```

### Submit PR

1. Fork the project
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to remote (`git push origin feature/amazing-feature`)
5. Create Pull Request

---

## 📄 License

Apache License 2.0

---

## 🙏 Acknowledgments

- OpenClaw Community
- All Contributors

---

**Make OpenClaw Truly Remember.** 🧠
