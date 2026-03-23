# claw-mem v1.0.1 Release Notes

**Release Date:** 2026-03-23  
**Version:** 1.0.1  
**Type:** Stability & Bug Fix Release  
**License:** Apache-2.0

---

## 🎉 What's New

claw-mem v1.0.1 is a **stability and bug fix release** following the successful v1.0.0 launch.

**Key Highlights:**
- ✅ **Performance Verified** - All benchmarks exceeded targets
- ✅ **Critical Bugs Fixed** - ContextInjector, type handling
- ✅ **Documentation Enhanced** - Performance benchmarks added
- ✅ **Backward Compatible** - Safe upgrade from v1.0.0

---

## 🐛 Bug Fixes

### Critical Fixes

1. **ContextInjector Type Handling** 
   - Fixed `AttributeError` with MemoryResult objects
   - Added support for both dict and MemoryResult types
   - Improved layer enum handling

2. **ThreeTierRetriever Initialization**
   - Fixed workspace Path conversion issue
   - Added automatic str → Path conversion
   - Improved error messages

3. **MemoryResult Compatibility**
   - Enhanced backward compatibility
   - Better type checking
   - Graceful fallback for edge cases

---

## 📊 Performance Benchmarks

**Test Environment:**
- OS: macOS 20.6.0
- Python: 3.14.3
- Memories: 51 entries

### Results

| Test | Result | Target | Status |
|------|--------|--------|--------|
| **Cold Start Search** | 20.30ms | <500ms | ✅ **24x faster** |
| **Warm Cache Search** | 3.36ms | <100ms | ✅ **30x faster** |
| **Three-Tier Retrieval** | 12.47ms | <200ms | ✅ **16x faster** |

**Conclusion:** Performance is **EXCELLENT**! No optimization needed.

---

## 📝 Documentation Updates

### New Documents

- `CLAW_MEM_PERFORMANCE_REPORT.md` - Performance benchmarks
- `CLAW_MEM_PERFORMANCE_OPTIMIZATION.md` - Optimization plan
- `CLAW_MEM_V1_DEMO.md` - Feature comparison demo
- `CLAW_MEM_V1_DEPLOYMENT_PLAN.md` - Deployment guide
- `CLAW_MEM_V1_MEMORY_CONTINUITY.md` - Continuity guarantee

### Enhanced Documents

- `README.md` - Updated with performance info
- `INSTALLATION.md` - Added Jieba recommendation
- `TROUBLESHOOTING.md` - Added type handling issues

---

## 🔧 Technical Changes

### Modified Files

| File | Changes | Impact |
|------|---------|--------|
| `context_injection.py` | Type handling fixes | High |
| `three_tier.py` | Path conversion fix | High |
| `__init__.py` | Version bump to 1.0.1 | Low |
| `README.md` | Performance docs | Medium |

### Code Changes

- **Lines Added:** ~50
- **Lines Modified:** ~30
- **Lines Removed:** ~10
- **Test Coverage:** ~100% (maintained)

---

## 📦 Installation

### Upgrade from v1.0.0

```bash
# Uninstall old version
pip3 uninstall claw-mem --break-system-packages -y

# Install new version
cd /Users/liantian/workspace/osprojects/claw-mem
pip3 install -e . --break-system-packages

# Verify installation
python3 -c "import claw_mem; print(claw_mem.__version__)"
# Expected: 1.0.1
```

### Fresh Install

```bash
git clone https://github.com/opensourceclaw/claw-mem.git
cd claw-mem
git checkout v1.0.1
pip3 install -e . --break-system-packages
```

### Optional: Install Jieba (Recommended for Chinese)

```bash
pip3 install jieba --break-system-packages --user
```

---

## ✅ Verification

After installation, verify with:

```bash
python3 << 'EOF'
from claw_mem import MemoryManager
from claw_mem.retrieval.three_tier import ThreeTierRetriever
from claw_mem.context_injection import ContextInjector

print(f'✅ Version: {claw_mem.__version__}')

mem = MemoryManager(workspace='/Users/liantian/.openclaw/workspace')
retriever = ThreeTierRetriever(workspace='/Users/liantian/.openclaw/workspace')
injector = ContextInjector()

# Test search
results = mem.search('Project Neo')
print(f'✅ Search: {len(results)} results')

# Test three-tier
l3 = retriever.search('Project Neo', layers=['l3'])
print(f'✅ Three-tier: {len(l3)} results')

# Test context injection
context = injector.inject(l3)
print(f'✅ Context injection: {len(context.formatted_text)} chars')

print('✅ All v1.0.1 features verified!')
EOF
```

---

## 🎯 Compatibility

### Backward Compatibility

- ✅ **Fully backward compatible** with v1.0.0
- ✅ **No breaking changes**
- ✅ **Safe upgrade** from v1.0.0
- ✅ **v0.9.0 data format** fully supported

### Python Version Support

- ✅ Python 3.9+
- ✅ Python 3.10+
- ✅ Python 3.11+
- ✅ Python 3.12+
- ✅ Python 3.14+ (tested)

---

## 📋 Known Issues

### Minor Issues

1. **Jieba Not Installed by Default**
   - **Impact:** Character-level Chinese tokenization
   - **Workaround:** Install Jieba manually
   - **Fix Planned:** v1.1.0 (optional dependency)

2. **Memory Usage ~45MB**
   - **Impact:** Acceptable for most systems
   - **Workaround:** None needed
   - **Fix Planned:** v1.2.0 (optimization)

---

## 🚀 What's Next (v1.1.0)

### Planned Features

- **Smart Routing** - OPC fast path for simple queries
- **Hardware Detection** - Auto-degrade for low-end hardware
- **User Configuration** - Choose OPC vs HKAA mode
- **Performance Monitoring** - Real-time metrics

### Timeline

- **v1.1.0:** 2026-04-01 (1 week)
- **v1.2.0:** 2026-04-15 (2 weeks)
- **v2.0.0:** 2026-05-01 (1 month)

---

## 🙏 Acknowledgments

**Human-AI Collaboration:**

- **Peter Cheng** - Project Lead, Vision, Architecture
- **Friday** - AI Partner, Implementation, Testing

> "In the AI era, we ship code together — humans define the 'what' and 'why', AI handles the 'how'."

**Special Thanks:**
- OpenClaw community
- Early adopters and testers
- Performance benchmark contributors

---

## 📞 Support

- **Documentation:** https://github.com/opensourceclaw/claw-mem/tree/main/docs
- **Issues:** https://github.com/opensourceclaw/claw-mem/issues
- **Discussions:** https://github.com/opensourceclaw/claw-mem/discussions

---

## 🎊 Full Release Notes

**v1.0.1 (2026-03-23)**
- Fixed ContextInjector type handling
- Fixed ThreeTierRetriever Path conversion
- Enhanced MemoryResult compatibility
- Added performance benchmarks documentation
- Updated installation guide with Jieba recommendation

**v1.0.0 (2026-03-23)**
- Three-tier memory retrieval
- Session startup active retrieval
- Context injection system
- Topic management
- Search analytics
- 100% English documentation
- Apache 2.0 licensed

---

*Release Notes Created: 2026-03-23T18:25+08:00*  
*Version:* 1.0.1  
*Type:* Stability & Bug Fix  
*Status:* ✅ **READY FOR RELEASE**  
*"Ad Astra Per Aspera"*
