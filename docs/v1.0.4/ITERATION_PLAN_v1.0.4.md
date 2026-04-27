# claw-mem v1.0.4 Iteration Plan

**Version:** 1.0.4  
**Theme:** Performance Optimization & User Experience  
**Created:** 2026-03-24  
**Status:** 📋 Planning (Ready for Review)  
**Priority:** P1 (High)  
**Component:** claw-mem → NeoMem  
**License:** Apache-2.0  
**Documentation Standard:** 100% English (Apache International Open Source Standard)  

---

## Executive Summary

claw-mem v1.0.4 focuses on **performance optimization, bug fixes, and user experience improvements** based on v1.0.3 production feedback. This is a refinement release, not a major feature release, following the principle of "simple, stable, efficient".

**Core Principle:** 大道至简 (Great Truth is Simple)

---

## Release Strategy

### Version Positioning

| Version | Type | Focus | Status |
|---------|------|-------|--------|
| **v1.0.3** | Feature | Smart Violation Detection | ✅ Released |
| **v1.0.4** | Refinement | Performance + UX | 📋 Planning |
| **v1.0.5** | Refinement | Stability + Bug Fixes | 🔮 Future |
| **v1.0.6** | Refinement | Polish + Documentation | 🔮 Future |
| **v2.0.0** | Major | Five-Layer Architecture | 🔮 Future (2026-07+) |

### Design Principles

1. **Simple** - Minimize complexity
2. **Stable** - No breaking changes
3. **Efficient** - Performance first
4. **Maintainable** - Easy to understand and modify

---

## Problem Statement

### v1.0.3 Production Feedback

**Issues Identified:**
1. ⚠️ **Rule Engine config path** - Default path not always available
2. ⚠️ **Chinese detection** - Some edge cases missed
3. ⚠️ **Release title validation** - Underscore support added late
4. ⚠️ **Integration tests** - Not run before initial release
5. ⚠️ **Documentation** - Some Chinese text remained

**Lessons Learned:**
1. ✅ Always run integration tests before release
2. ✅ Deploy to local environment first, verify, then publish
3. ✅ Follow Apache release process strictly
4. ✅ Keep architecture simple (three-layer, not five-layer)

---

## v1.0.4 Goals

### Primary Objectives

1. ✅ **Fix v1.0.3 bugs** - All known issues resolved
2. ✅ **Performance optimization** - <50ms latency target
3. ✅ **Improve test coverage** - 95%+ coverage
4. ✅ **Documentation polish** - 100% English, complete
5. ✅ **User experience** - Better error messages, clearer logs

### Success Metrics

| Metric | v1.0.3 | v1.0.4 Target | Improvement |
|--------|--------|---------------|-------------|
| **Test Coverage** | 96% | 98% | +2% |
| **Detection Latency** | <100ms | <50ms | -50% |
| **False Positive Rate** | <3% | <2% | -33% |
| **Documentation Completeness** | 95% | 100% | +5% |
| **Bug Count** | 5 known | 0 known | -100% |

---

## Features

### Feature 1: Bug Fixes (BUG-001 ~ BUG-005)

#### BUG-001: Rule Engine Config Path
**Issue:** Default config path not always available  
**Impact:** Rule Engine fails to load rules  
**Fix:** Create config directory if not exists  
**Priority:** P0 (Critical)

**Implementation:**
```python
def __init__(self, config_path: Optional[str] = None):
    if config_path is None:
        config_path = str(Path.home() / '.openclaw' / 'workspace' / 'skills' / 'claw-mem' / 'config' / 'rules.json')
    
    # Create directory if not exists
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    
    self.config_path = config_path
    self.load_config(config_path)
```

---

#### BUG-002: Chinese Detection Edge Cases
**Issue:** Some Chinese variants not detected  
**Impact:** False negatives in language validation  
**Fix:** Expand Unicode range detection  
**Priority:** P0 (Critical)

**Implementation:**
```python
self.violation_patterns = {
    'language': [
        (r'[\u4e00-\u9fff]', 'Chinese characters detected'),  # CJK Unified Ideographs
        (r'[\u3400-\u4dbf]', 'Chinese characters detected'),  # CJK Extension A
        (r'[\u20000-\u2a6df]', 'Chinese characters detected'),  # CJK Extension B
    ]
}
```

---

#### BUG-003: Release Title Underscore Support
**Issue:** claw_rl format not accepted  
**Impact:** Valid package names rejected  
**Fix:** Support both dash and underscore  
**Priority:** P1 (High)

**Implementation:**
```python
self.release_title_pattern = re.compile(
    r'^[a-z][a-z0-9_-]*\s+v\d+\.\d+\.\d+$',
    re.IGNORECASE
)
```

---

#### BUG-004: Integration Tests Not Run
**Issue:** Tests not run before initial release  
**Impact:** Bugs reached production  
**Fix:** Add pre-release test script  
**Priority:** P0 (Critical)

