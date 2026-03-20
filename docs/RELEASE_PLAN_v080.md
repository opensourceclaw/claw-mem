# claw-mem v0.8.0 Release Plan

**Version**: v0.8.0  
**Theme**: User Experience & Intelligence  
**Status**: 📋 Planning  
**Created**: 2026-03-20  
**Target Release**: 2026-03-25 (5 days iteration)

---

## 📋 Iteration Background

### v0.7.0 Completion Status

| Metric | Status | Details |
|--------|--------|---------|
| **Startup Time** | ✅ 7.47ms | 191x improvement |
| **Index Compression** | ✅ 82.5% reduction | 11KB |
| **Lazy Loading** | ✅ 0.133ms | Instant startup |
| **Exception Recovery** | ✅ Auto backup | Corruption recovery |
| **Test Coverage** | ✅ 100% | Functional + performance |

**v0.7.0 Core Achievement**: Performance optimization completed, solid technical foundation ✅

### v0.8.0 Focus Direction

Based on v0.7.0 post-release review, v0.8.0 focuses on:

```
┌─────────────────────────────────────────────────────────────┐
│                    v0.8.0 Core Theme                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  From "Technically Qualified" → "Product Mature"            │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Key Improvements:                                          │
│  • Lower usage barrier (installation, config, errors)       │
│  • Enhanced intelligence (auto rules, importance scoring)   │
│  • Better UX (error messages, visualization, debug)         │
│  • Community building start (feedback channels, docs)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Feature Planning

### P0 Priority (Must Release)

| ID | Feature | Description | Effort | Value |
|----|---------|-------------|--------|-------|
| **F001** | PyPI Release | Official PyPI package | 1 day | 🔴 Very High |
| **F002** | Error Friendliness | Chinese errors + fix suggestions | 1 day | 🔴 High |
| **F003** | Auto Config Detection | Auto-detect OpenClaw workspace | 0.5 day | 🔴 High |
| **F004** | Importance Scoring | Auto scoring based on type, frequency | 2 days | 🟡 Medium-High |

**Subtotal**: 4.5 days

---

### P1 Priority (Strongly Recommended)

| ID | Feature | Description | Effort | Value |
|----|---------|-------------|--------|-------|
| **F101** | Auto Rule Extraction | Extract Pre-flight rules from corrections | 2 days | 🟡 High |
| **F102** | Memory Decay | Ebbinghaus forgetting curve | 1.5 days | 🟡 Medium |
| **F103** | CLI Visualization | Simple terminal visualization | 1.5 days | 🟡 Medium |
| **F104** | Backup/Restore | claw-mem backup/restore commands | 0.5 day | 🟡 Medium |

**Subtotal**: 5.5 days

---

### P2 Priority (Optional)

| ID | Feature | Description | Effort | Value |
|----|---------|-------------|--------|-------|
| **F201** | Debug Mode | Search logs, detailed errors | 1 day | 🟢 Low |
| **F202** | Statistics Dashboard | Memory status statistics | 0.5 day | 🟢 Low |
| **F203** | Documentation Optimization | Beginner tutorial series | 1 day | 🟢 Medium |

**Subtotal**: 2.5 days

---

## 📅 Iteration Plan

### Option A: Lite Version (Recommended)

**Duration**: 5 days  
**Scope**: P0 features only  
**Release**: 2026-03-25

```
Day 1 (03-21): F001 PyPI Release
Day 2 (03-22): F002 Error Friendliness + F003 Auto Config
Day 3 (03-23): F004 Importance Scoring
Day 4 (03-24): Testing + Documentation
Day 5 (03-25): Release Verification
```

**Pros**: Fast delivery, focus on core value  
**Cons**: P1 features deferred

---

### Option B: Full Version

**Duration**: 10 days  
**Scope**: P0 + P1 features  
**Release**: 2026-03-30

```
Day 1-2: F001 PyPI Release
Day 3: F002 + F003 UX Improvements
Day 4-5: F004 Importance Scoring
Day 6-7: F101 Auto Rule Extraction
Day 8: F102 Memory Decay
Day 9: F103 + F104 Tools
Day 10: Testing + Release
```

**Pros**: Complete features, significant product maturity improvement  
**Cons**: Long iteration cycle, may delay

---

### Option C: Phased Release

**Duration**: Two phases  
**Scope**: P0 → P1 in batches

```
v0.8.0 (03-25): P0 features - UX foundation
v0.8.1 (03-30): P1 features - Intelligence enhancement
```

**Pros**: Balance speed and completeness  
**Cons**: Two release cycles

---

## 🔧 Technical Design

### F001: PyPI Release

**Task List**:
- [ ] Create pyproject.toml
- [ ] Configure setup.cfg
- [ ] Prepare PyPI account
- [ ] Test on TestPyPI
- [ ] Official release

**Configuration Template**:
```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "claw-mem"
version = "0.8.0"
description = "AI Harness Engineering Memory System"
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.9"
authors = [
    {name = "Peter Cheng", email = "peter.cheng@example.com"}
]
keywords = ["ai", "memory", "openclaw", "harness"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "rank-bm25>=0.2.2",
    "cachetools>=5.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-benchmark",
]
zh = [
    "jieba>=0.42.1",  # Chinese tokenization
]

