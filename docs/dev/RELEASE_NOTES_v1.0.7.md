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

- Syntax: `[[memory_id]]` or `[[2026-03-25#investment-decision]]`
- Automatic link parsing
- Backlink detection
- Related memory recommendations

**Example:**
```markdown
# Investment Decision [[2026-03-24#education-fund-planning]]

Reference [[Kati_learning]] [[anxiety-emotion]]
```

---

### 2. Tags System

**Simple tagging:**

- Syntax: `#tag` or `#tag-name`
- Automatic tag extraction
- Tag search
- Tag-based recommendations

**Example:**
```markdown
# Investment Decision

## Content
Worried that investment returns won't be enough for daughter's education.

## Tags
#investment #education-fund #anxiety
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
