# claw-mem v1.0.5 Release Notes

**Release Date:** 2026-03-25  
**Version:** 1.0.5  
**Type:** Patch Release (Backward Compatible)

---

## ✨ New Features

### 1. Metadata Support

Added optional `metadata` parameter to `store()` and `search()` methods for NeoClaw integration.

**Example:**
```python
# Store with metadata
memory.store(
    content="Important decision",
    memory_type="semantic",
    metadata={"neo_agent": "Tech", "neo_domain": "Work"}
)

# Search with metadata filtering
results = memory.search(
    query="decision",
    metadata={"neo_agent": "Tech"}
)
```

### 2. Backward Compatibility

- ✅ 100% backward compatible with v1.0.4
- ✅ No breaking changes
- ✅ Existing code works without modification
- ✅ Metadata parameter is optional

---

## 🔧 Technical Details

### API Changes

**store() method:**
```python
# v1.0.4 (still works)
memory.store(content, memory_type="episodic")

# v1.0.5 (new optional parameter)
memory.store(content, memory_type="episodic", metadata={})
```

**search() method:**
```python
# v1.0.4 (still works)
results = memory.search(query)

# v1.0.5 (new optional parameter)
results = memory.search(query, metadata={})
```

### Technology Layer Independence

- claw-mem remains **business-agnostic**
- Technology layer doesn't interpret metadata meaning
- Metadata is stored as JSON and filtered mechanically
- Business logic is in NeoClaw service layer

---

## 📦 Installation

```bash
pip install claw-mem==1.0.5
```

Or upgrade:
```bash
pip install --upgrade claw-mem
```

---

## 🧪 Testing

Test coverage: **91%**

```bash
# Run tests
pytest tests/ -v

# Coverage report
pytest tests/ --cov=claw_mem --cov-report=html
```

---

## 📚 Documentation

- README.md: Updated with metadata examples
- API docs: Updated with new parameters
- Migration guide: No migration needed

---

## 🙏 Acknowledgments

**Core Development:**
- Peter Cheng - Architecture Design
- Friday AI - Implementation

**Integration:**
- NeoClaw v0.6.0 team

---

## 📝 License

Apache License 2.0

---

**Full Changelog:** https://github.com/opensourceclaw/claw-mem/compare/v1.0.4...v1.0.5