[project.scripts]
claw-mem = "claw_mem.cli:main"

[project.urls]
Homepage = "https://github.com/opensourceclaw/claw-mem"
Documentation = "https://github.com/opensourceclaw/claw-mem/docs"
Repository = "https://github.com/opensourceclaw/claw-mem/claw-mem.git"
```

---

### F002: Error Message Friendliness

**Current Issue**:
```python
❌ Current:
Error: Index not found at ~/.claw-mem/index/index_v0.8.0.pkl.gz

✅ Target:
[Error] Memory index not found, rebuilding... (about 1 second)
[Suggestion] If this persists, run: claw-mem repair
[Error Code] INDEX_NOT_FOUND
```

**Implementation**:
```python
class FriendlyError(Exception):
    """Friendly error message base class"""
    
    def __init__(self, message: str, suggestion: str = None, 
                 error_code: str = None):
        self.message = message
        self.suggestion = suggestion
        self.error_code = error_code
        super().__init__(self.format())
    
    def format(self) -> str:
        output = f"[Error] {self.message}\n"
        if self.suggestion:
            output += f"[Suggestion] {self.suggestion}\n"
        if self.error_code:
            output += f"[Error Code] {self.error_code}\n"
        return output

# Usage example
def load_index(self):
    if not os.path.exists(self.index_path):
        raise FriendlyError(
            message="Memory index not found, rebuilding...",
            suggestion="First startup needs to rebuild index, please wait",
            error_code="INDEX_NOT_FOUND"
        )
```

**Error Type List**:
| Error Code | Scenario | Friendly Message |
|------------|----------|-----------------|
| INDEX_NOT_FOUND | Index not exists | Rebuilding, please wait |
| WORKSPACE_NOT_FOUND | Workspace not found | Please check OpenClaw config |
| MEMORY_CORRUPTED | Memory file corrupted | Try restore from backup |
| PERMISSION_DENIED | Permission denied | Please check file permissions |

---

### F003: Auto Configuration Detection

**Current Issue**:
```python
# User must manually configure
memory = MemoryManager(
    workspace="/Users/liantian/.openclaw/workspace"  # Manual
)
```

**Target**:
```python
# Auto-detect
memory = MemoryManager()  # Auto-find OpenClaw workspace
```

**Implementation**:
```python
class ConfigDetector:
    """Auto-detect OpenClaw configuration"""
    
    DEFAULT_PATHS = [
        os.path.expanduser("~/.openclaw/workspace"),
        os.path.expanduser("~/.config/openclaw/workspace"),
        os.getcwd(),  # Current directory
    ]
    
    @classmethod
    def detect_workspace(cls) -> Optional[str]:
        """Detect OpenClaw workspace path"""
        for path in cls.DEFAULT_PATHS:
            if cls._is_valid_workspace(path):
                return path
        
        # None found, return default
        return cls.DEFAULT_PATHS[0]
    
    @classmethod
    def _is_valid_workspace(cls, path: str) -> bool:
        """Validate if it's a valid workspace"""
        if not os.path.exists(path):
            return False
        
        # Check if has MEMORY.md or memory/ directory
        has_memory_md = os.path.exists(os.path.join(path, "MEMORY.md"))
        has_memory_dir = os.path.exists(os.path.join(path, "memory"))
        
        return has_memory_md or has_memory_dir

# MemoryManager refactoring
class MemoryManager:
    def __init__(self, workspace: str = None, config: dict = None):
        if workspace is None:
            workspace = ConfigDetector.detect_workspace()
        
        self.workspace = workspace
        self.config = config or {}
```

---

### F004: Memory Importance Scoring

**Design Concept**:
```
Importance Score = Base (1.0) + Type Weight + Frequency Weight + Recency Weight

Base Score: 1.0
Type Weight:
  - Semantic (core facts): +0.5
  - Procedural (skills): +0.3
  - Episodic (daily): +0.0

Frequency Weight:
  - Access count > 10: +0.3
  - Access count > 5: +0.2
  - Access count > 1: +0.1

