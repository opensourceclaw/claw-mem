# claw-mem v1.0.3 Iteration Plan

**Version:** 1.0.3  
**Theme:** Smart Violation Detection Enhancement  
**Created:** 2026-03-24  
**Status:** 📋 Planning  
**Priority:** P1 (High)  
**Component:** Memory System Enhancement  
**License:** Apache-2.0  
**Documentation Standard:** 100% English (Apache International Open Source Standard)  

---

## Executive Summary

claw-mem v1.0.3 focuses on **intelligent violation detection** to address limitations in v1.0.2's keyword-based approach. This iteration enhances pre-action verification with semantic analysis, comprehensive package name validation, and configurable rule engine.

**Core Objective:** Transform from basic keyword matching to intelligent semantic understanding for rule violation detection.

---

## Problem Statement

### Current Issues (v1.0.2 Limitations)

| Issue | Current Approach | Limitation | Impact |
|-------|------------------|------------|--------|
| **Violation Detection** | Keyword-based | Only detects obvious violations | Some violations missed |
| **Package Name Validation** | Basic keyword matching | Limited recognition | May allow invalid names |
| **Release Title Format** | Basic format checking | Not strictly enforced | Non-standard titles allowed |
| **Rule Configuration** | Hard-coded rules | Not user-configurable | Limited flexibility |

### Real-World Examples

**Example 1: Violation Detection**
```
✅ Detected (v1.0.2): "Write Chinese documentation" violates "100% English" rule
⚠️ Missed (v1.0.2): "用中文写文档" (Chinese text, same violation)
⚠️ Missed (v1.0.2): "Create package neorl" violates "claw_rl" rule
```

**Example 2: Package Name Validation**
```
✅ Detected: "Create package neorl"
⚠️ Missed: "Initialize neorl module"
⚠️ Missed: "Import from neomind package"
```

**Example 3: Release Title Format**
```
✅ Correct: "claw-mem v1.0.2"
⚠️ Allowed (should block): "NeoMind v1.0.2 - Cool Features"
⚠️ Allowed (should block): "Release v1.0.2: Great Update"
```

---

## Iteration Goals

### Primary Goals

1. ✅ **Semantic Violation Detection** - NLP-based understanding
2. ✅ **Package Name Validation** - Comprehensive checking
3. ✅ **Release Title Enforcement** - Strict format validation
4. ✅ **Configurable Rule Engine** - User-defined rules

### Success Metrics

| Metric | Current (v1.0.2) | Target (v1.0.3) | Improvement |
|--------|------------------|-----------------|-------------|
| **Violation Detection Rate** | ~70% | >95% | +25% |
| **False Positive Rate** | <5% | <3% | -40% |
| **Package Name Validation** | Basic | Comprehensive | New |
| **Release Title Compliance** | ~80% | 100% | +20% |
| **Rule Configurability** | 0% | 100% | New |

---

## Features

### Feature 1: Semantic Violation Detection (FR-1)

**Description:** Use NLP to understand rule semantics, not just keyword matching.

**Requirements:**
- [ ] Implement semantic similarity detection
- [ ] Support multi-language violation detection
- [ ] Detect paraphrased violations
- [ ] Maintain <100ms latency

**Implementation Approach:**
```python
class SemanticViolationDetector:
    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.embedding_model = self._load_embedding_model()
    
    def detect_violation(self, action: str, rules: List[Memory]) -> List[Violation]:
        """Detect violations using semantic similarity"""
        # 1. Embed action text
        action_embedding = self.embedding_model.encode(action)
        
        # 2. Compare with rule embeddings
        violations = []
        for rule in rules:
            rule_embedding = self.embedding_model.encode(rule.content)
            similarity = cosine_similarity(action_embedding, rule_embedding)
            
            if similarity > 0.85:  # High similarity threshold
                violations.append(Violation(rule, similarity))
        
        return violations
```

**Acceptance Criteria:**
- [ ] Detects "用中文写文档" as violation of "100% English" rule
- [ ] Detects "Create package neorl" as violation
- [ ] Latency <100ms
- [ ] Detection rate >95%

**Dependencies:**
- Sentence Transformers library
- Pre-trained embedding model (e.g., all-MiniLM-L6-v2)

---

### Feature 2: Package Name Validation (FR-2)

**Description:** Comprehensive package name validation with alias support.

**Requirements:**
- [ ] Maintain list of valid/invalid package names
- [ ] Support aliases and variations
- [ ] Detect indirect references
- [ ] Configurable validation rules

