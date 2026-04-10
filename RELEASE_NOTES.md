# claw-mem v2.0.0-rc.3 Release Notes

**Release Date:** April 10, 2026  
**Type:** Release Candidate (RC)  

---

## 🎯 Overview

claw-mem v2.0.0-rc.3 is a release candidate focusing on metadata support, test coverage improvement, and bug fixes. This release brings comprehensive metadata storage and filtering capabilities across all memory layers.

## 📊 Test Coverage

- **Overall Coverage:** 57% (2203/3893 lines)
- **Total Tests:** 269 passed, 0 failed, 3 skipped
- **New Test Modules:** 21 tests added

### Coverage Highlights

| Module | Previous | Current | Change |
|---------|-----------|---------|---------|
| `recovery.py` | 0% | 14% | +14% |
| `context_injection.py` | 15% | 57% | +42% |
| `memory_manager.py` | 13% | 60% | +47% |
| `storage/` modules | 11-15% | 60-74% | +45-63% |

---

## ✨ New Features

### Metadata Support (F110)

- **Complete Metadata Storage**: Custom metadata fields now saved to all storage layers
- **Metadata Filtering**: Search supports metadata-based filtering
- **Flexible Metadata**: Supports arbitrary key-value pairs in metadata
- **Backward Compatible**: Existing memories without metadata work seamlessly

### Storage Layer Enhancements

- **Episodic Storage**: Enhanced metadata support in daily memory files
- **Semantic Storage**: Improved metadata handling in MEMORY.md
- **Procedural Storage**: Metadata support for skill memories

---

## 🐛 Bug Fixes

### Critical Fixes

1. **Metadata Not Saved** (F110-001)
   - **Issue:** Custom metadata fields were not persisted to storage
   - **Fix:** Updated `_format_memory()` in all storage layers to save metadata
   - **Impact:** Users can now store and retrieve custom metadata

2. **Metadata Not Retrieved** (F110-002)
   - **Issue:** Metadata fields not parsed from markdown files
   - **Fix:** Updated `_read_file()` in all storage layers to parse metadata
   - **Impact:** Search with metadata filters now works correctly

3. **Memory.md Initialization Conflict** (F110-003)
   - **Issue:** Format comment in initialization file caused parsing conflicts
   - **Fix:** Removed conflicting comment from `MEMORY.md` initialization
   - **Impact:** Cleaner parsing, no false metadata entries

4. **Count Method Semantics** (F110-004)
   - **Issue:** `count()` returned file count instead of record count
   - **Fix:** Updated `count()` to iterate and count actual memory records
   - **Impact:** Accurate memory statistics

### Test Suite Fixes

5. **Test Failures Fixed**
   - Fixed `test_rule_extractor.py`: Added missing `workspace` parameter
   - Fixed `test_episodic_storage.py`: Corrected `count()` expectation
   - Fixed `test_procedural_storage.py`: Corrected `count()` expectation
   - Fixed `test_errors.py`: Added simple message support to error classes
   - Fixed `test_memory_manager.py`: Enabled previously skipped metadata tests
   - Fixed `test_f6_recovery.py`: Removed return statement causing pytest warning

### Error Handling Improvements

6. **Backward Compatibility** (F110-005)
   - **Issue:** Error classes required specific parameters
   - **Fix:** Added simple message support to `ValidationError` and `ConfigurationError`
   - **Impact:** Easier error creation, better backward compatibility

---

## 📝 Test Improvements

### New Test Modules

1. **test_recovery.py** (7 tests)
   - Diagnosis initialization
   - Recovery result initialization
   - Recovery manager initialization
   - Diagnosis for various error types
   - Recovery strategies (rebuild, checkpoint)
   - Recovery statistics

2. **test_context_injection.py** (14 tests)
   - InjectedContext dataclass
   - ContextFormatter initialization
   - Format with empty memories
   - Format with single/multiple memories
   - Format with/without source
   - Layer-grouped and flat formats
   - Truncation handling

---

## 🔄 Breaking Changes

None. This release candidate is fully backward compatible.

---

## 📋 Migration Notes

No migration required. Existing memory files will continue to work seamlessly.

### For New Users

Custom metadata can be stored using:

```python
memory.store(
    content="User prefers DD/MM/YYYY date format",
    memory_type="semantic",
    metadata={"neo_agent": "Tech", "neo_domain": "Work"}
)
```

### Metadata Filtering

Search with metadata filters:

```python
results = memory.search(
    query="memory",
    metadata={"neo_agent": "Tech"}
)
```

---

## 🔒 Security

- **Audit Logging**: All memory writes are logged
- **Input Validation**: Unsafe content is rejected
- **Permission Checks**: File permissions validated before operations

---

## 📦 Installation

### From Source

```bash
git clone https://github.com/opensourceclaw/claw-mem.git
cd claw-mem
git checkout v2.0.0-rc.3
pip install -e .
```

### From PyPI (when published)

```bash
pip install claw-mem==2.0.0rc3
```

---

## 🔧 Configuration

No new configuration options required. Default settings work out of the box.

---

## 📚 Documentation

- **CHANGELOG**: Full changelog at [CHANGELOG.md](CHANGELOG.md)
- **README**: Usage guide at [README.md](README.md)
- **Architecture**: System architecture at [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🤝 Contributors

This release is the result of successful human-AI collaboration.

### Human Contributors
- Peter Cheng (@petercheng) - Design and implementation

### AI Contributors
- Friday AI - Main Agent for deployment, execution, and coordination
  - Managed release process from v2.0.0-rc.2 to v2.0.0-rc.3
  - Coordinated GitHub Release creation and deployment
  - Validated functionality and benchmark results

- JARVIS AI - Adversary Agent for audit and quality assurance
  - Conducted comprehensive code review and audit
  - Validated release readiness and security
  - Provided quality assurance and risk assessment

### Collaboration Model
This project demonstrates the power of human-AI collaboration:
- Human provides vision, design, and strategic direction
- Friday AI executes deployment and coordinates tasks
- JARVIS AI ensures quality through adversarial review
- Together, they achieve 100% benchmark accuracy and successful release

---

## 📞 Known Issues

1. **Test Coverage**: 57% coverage is acceptable for RC release, targeting 70% for stable release
2. **Performance**: Large memory operations may have latency due to metadata parsing

---

## 🚀 Next Steps

### For RC4

1. Improve test coverage from 57% to 70%
2. Performance optimization for metadata operations
3. Integration testing and validation

### For v2.0.0 Final

1. Address community feedback from RC3
2. Production deployment verification
3. Documentation improvements

---

## 📞 Feedback

Please report any issues or feedback at:
- GitHub Issues: https://github.com/opensourceclaw/claw-mem/issues
- Email: peter@petercheng.dev

---

**Status:** 🟢 Release Candidate Ready for Testing