Recency Weight:
  - Accessed within 7 days: +0.2
  - Accessed within 30 days: +0.1

Maximum: 2.0
```

**Implementation**:
```python
class ImportanceScorer:
    """Memory importance scorer"""
    
    TYPE_WEIGHTS = {
        'semantic': 0.5,
        'procedural': 0.3,
        'episodic': 0.0,
    }
    
    def calculate(self, memory: Memory) -> float:
        score = 1.0  # Base score
        
        # Type weight
        score += self.TYPE_WEIGHTS.get(memory.memory_type, 0.0)
        
        # Frequency weight
        if memory.access_count > 10:
            score += 0.3
        elif memory.access_count > 5:
            score += 0.2
        elif memory.access_count > 1:
            score += 0.1
        
        # Recency weight
        days_since_access = (datetime.now() - memory.accessed_at).days
        if days_since_access < 7:
            score += 0.2
        elif days_since_access < 30:
            score += 0.1
        
        # Cap at 2.0
        return min(2.0, score)
    
    def should_prioritize(self, memory: Memory, threshold: float = 1.5) -> bool:
        """Should prioritize in retrieval"""
        return self.calculate(memory) >= threshold
```

**Application Scenarios**:
- Search results re-ranking (high importance first)
- Memory expiration judgment (low priority expires first)
- Context injection filtering (only inject high-importance memories)

---

### F101: Auto Rule Extraction

**Scenario**:
```
User: ❌ Don't create files to ~/.openclaw/workspace/
AI:  OK, I remembered.

→ Auto-extract rule:
   "File creation operation, forbidden path: ~/.openclaw/workspace/*"
```

**Implementation**:
```python
class RuleExtractor:
    """Auto-extract rules from user corrections"""
    
    FORBIDDEN_PATTERNS = [
        (r"Don't (create|write|save).*?to (.*?)$", "FORBIDDEN_PATH"),
        (r"Never (use|call).*?(.*?)$", "FORBIDDEN_TOOL"),
        (r"Must (first|before).*?then", "REQUIRE_ORDER"),
        # More patterns...
    ]
    
    def extract(self, conversation: str) -> Optional[Rule]:
        """Extract rules from conversation"""
        for pattern, rule_type in self.FORBIDDEN_PATTERNS:
            match = re.search(pattern, conversation)
            if match:
                return self._create_rule(match, rule_type)
        return None
    
    def _create_rule(self, match, rule_type: str) -> Rule:
        """Create rule object"""
        if rule_type == "FORBIDDEN_PATH":
            return Rule(
                type="PATH_CONSTRAINT",
                condition=f"path != '{match.group(2)}'",
                action="REJECT",
                message=f"Forbidden to write to {match.group(2)}"
            )
        # Other rule types...
```

**Rule Storage**:
```markdown
# memory/rules/auto-extracted.md

## Rule 001
- **Type**: PATH_CONSTRAINT
- **Trigger**: File creation operations
- **Condition**: path not starting with ~/.openclaw/workspace/
- **Action**: REJECT
- **Source**: 2026-03-20 User correction
- **Confidence**: 0.9
```

---

### F102: Memory Decay Mechanism

**Implement Ebbinghaus Forgetting Curve**:
```python
class ActivationDecay:
    """Activation decay - Ebbinghaus forgetting curve"""
    
    DECAY_CONSTANTS = {
        'episodic': 7,    # 7 days half-life
        'semantic': 90,   # 90 days half-life
        'procedural': 180, # 180 days half-life
    }
    
    def decay(self, memory: Memory) -> float:
        """Calculate current activation level"""
        tau = self.DECAY_CONSTANTS[memory.memory_type]
        days = (datetime.now() - memory.accessed_at).days
        
        # Ebbinghaus formula: A(t) = A₀ * exp(-t/τ)
        activation = memory.activation_level * math.exp(-days / tau)
        
        # Boost on access
        if days == 0:
            activation = min(1.0, activation + 0.1)
        
        return activation
    
    def should_archive(self, memory: Memory) -> bool:
        """Should archive"""
        if memory.memory_type == 'episodic':
            return self.decay(memory) < 0.1
        return False  # Semantic and procedural don't expire
```

---

### F103: CLI Visualization Tools

**Command Design**:
```bash
# View memory status
claw-mem stats

# Example output:
┌────────────────────────────────────────────────┐
│              claw-mem Memory Status            │
├────────────────────────────────────────────────┤
│ Total Memories: 1234                           │
│ ├─ Semantic: 123                               │
│ ├─ Episodic: 1000                              │
│ └─ Procedural: 111                             │
│                                                │
│ Index Size: 11KB                               │
│ Last Updated: 2026-03-20 14:30                │
│ Average Importance: 1.35                       │
└────────────────────────────────────────────────┘