**Implementation:**
```python
class PackageNameValidator:
    def __init__(self):
        self.valid_names = ['claw_rl', 'claw-mem', 'neoclaw']
        self.invalid_names = ['neorl', 'neomind', 'neoclaw-old']
        self.aliases = {
            'neorl': ['neorl', 'neo-rl', 'neo_rl'],
            'neomind': ['neomind', 'neo-mind', 'neo_mind']
        }
    
    def validate(self, text: str) -> ValidationResult:
        """Validate package names in text"""
        violations = []
        
        # Check direct mentions
        for invalid in self.invalid_names:
            if invalid in text.lower():
                violations.append(f"Invalid package name: {invalid}")
        
        # Check aliases
        for invalid, aliases in self.aliases.items():
            for alias in aliases:
                if alias in text.lower():
                    violations.append(f"Invalid package alias: {alias} -> {invalid}")
        
        return ValidationResult(valid=len(violations)==0, violations=violations)
```

**Acceptance Criteria:**
- [ ] Detects "neorl", "neo-rl", "neo_rl" as invalid
- [ ] Detects "neomind", "neo-mind", "neo_mind" as invalid
- [ ] Allows "claw_rl", "claw-mem"
- [ ] Configurable via JSON/YAML

---

### Feature 3: Release Title Format Enforcement (FR-3)

**Description:** Strict format validation for release titles.

**Requirements:**
- [ ] Enforce format: `{project-name} v{version}`
- [ ] Block descriptive subtitles
- [ ] Block emoji in titles
- [ ] Provide format suggestions

**Implementation:**
```python
import re

class ReleaseTitleValidator:
    def __init__(self):
        # Format: {project-name} v{major}.{minor}.{patch}
        self.pattern = re.compile(
            r'^[a-z][a-z0-9-]*\s+v\d+\.\d+\.\d+$',
            re.IGNORECASE
        )
    
    def validate(self, title: str) -> ValidationResult:
        """Validate release title format"""
        violations = []
        
        # Check format
        if not self.pattern.match(title):
            violations.append("Invalid format. Expected: {project} v{version}")
        
        # Check for subtitles
        if ' - ' in title or ': ' in title:
            violations.append("Subtitles not allowed")
        
        # Check for emoji
        if any(char in title for char in '😀😃😄😁'):
            violations.append("Emoji not allowed in release titles")
        
        return ValidationResult(valid=len(violations)==0, violations=violations)
```

**Acceptance Criteria:**
- [ ] ✅ Allows: "claw-mem v1.0.3"
- [ ] ✅ Allows: "claw_rl v1.0.3"
- [ ] ❌ Blocks: "NeoMind v1.0.3 - Cool Features"
- [ ] ❌ Blocks: "Release v1.0.3: Great Update"
- [ ] ❌ Blocks: "claw-mem v1.0.3 🎉"

---

### Feature 4: Configurable Rule Engine (FR-4)

**Description:** Allow users to define custom validation rules.

**Requirements:**
- [ ] JSON/YAML configuration format
- [ ] Support regex patterns
- [ ] Support custom violation messages
- [ ] Hot-reload configuration

**Configuration Format:**
```yaml
# rules.yaml
rules:
  - name: "package_name_validation"
    type: "forbidden_words"
    patterns:
      - "neorl"
      - "neomind"
      - "neo-rl"
    message: "Invalid package name detected"
    severity: "error"
  
  - name: "release_title_format"
    type: "regex"
    pattern: "^[a-z][a-z0-9-]*\\s+v\\d+\\.\\d+\\.\\d+$"
    message: "Release title must be: {project} v{version}"
    severity: "error"
  
  - name: "documentation_language"
    type: "semantic"
    rule: "Apache docs must be 100% English"
    threshold: 0.85
    message: "Documentation must be 100% English"
    severity: "critical"
```

**Acceptance Criteria:**
- [ ] Load rules from YAML/JSON
- [ ] Support forbidden_words type
- [ ] Support regex type
- [ ] Support semantic type
- [ ] Hot-reload on config change

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

**Goals:**
- [ ] Project structure setup
- [ ] Dependencies installation
- [ ] Embedding model integration
- [ ] Base semantic detector

**Deliverables:**
- `core/semantic_detector.py`
- `requirements.txt` updated
- Unit tests for semantic detection

### Phase 2: Validation Rules (Week 3-4)

**Goals:**
- [ ] Package name validator
- [ ] Release title validator
- [ ] Configurable rule engine

**Deliverables:**
- `core/package_validator.py`
- `core/title_validator.py`
- `core/rule_engine.py`
- `config/rules.yaml`

### Phase 3: Integration (Week 5-6)

**Goals:**
- [ ] Integrate with pre-action check
- [ ] Performance optimization
- [ ] Documentation

**Deliverables:**
- Updated `pre_action_check.py`
- Performance benchmarks (<100ms)
- User documentation

### Phase 4: Testing & Release (Week 7-8)

