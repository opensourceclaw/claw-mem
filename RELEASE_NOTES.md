# claw-mem v2.0.0-rc.1 Release Notes

**Release Date:** 2026-04-03
**Version Type:** Release Candidate (RC)

---

## Overview

This is the first Release Candidate for claw-mem v2.0.0, an improved version based on v2.0.0-beta.3.

## Quality Metrics

| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| Tests | 94 passed, 2 skipped | All pass | ✅ |
| Test Coverage | 49% | >= 70% | ⚠️ Technical Debt |
| ID Generation | Fixed | Correct | ✅ |
| AsyncIO Tests | Fixed | Pass | ✅ |

## What's Changed

### Bug Fixes

- **ID generation logic**: Fixed ID generation only after record creation in `MemoryManager.store()`
- **AsyncIO tests**: Fixed async method calls in async tests

### Improvements

- **Version upgrade**: v2.0.0-beta.3 to v2.0.0-rc.1
- **Best practices**: Integrated OpenAI Harness Engineering and Anthropic Harness Design

## Known Issues & Limitations

### Technical Debt

- **Test coverage**: 49% (target: >= 70%)
  - Planned for future releases
  - Need more edge case and exception scenario tests

### Next Steps

1. Increase test coverage to 80%
2. Integrate Context Engine (semantic query capabilities)
3. Integrate Ralph Wiggum Loop (automated iteration mechanism)

## Acknowledgments

Contributors:
- Friday (AI Agent) - Development and implementation
- JARVIS (AI Agent) - Code review

---

## References

- [ADR-007: Versioning Strategy](https://github.com/opensourceclaw/neoclaw/blob/main/docs/v2.0.0/architecture/ADR-007-versioning-strategy.md)
- [OpenAI Harness Engineering](https://openai.com/index/harness-engineering/)
- [Anthropic Harness Design](https://www.anthropic.com/engineering/harness-design-long-running-apps)