# Search memory (with visualization)
claw-mem search "date format" --visualize

# View search logs
claw-mem debug --last-search
```

---

## 📊 Acceptance Criteria

### F001 PyPI Release
- [ ] `pip install claw-mem` succeeds
- [ ] Version correct (0.8.0)
- [ ] Dependencies auto-installed
- [ ] CLI command available

### F002 Error Friendliness
- [ ] All error messages in Chinese
- [ ] 80% errors have fix suggestions
- [ ] Error codes queryable in documentation

### F003 Auto Configuration
- [ ] Auto-detect workspace by default
- [ ] Friendly message on detection failure
- [ ] Support manual override

### F004 Importance Scoring
- [ ] Scoring formula reasonable
- [ ] Search results ranked by importance
- [ ] No significant performance impact

### F101 Auto Rules
- [ ] Can identify common correction patterns
- [ ] Extracted rules are executable
- [ ] Support rule review (not auto-apply)

### F102 Memory Decay
- [ ] Forgetting curve formula correct
- [ ] Different decay rates for different types
- [ ] Support configuring decay constants

### F103 CLI Visualization
- [ ] stats command output beautiful
- [ ] search supports visualization
- [ ] debug command shows detailed info

---

## ⚠️ Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PyPI release process complex | Medium | Medium | Prepare early, test TestPyPI first |
| Auto rule extraction accuracy low | High | Low | Default not auto-apply, requires review |
| Importance scoring impacts performance | Low | Medium | Cache scoring results |
| Iteration cycle delay | Medium | Medium | Use Option A (lite version) |

**Overall Risk**: Low-Medium ✅

---

## 📝 Documentation Update List

| Document | Change | Priority |
|----------|--------|----------|
| README.md | Update installation method (PyPI) | 🔴 |
| CHANGELOG.md | Add v0.8.0 changes | 🔴 |
| docs/ERROR_CODES.md | New error codes documentation | 🟡 |
| docs/IMPORTANCE_SCORING.md | Importance scoring guide | 🟡 |
| docs/AUTO_RULES.md | Auto rule extraction guide | 🟡 |
| docs/CLI_GUIDE.md | CLI usage guide | 🟡 |

---

## 🎯 Release Checklist

### Pre-Release
- [ ] All P0 features complete
- [ ] Test coverage >95%
- [ ] Performance tests passed
- [ ] Documentation updated
- [ ] Peter review confirmation

### During Release
- [ ] Git Tag creation (v0.8.0)
- [ ] GitHub Release publish
- [ ] PyPI package publish
- [ ] README update

### Post-Release
- [ ] Installation verification (PyPI)
- [ ] Basic functionality verification
- [ ] User notification
- [ ] Feedback collection

---

## 📅 Timeline (Option A - Recommended)

| Date | Task | Owner | Status |
|------|------|-------|--------|
| 03-21 (Sat) | F001 PyPI Release | Friday | ⏳ |
| 03-22 (Sun) | F002 + F003 UX Improvements | Friday | ⏳ |
| 03-23 (Mon) | F004 Importance Scoring | Friday | ⏳ |
| 03-24 (Tue) | Testing + Documentation | Friday | ⏳ |
| 03-25 (Wed) | Release Verification | Peter + Friday | ⏳ |

---

## 🎉 Release Decision

**Please Peter Confirm**:

### 1. Iteration Option
- [ ] Option A: Lite Version (5 days, P0 features) ✅ (Recommended)
- [ ] Option B: Full Version (10 days, P0+P1)
- [ ] Option C: Phased (v0.8.0 + v0.8.1)

### 2. Release Scope
- [ ] F001 PyPI Release ✅
- [ ] F002 Error Friendliness ✅
- [ ] F003 Auto Configuration ✅
- [ ] F004 Importance Scoring ✅
- [ ] F101 Auto Rule Extraction ⏳
- [ ] F102 Memory Decay ⏳
- [ ] F103 CLI Visualization ⏳

### 3. Release Date
- [ ] 2026-03-25 (Option A) ✅
- [ ] 2026-03-30 (Option B)
- [ ] Other: ________

### 4. Release Confirmation
- [ ] Approve to start v0.8.0 iteration ⏳

---

**Reviewer**: Peter Cheng  
**Review Date**: 2026-03-20  
**Review Status**: ⏳ Pending

---

*Document Version: v1.0*  
*Created: 2026-03-20T15:05*  
*Status: Planning*