**Goals:**
- [ ] Integration tests
- [ ] User acceptance testing
- [ ] Release preparation

**Deliverables:**
- Test suite (90%+ coverage)
- Release notes
- v1.0.3 release

---

## Testing Strategy

### Unit Tests

| Component | Tests | Coverage Target |
|-----------|-------|-----------------|
| Semantic Detector | 20 | 95% |
| Package Validator | 15 | 95% |
| Title Validator | 10 | 95% |
| Rule Engine | 15 | 95% |
| **Total** | **60** | **95%** |

### Integration Tests

| Test | Scenario | Status |
|------|----------|--------|
| Semantic Detection | Detects Chinese text as English violation | 📋 TODO |
| Package Validation | Detects "neorl" variations | 📋 TODO |
| Title Format | Blocks non-standard titles | 📋 TODO |
| Rule Config | Hot-reload configuration | 📋 TODO |

### Performance Tests

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Semantic Detection | <100ms | Average latency |
| Package Validation | <10ms | Average latency |
| Title Validation | <5ms | Average latency |
| Rule Engine Load | <50ms | Configuration load |

---

## Success Metrics

### Technical Metrics

| Metric | Baseline (v1.0.2) | Target (v1.0.3) | Measurement |
|--------|-------------------|-----------------|-------------|
| **Violation Detection Rate** | ~70% | >95% | Test suite |
| **False Positive Rate** | <5% | <3% | Test suite |
| **Semantic Detection Latency** | N/A | <100ms | Performance tests |
| **Rule Configurability** | 0% | 100% | Feature checklist |

### User Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **User Satisfaction** | 9/10 | 9.5/10 | Post-release survey |
| **Rule Flexibility** | Low | High | User feedback |
| **Detection Accuracy** | 70% | 95% | User validation |

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Performance Degradation** | High | Medium | Optimize embedding model, caching |
| **False Positives** | Medium | Medium | Tune similarity thresholds |
| **Configuration Complexity** | Low | Low | Provide default config, examples |
| **Dependency Issues** | Medium | Low | Pin versions, test thoroughly |

**Overall Risk Level:** 🟢 **LOW** (Manageable with mitigation)

---

## Documentation

### New Documentation

- [ ] `docs/SEMANTIC_DETECTION.md` - How semantic detection works
- [ ] `docs/PACKAGE_VALIDATION.md` - Package name validation rules
- [ ] `docs/RELEASE_TITLE_FORMAT.md` - Release title format guide
- [ ] `docs/RULE_ENGINE.md` - Configurable rule engine guide
- [ ] `docs/RULES_CONFIG.md` - Rules configuration reference

### Updated Documentation

- [ ] `README.md` - Add v1.0.3 features
- [ ] `RELEASE_NOTES_v1.0.3.md` - Complete release notes
- [ ] `docs/PRE_ACTION_CHECK.md` - Update with semantic detection

---

## Release Plan

### Timeline

| Phase | Duration | Dates | Status |
|-------|----------|-------|--------|
| **Phase 1: Foundation** | 2 weeks | 2026-03-25 to 04-07 | 📋 Planned |
| **Phase 2: Validation Rules** | 2 weeks | 2026-04-08 to 04-21 | 📋 Planned |
| **Phase 3: Integration** | 2 weeks | 2026-04-22 to 05-05 | 📋 Planned |
| **Phase 4: Testing** | 2 weeks | 2026-05-06 to 05-19 | 📋 Planned |
| **Release** | - | 2026-05-20 | 📋 Planned |

### Release Checklist

- [ ] All features implemented
- [ ] All tests passing (95%+ coverage)
- [ ] Performance benchmarks met (<100ms)
- [ ] Documentation complete (100% English)
- [ ] User acceptance testing passed
- [ ] Release notes ready

---

## Team & Responsibilities

| Role | Person | Responsibilities |
|------|--------|------------------|
| **Product Owner** | Peter Cheng | Requirements, priorities, approval |
| **Lead Developer** | Friday | Implementation, testing, documentation |
| **QA** | Automated Tests | Test coverage, quality gates |

---

## Contact

**Repository:** https://github.com/opensourceclaw/claw-mem  
**Issues:** https://github.com/opensourceclaw/claw-mem/issues  
**Documentation:** `/Users/liantian/workspace/claw-mem/docs/`  

---

## Document History

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.0 | 2026-03-24 | Initial iteration plan | Friday |

---

*Document Created: 2026-03-24T17:15+08:00*  
*Version: 1.0.3*  
*Status: 📋 Planning*  
*Priority: P1 (High)*  
*Target Release: v1.0.3*  
*Theme: Smart Violation Detection Enhancement*  
*License: Apache-2.0*  
*Documentation Language: 100% English (Apache Standard)*
