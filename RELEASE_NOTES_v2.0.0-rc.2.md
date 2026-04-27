# Release Notes - claw-mem v2.0.0-rc.2 "The Attention OS"

**Release Date:** 2026-04-05  
**Version:** v2.0.0-rc.2  
**Codename:** Attention OS  

---

## 🎉 What's New

This release introduces the **"Attention OS"**, a revolutionary approach to context management that solves the "Attention Decay" problem in long-term Agent interactions.

### Core Features

- **Pure Markdown Architecture**: No external database dependencies. All memory is stored in human-readable, Git-friendly Markdown files.
- **In-Memory Attention Engine**: High-performance Python Dict-based indexing for sub-millisecond context retrieval.
- **Weighted DAG Topology**: Memory nodes are linked in a Directed Acyclic Graph, allowing the Agent to trace causal chains and understand context lineage.
- **Natural Decay Logic**: A `0.9x` decay factor applied on startup simulates human "forgetting," ensuring the Agent always focuses on what matters most.
- **Crash-Safe Atomic Writes**: All updates use the `tempfile` + `os.replace()` pattern, guaranteeing data integrity even during system failures.

---

## 🏗️ Architecture Highlights

| Component | Description |
| :--- | :--- |
| **AttentionNode** | The fundamental unit of memory, containing `score`, `parents`, and `content_path`. |
| **AttentionIndex** | The in-memory map that powers the Weighted DAG. |
| **Context Assembler** | Dynamically builds the LLM prompt by combining Core Rules with high-attention nodes. |
| **Atomic Writer** | The guardian of data integrity, ensuring every update is safe. |

---

## 📦 Installation

```bash
pip install claw-mem==2.0.0rc2
```

Or from source:

```bash
git clone https://github.com/opensourceclaw/claw-mem.git
cd claw-mem
git checkout v2.0.0-rc.2
pip install -e .
```

---

## 🛡️ Compliance & Quality

- **Dual AI Audit**: Passed rigorous review by JARVIS (Adversary Agent).
- **Regression Testing**: All core functionality tests passed.
- **English-Only**: All release documentation strictly follows the English-only rule.

---

**Full Changelog**: https://github.com/opensourceclaw/claw-mem/compare/v2.0.0-rc.1...v2.0.0-rc.2
