# Dev Agent Task Assignment - claw-mem v1.0.0 Sprint

**Assigned**: 2026-03-23 14:20  
**Sprint End**: 2026-03-30  
**Coordinator**: Stark (Work Pillar)

---

## 🔴 P0 Tasks (Critical - Must Complete)

### Task 1: Cross-Session Memory Retrieval Fix
**Priority**: P0  
**Estimate**: 8 hours  
**Due**: 2026-03-26

**Requirements**:
- Implement three-tier retrieval API (L1/L2/L3)
- Session startup hook for automatic retrieval
- Manual search command (`/search`)
- Intent classification for topic-based retrieval

**Reference**: `/docs/claw-mem-v1.0.0-requirements.md` (REQ-001, REQ-002)

**Acceptance Criteria**:
- [ ] New session can retrieve memories from previous sessions
- [ ] Search API returns results from L2 (daily memory) and L3 (MEMORY.md)
- [ ] Retrieval latency < 2 seconds
- [ ] Unit tests with 95%+ coverage
- [ ] Integration tests passing

---

### Task 2: Context Injection Fix
**Priority**: P0  
**Estimate**: 4 hours  
**Due**: 2026-03-25

**Requirements**:
- Fix memory context injection into session prompts
- Ensure retrieved memories are properly formatted
- Handle edge cases (empty results, special characters)

**Acceptance Criteria**:
- [ ] Retrieved memories appear in session context
- [ ] No formatting errors in injected content
- [ ] Edge cases handled gracefully
- [ ] Unit tests passing

---

### Task 3: Display Bug Fixes
**Priority**: P0  
**Estimate**: 4 hours  
**Due**: 2026-03-25

**Requirements**:
- Fix CLI memory display issues
- Fix plugin output formatting
- Handle special characters and encoding

**Acceptance Criteria**:
- [ ] All CLI commands display correctly
- [ ] Plugin output properly formatted
- [ ] No encoding errors
- [ ] Regression tests added

---

### Task 4: 100% English Technical Documentation
**Priority**: P0  
**Estimate**: 4 hours  
**Due**: 2026-03-27

**Requirements**:
- Review all `/docs/` files for Chinese content
- Translate any remaining Chinese to English
- Update code comments to English
- Ensure consistency in terminology

**Acceptance Criteria**:
- [ ] All markdown files in `/docs/` are 100% English
- [ ] All code comments are English
- [ ] API documentation complete
- [ ] No Chinese characters in technical docs

---

### Task 5: Apache 2.0 License Configuration
**Priority**: P0  
**Estimate**: 30 minutes  
**Due**: 2026-03-23

**Requirements**:
- Verify LICENSE file is present and correct
- Ensure pyproject.toml has license field
- Add license headers to source files if needed

**Status**: ✅ Already complete (LICENSE file verified)

**Acceptance Criteria**:
- [x] LICENSE file present with Apache 2.0 text
- [x] pyproject.toml has `license = "Apache-2.0"`
- [ ] Verify all source files have license header (if required)

---

## 🟡 P1 Tasks (Important - Quality Improvement)

### Task 6: Test Coverage 95-100%
**Priority**: P1  
**Estimate**: 6 hours  
**Due**: 2026-03-28

**Requirements**:
- Fix existing test failures (test_f5_compression.py, test_integration_v090.py)
- Add missing unit tests for new features
- Achieve 95-100% code coverage

**Acceptance Criteria**:
- [ ] All tests passing
- [ ] Coverage report shows 95%+
- [ ] No skipped or xfail tests without justification

---

### Task 7: Performance Optimization <500ms
**Priority**: P1  
**Estimate**: 4 hours  
**Due**: 2026-03-28

**Requirements**:
- Profile retrieval performance
- Optimize index loading and search
- Reduce memory footprint

**Acceptance Criteria**:
- [ ] Retrieval latency < 500ms (p95)
- [ ] Memory usage < 100MB for index
- [ ] Cold start < 2 seconds

---

### Task 8: Performance Benchmarks
**Priority**: P1  
**Estimate**: 2 hours  
**Due**: 2026-03-29

**Requirements**:
- Create benchmark suite for retrieval
- Document baseline metrics
- Set up CI benchmarking

**Acceptance Criteria**:
- [ ] Benchmark scripts in `/scripts/benchmarks/`
- [ ] Baseline metrics documented
- [ ] CI integration for regression detection

---

## 🛠️ Development Guidelines

### Code Quality
- Follow existing code style (black, flake8 configured)
- Type hints required for all public APIs
- Docstrings in English for all functions/classes

### Testing
- Unit tests in `/tests/` directory
- Naming: `test_<feature>.py`
- Use pytest fixtures for common setup

### Documentation
- All docs in `/docs/` must be 100% English
- API docs with examples
- Changelog updates for each feature

### Git Workflow
- Branch naming: `feature/<name>`, `fix/<name>`, `docs/<name>`
- Commit messages: conventional commits format
- PR required for all changes

---

## 📊 Progress Tracking

Update this file as tasks complete:

| Task | Status | Progress | Notes |
|------|--------|----------|-------|
| Task 1 | 📋 Not Started | 0% | - |
| Task 2 | 📋 Not Started | 0% | - |
| Task 3 | 📋 Not Started | 0% | - |
| Task 4 | 📋 Not Started | 0% | - |
| Task 5 | ✅ Complete | 100% | License verified |
| Task 6 | 📋 Not Started | 0% | - |
| Task 7 | 📋 Not Started | 0% | - |
| Task 8 | 📋 Not Started | 0% | - |

---

## 📞 Communication

- **Coordinator**: Stark (Work Pillar)
- **Daily Standup**: Report progress via subagent
- **Blockers**: Report immediately to Stark
- **Questions**: Use Study Agent for research support

---

**Good luck! Let's build a production-ready v1.0.0! 🚀**