**Implementation:**
```bash
#!/bin/bash
# scripts/pre_release_test.sh

echo "Running pre-release tests..."

# Run integration tests
python3 tests/run_integration_tests.py

# Exit code determines release approval
if [ $? -eq 0 ]; then
    echo "✅ All tests passed - Ready for release"
    exit 0
else
    echo "❌ Tests failed - Do not release"
    exit 1
fi
```

---

#### BUG-005: Documentation Chinese Text
**Issue:** Some Chinese text remained in docs  
**Impact:** Apache compliance issue  
**Fix:** Translate all Chinese to English  
**Priority:** P1 (High)

**Implementation:**
- Manual review of all .md files
- Translation of any Chinese text
- Final review for 100% English compliance

---

### Feature 2: Performance Optimization (PERF-001 ~ PERF-003)

#### PERF-001: Rule Engine Caching
**Goal:** Cache compiled regex patterns  
**Target:** -30% latency  
**Priority:** P1 (High)

**Implementation:**
```python
class RuleEngine:
    def __init__(self, config_path: Optional[str] = None):
        self._regex_cache = {}  # Cache compiled patterns
        # ... rest of init
    
    def validate(self, text: str) -> List[Dict[str, Any]]:
        violations = []
        
        for rule in self.rules:
            if rule.rule_type == 'regex':
                for pattern_str in rule.patterns:
                    # Use cached pattern or compile new
                    if pattern_str not in self._regex_cache:
                        self._regex_cache[pattern_str] = re.compile(pattern_str, re.IGNORECASE)
                    
                    compiled_pattern = self._regex_cache[pattern_str]
                    if compiled_pattern.search(text):
                        violations.append({...})
        
        return violations
```

---

#### PERF-002: Semantic Detector Optimization
**Goal:** Pre-compile all patterns at init  
**Target:** -40% latency  
**Priority:** P1 (High)

**Implementation:**
```python
class SemanticViolationDetector:
    def __init__(self, memory_system=None):
        self.memory_system = memory_system
        
        # Pre-compile all patterns
        self._compiled_patterns = {}
        for category, patterns in self.violation_patterns.items():
            self._compiled_patterns[category] = [
                (re.compile(pattern, re.IGNORECASE), message)
                for pattern, message in patterns
            ]
```

---

#### PERF-003: Memory Retrieval Optimization
**Goal:** Add LRU cache for frequent queries  
**Target:** -50% latency for repeated queries  
**Priority:** P2 (Medium)

**Implementation:**
```python
from functools import lru_cache

class SemanticViolationDetector:
    @lru_cache(maxsize=128)
    def detect_violations_cached(self, action_hash: str) -> List[Violation]:
        # Cached detection logic
        pass
    
    def detect_violations(self, action: str) -> List[Violation]:
        # Use hash for caching
        action_hash = hashlib.md5(action.encode()).hexdigest()
        return self.detect_violations_cached(action_hash)
```

---

### Feature 3: User Experience (UX-001 ~ UX-003)

#### UX-001: Better Error Messages
**Goal:** Clear, actionable error messages  
**Priority:** P2 (Medium)

**Implementation:**
```python
# Before
raise ValueError("Config not found")

# After
raise ValueError(
    f"Configuration file not found at: {config_path}\n"
    f"Please ensure:\n"
    f"  1. File exists at the specified path\n"
    f"  2. File has read permissions\n"
    f"  3. Parent directory exists"
)
```

---

#### UX-002: Verbose Logging Option
**Goal:** Debug mode for troubleshooting  
**Priority:** P3 (Low)

**Implementation:**
```python
class SemanticViolationDetector:
    def __init__(self, memory_system=None, verbose: bool = False):
        self.verbose = verbose
        self.logger = logging.getLogger('semantic_detector')
        
        if verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.WARNING)
```

---

#### UX-003: Configuration Validation
**Goal:** Validate config at load time  
**Priority:** P2 (Medium)

**Implementation:**
```python
def load_config(self, config_path: str):
    path = Path(config_path)
    
    if not path.exists():
        self._create_default_config(path)
        return
    
    with open(path, 'r') as f:
        config = json.load(f)
    
    # Validate config structure
    self._validate_config(config)
    
    # Parse rules
    self.rules = []
    for rule_config in config.get('rules', []):
        # Validate each rule
        self._validate_rule(rule_config)
        rule = Rule(...)
        self.rules.append(rule)
```

---

### Feature 4: Test Coverage (TEST-001 ~ TEST-003)

#### TEST-001: Edge Case Tests
**Goal:** Cover all edge cases  
**Priority:** P1 (High)

**Test Cases:**
- Empty input
- Unicode edge cases
- Very long input (>10KB)
- Special characters
- Mixed languages

---

#### TEST-002: Performance Tests
**Goal:** Benchmark performance  
**Priority:** P2 (Medium)

**Test Cases:**
- Latency under normal load
- Latency under stress (1000 req/s)
- Memory usage
- CPU usage

---

#### TEST-003: Integration Tests Enhancement
**Goal:** End-to-end testing  
**Priority:** P1 (High)

**Test Cases:**
- Full release workflow
- Deployment verification
- Rollback procedure

---

## Implementation Plan

### Week 1: Bug Fixes (2026-03-25 to 2026-03-31)

