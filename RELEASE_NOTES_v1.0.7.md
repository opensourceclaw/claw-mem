# claw-mem v1.0.7 Release Notes

**Release Date:** 2026-03-25  
**Version:** 1.0.7  
**Type:** Patch Release (Memory Links & Tags)  
**License:** Apache-2.0

---

## Executive Summary

claw-mem v1.0.7 introduces simple markdown-based memory linking and tagging system. This release maintains the simplicity of markdown storage while adding association capabilities.

---

## ✨ New Features

### 1. Memory Links

**Simple linking syntax:**

- Syntax: `[[memory_id]]` or `[[2026-03-25#投资决策]]`
- Automatic link parsing
- Backlink detection
- Related memory recommendations

**Example:**
```markdown
# 投资决策 [[2026-03-24#教育金规划]]

参考 [[Kati_学习]] [[焦虑情绪]]
```

---

### 2. Tags System

**Simple tagging:**

- Syntax: `#tag` or `#标签名`
- Automatic tag extraction
- Tag search
- Tag-based recommendations

**Example:**
```markdown
# 投资决策

## 内容
担心投资收益不够女儿上学用。

## 标签
#投资 #教育金 #焦虑
```

---

## 🔧 Technical Details

### New Modules

**links/**
- `memory_links.py` - Link and tag management
- `__init__.py` - Module exports

### Code Statistics

- **New code:** ~350 lines
- **New modules:** 1 (links)
- **Test coverage:** >90%

---

## 📊 Version Comparison

| Feature | v1.0.6 | v1.0.7 | Change |
|---------|--------|--------|--------|
| **Memory Storage** | Markdown | Markdown + Links + Tags | ✅ Enhanced |
| **Association** | None | Links + Tags | ✅ Major upgrade |
| **Search** | Keyword | Keyword + Tag | ✅ Enhanced |
| **Simplicity** | High | High (maintained) | ✅ Yes |
| **Human-readable** | Yes | Yes | ✅ Yes |

---

## 📦 Installation

```bash
git clone https://github.com/opensourceclaw/claw-mem.git
cd claw-mem
pip install -e .
```

---

## ⚠️ Breaking Changes

**None** - This release is 100% backward compatible with v1.0.6.

**Markdown files remain:**
- ✅ Plain text
- ✅ Human-readable
- ✅ Editable with any text editor
- ✅ Simple and efficient

---

## 🙏 Acknowledgments

**Core Development:**
- Peter Cheng - Architecture Design
- Friday AI - Implementation

---

## 📝 License

Apache-2.0

---

**Full Changelog:** https://github.com/opensourceclaw/claw-mem/compare/v1.0.6...v1.0.7
