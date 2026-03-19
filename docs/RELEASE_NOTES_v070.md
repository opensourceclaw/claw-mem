# claw-mem v0.7.0 - Persistent Memory

**Release Date**: March 19, 2026  
**Version**: v0.7.0  
**License**: Apache-2.0

---

## Overview

claw-mem v0.7.0 introduces persistent memory with 191x faster startup time. This release focuses on performance optimization, reliability, and user experience improvements.

## Key Features

### 1. Index Persistence

Serialize N-gram + BM25 index to disk for instant startup. No more rebuilding index on every restart.

**Performance**: Startup time reduced from 1.5s to **7.47ms** (191x faster)

### 2. Lazy Loading

Load index on first search instead of blocking startup. Applications feel instant.

**Performance**: Initialization time **0.133ms**

### 3. Incremental Updates

Add or remove memories without rebuilding the entire index. Perfect for real-time applications.

**Performance**: **14.16ms** per memory addition

### 4. Index Compression

Gzip compression (level 9) reduces disk usage by 82.5% without performance penalty.

**Performance**: Compression ratio **17.5%** (82.5% space saved)

### 5. Exception Recovery

Automatic backup before save, atomic writes, corruption detection, and automatic recovery from backup.

**Performance**: Recovery time **12.06ms**

### 6. Integrity Verification

New `verify_integrity()` API to check index health and detect corruption.

## Performance Comparison

| Metric | v0.6.0 | v0.7.0 | Improvement |
|--------|--------|--------|-------------|
| Startup Time | ~1.5s | **7.47ms** | **191x** 🚀 |
| Initialization | N/A | **0.133ms** | New |
| Incremental Add | ❌ | **14.16ms** | New |
| Index Size | N/A | **11.29 KB** | -82.5% 💾 |
| Compression | 0% | **17.5%** | New |
| Recovery | ❌ | **12.06ms** | New |

## Installation

```bash
pip install --upgrade claw-mem
```

### Requirements

- Python 3.8+
- jieba (optional, for Chinese tokenization)
- rank-bm25 (optional, for BM25 search)

## Usage

### Basic Usage

```python
from claw_mem import MemoryManager

# Initialize memory manager
mm = MemoryManager(workspace="~/.openclaw/workspace")

# Start session (automatically loads persisted index)
mm.start_session("my_session")

# Store memory
mm.store("User prefers concise answers", memory_type="episodic")

# Search memories
results = mm.search("user preferences", limit=5)

# End session
mm.end_session()
```

### Advanced Configuration

```python
from claw_mem import MemoryManager

mm = MemoryManager(
    workspace="~/.openclaw/workspace",
    enable_persistence=True,  # Enable index persistence (default: True)
    index_dir="~/.claw-mem/index",  # Custom index directory
)
```

### Integrity Check

```python
from claw_mem import MemoryManager

mm = MemoryManager()
is_valid, issues = mm.index.verify_integrity()

if not is_valid:
    print(f"Index issues: {issues}")
```

## Technical Details

### Index File Format

```
~/.claw-mem/index/
├── index_v0.7.0.pkl.gz    # Compressed index (gzip level 9)
└── meta_v0.7.0.json       # Metadata with checksum
```

### Atomic Writes

Index files are written atomically using temp file + rename pattern to prevent corruption from interrupted writes.

### Backup Management

- Automatic backup before each save
- Timestamped backup files
- Keeps last 3 backups automatically
- Automatic recovery from latest backup on corruption

### Compression

- Algorithm: gzip (level 9)
- Average compression ratio: 17.5%
- Decompression overhead: <0.3ms
- Transparent to users

## Breaking Changes

**None** - This release is fully backward compatible with v0.6.0.

## Bug Fixes

- Fixed cold startup delay (was ~1.5s, now 7.47ms)
- Fixed index rebuild on every restart
- Fixed lack of corruption recovery mechanism

## Known Limitations

1. **First startup**: Initial index build takes ~1.5s (one-time only)
2. **Jieba loading**: Chinese tokenizer loads in ~1s on first use (cached afterwards)
3. **Version migration**: Index version mismatch triggers rebuild instead of migration (planned for v0.8.0)

## What's New

### New APIs

- `InMemoryIndex.load_or_build()` - Load from disk or build
- `InMemoryIndex.save_index()` - Save with compression
- `InMemoryIndex.load_index()` - Load with decompression
- `InMemoryIndex.add_memory()` - Incremental add
- `InMemoryIndex.remove_memory()` - Incremental remove
- `InMemoryIndex.verify_integrity()` - Health check
- `InMemoryIndex._ensure_loaded()` - Lazy loading support

### New Configuration Options

- `enable_persistence` (bool) - Enable/disable index persistence
- `index_dir` (str) - Custom index directory

### New Files

- `docs/F1_IMPLEMENTATION.md` - Index persistence implementation guide
- `docs/F2_LAZY_LOADING.md` - Lazy loading implementation guide
- `docs/F5_COMPRESSION.md` - Index compression implementation guide
- `docs/F6_RECOVERY.md` - Exception recovery implementation guide
- `docs/F7_PERFORMANCE_TEST.md` - Performance test results
- `tests/test_f1_persistence.py` - F1 test suite
- `tests/test_f2_lazy_loading.py` - F2 test suite
- `tests/test_f5_compression.py` - F5 test suite
- `tests/test_f6_recovery.py` - F6 test suite
- `tests/test_v070_comprehensive.py` - Comprehensive test suite

## Contributors

**Project Lead**: Peter Cheng  
**Core Development**: Friday (OpenClaw AI Assistant)  
**Testing**: Automated test suite + Friday

## License

Copyright 2026 Peter Cheng

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Support

- **GitHub Issues**: https://github.com/opensourceclaw/claw-mem/issues
- **Documentation**: https://github.com/opensourceclaw/claw-mem/tree/main/docs
- **Examples**: https://github.com/opensourceclaw/claw-mem/tree/main/examples

---

**Release Status**: ✅ Published  
**Release URL**: https://github.com/opensourceclaw/claw-mem/releases/tag/v0.7.0