| Day | Task | Owner | Status |
|-----|------|-------|--------|
| **Day 1** | BUG-001: Rule Engine config path | Friday | 📋 TODO |
| **Day 2** | BUG-002: Chinese detection | Friday | 📋 TODO |
| **Day 3** | BUG-003: Release title underscore | Friday | 📋 TODO |
| **Day 4** | BUG-004: Pre-release test script | Friday | 📋 TODO |
| **Day 5** | BUG-005: Documentation Chinese | Friday | 📋 TODO |
| **Day 6-7** | Buffer / Catch-up | Friday | 📋 TODO |

---

### Week 2: Performance + UX (2026-04-01 to 2026-04-07)

| Day | Task | Owner | Status |
|-----|------|-------|--------|
| **Day 8-9** | PERF-001: Rule Engine caching | Friday | 📋 TODO |
| **Day 10** | PERF-002: Semantic Detector opt | Friday | 📋 TODO |
| **Day 11** | PERF-003: LRU cache | Friday | 📋 TODO |
| **Day 12** | UX-001: Better error messages | Friday | 📋 TODO |
| **Day 13** | UX-002 + UX-003 | Friday | 📋 TODO |
| **Day 14** | Buffer / Catch-up | Friday | 📋 TODO |

---

### Week 3: Testing + Release (2026-04-08 to 2026-04-14)

| Day | Task | Owner | Status |
|-----|------|-------|--------|
| **Day 15-16** | TEST-001: Edge case tests | Friday | 📋 TODO |
| **Day 17** | TEST-002: Performance tests | Friday | 📋 TODO |
| **Day 18** | TEST-003: Integration tests | Friday | 📋 TODO |
| **Day 19** | Documentation final review | Friday | 📋 TODO |
| **Day 20** | Pre-release verification | Friday | 📋 TODO |
| **Day 21** | **Release v1.0.4** | Friday | 📋 TODO |

---

## Testing Strategy

### Unit Tests
- **Target:** 98% coverage
- **Focus:** Edge cases, error handling
- **Tool:** pytest

### Integration Tests
- **Target:** 100% pass rate
- **Focus:** End-to-end workflows
- **Tool:** Custom test runner

### Performance Tests
- **Target:** <50ms latency
- **Focus:** Under load, stress testing
- **Tool:** Custom benchmark script

### User Acceptance Tests
- **Target:** Peter approval
- **Focus:** Real-world usage scenarios
- **Tool:** Live demo

---

## Quality Gates

| Gate | Criteria | Target | Status |
|------|----------|--------|--------|
| **Test Coverage** | Unit test coverage | >98% | 📋 TODO |
| **Integration Tests** | Pass rate | 100% | 📋 TODO |
| **Performance** | Latency | <50ms | 📋 TODO |
| **Documentation** | English compliance | 100% | 📋 TODO |
| **Bug Count** | Known bugs | 0 | 📋 TODO |

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Performance regression** | High | Low | Benchmark before/after each change |
| **Breaking changes** | High | Low | Strict backward compatibility testing |
| **Scope creep** | Medium | Medium | Strict adherence to v1.0.x refinement scope |
| **Timeline slip** | Medium | Low | Daily progress tracking, buffer days |

---

## Success Criteria

**v1.0.4 is considered successful when:**

1. ✅ All v1.0.3 bugs fixed (5/5)
2. ✅ Performance targets met (<50ms latency)
3. ✅ Test coverage >98%
4. ✅ Documentation 100% English
5. ✅ Zero known bugs at release
6. ✅ Peter approval obtained

---

## Release Checklist

### Pre-Release
- [ ] All bug fixes completed
- [ ] All performance optimizations completed
- [ ] All tests passing (98%+ coverage)
- [ ] Documentation 100% English
- [ ] Pre-release test script passes
- [ ] Peter approval obtained

### Release
- [ ] Git tag created (v1.0.4)
- [ ] GitHub Release created
- [ ] Release notes published
- [ ] Local deployment verified

### Post-Release
- [ ] Monitor for issues (48 hours)
- [ ] Collect user feedback
- [ ] Plan v1.0.5 if needed

---

## Related Documents

- `RELEASE_NOTES_v1.0.3.md` - Previous release notes
- `APACHE_RELEASE_PROCESS.md` - Apache release standard
- `AGENT_MEMORY_STRATEGY.md` - Long-term strategy (v2.0.0)
- `docs/` - All project documentation

---

## Contact

**Project Owner:** Peter Cheng  
**Lead Developer:** Friday  
**Repository:** https://github.com/opensourceclaw/claw-mem  
**Documentation:** `/Users/liantian/workspace/claw-mem/docs/`  

---

## Document History

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.0 | 2026-03-24 | Initial iteration plan | Friday |

---

*Document Created: 2026-03-24T22:30+08:00*  
*Version: 1.0.4*  
*Status: 📋 Planning (Ready for Review)*  
*Priority: P1 (High)*  
*Theme: Performance Optimization & User Experience*  
*License: Apache-2.0*  
*Documentation Language: 100% English (Apache Standard)*  
*"Ad Astra Per Aspera"*
