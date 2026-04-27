# Memory Schema v1.0.2

**Version:** 1.0.2  
**Created:** 2026-03-25  
**Status:** 🔄 In Development  
**Component:** Memory System  

---

## 📋 Schema Definition

### Memory Class

```python
@dataclass
class Memory:
    """Memory representation with v1.0.2 enhancements"""
    
    # Core fields (existing)
    id: str
    content: str
    tags: List[str]
    
    # NEW: Priority & Critical Rule (v1.0.2)
    is_critical: bool = False  # Is this a critical rule?
    priority: int = 3  # 1-5 (5=critical, 3=normal, 1=low)
    
    # NEW: Confidence Scoring (v1.0.2)
    confidence: float = 0.5  # 0.0-1.0 (50% default for new memories)
    
    # NEW: Source Tracking (v1.0.2)
    source: str = 'inferred'  # 'user' | 'inferred' | 'system'
    
    # Metadata (existing)
    created_at: datetime = field(default_factory=datetime.now)
    reinforced_at: Optional[datetime] = None
    
    # NEW: Usage Tracking (v1.0.2)
    use_count: int = 0  # How many times used
    success_count: int = 0  # How many times successful
    flagged_for_review: bool = False  # Needs review?
    
    # Methods
    def reinforce(self, success: bool):
        """Reinforce memory based on outcome"""
        self.use_count += 1
        if success:
            self.success_count += 1
            self.confidence = min(1.0, self.confidence + 0.05)
        else:
            self.confidence = max(0.0, self.confidence - 0.2)
            self.flagged_for_review = True
        self.reinforced_at = datetime.now()
    
    def mark_critical(self):
        """Mark as critical rule"""
        self.is_critical = True
        self.priority = 5
        self.source = 'user'
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'content': self.content,
            'tags': self.tags,
            'is_critical': self.is_critical,
            'priority': self.priority,
            'confidence': self.confidence,
            'source': self.source,
            'created_at': self.created_at.isoformat(),
            'reinforced_at': self.reinforced_at.isoformat() if self.reinforced_at else None,
            'use_count': self.use_count,
            'success_count': self.success_count,
            'flagged_for_review': self.flagged_for_review,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Memory':
        """Create from dictionary (with backward compatibility)"""
        return cls(
            id=data['id'],
            content=data['content'],
            tags=data.get('tags', []),
            is_critical=data.get('is_critical', False),
            priority=data.get('priority', 3),
            confidence=data.get('confidence', 0.5),
            source=data.get('source', 'inferred'),
            created_at=datetime.fromisoformat(data['created_at']),
            reinforced_at=datetime.fromisoformat(data['reinforced_at']) if data.get('reinforced_at') else None,
            use_count=data.get('use_count', 0),
            success_count=data.get('success_count', 0),
            flagged_for_review=data.get('flagged_for_review', False),
        )
```

---

## 📊 Field Descriptions

### Core Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | str | - | Unique memory identifier |
| `content` | str | - | Memory content |
| `tags` | List[str] | [] | Memory tags |

### Priority Fields (NEW)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `is_critical` | bool | False | Is this a critical rule? |
| `priority` | int | 3 | Priority 1-5 (5=critical) |

**Priority Levels:**
- **5 (Critical):** User-instructed critical rules
- **4 (High):** Important user preferences
- **3 (Normal):** Default priority
- **2 (Low):** Inferred information
- **1 (Very Low):** System-generated, low importance

### Confidence Fields (NEW)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `confidence` | float | 0.5 | Confidence score 0.0-1.0 |

**Confidence Calculation:**
```
confidence = base_score + use_bonus + success_bonus - penalty

Where:
- base_score = 0.5 (50% for new memories)
- use_bonus = min(0.3, use_count * 0.01)
- success_bonus = min(0.2, success_rate * 0.2)
- penalty = failure_count * 0.1
```

**Confidence Levels:**
- **0.9-1.0 (Very High):** Highly reliable, no verification needed
- **0.8-0.9 (High):** Reliable, can be used confidently
- **0.6-0.8 (Medium):** Moderately reliable, use with caution
- **0.4-0.6 (Low):** Low reliability, verify before use
- **0.0-0.4 (Very Low):** Unreliable, must verify

### Source Fields (NEW)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `source` | str | 'inferred' | Memory source |

**Source Types:**
| Source | Priority | Auto-Verify | Description |
|--------|----------|-------------|-------------|
| `user` | 5 | No | Direct user instruction |
| `inferred` | 3 | Yes | Inferred from context |
| `system` | 1 | Yes | System-generated |

### Usage Tracking (NEW)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `use_count` | int | 0 | Times used |
| `success_count` | int | 0 | Times successful |
| `flagged_for_review` | bool | False | Needs review? |

---

## 🔄 Migration Plan

### Migration Script

```python
def migrate_to_v1_0_2():
    """Migrate all memories to v1.0.2 schema"""
    
    count = 0
    for memory in memory_system.all():
        # Add new fields with defaults
        if not hasattr(memory, 'is_critical'):
            memory.is_critical = False
            memory.priority = 3
            memory.confidence = 0.5
            memory.source = 'inferred'
            memory.use_count = 0
            memory.success_count = 0
            memory.flagged_for_review = False
        
        memory_system.save(memory)
        count += 1
    
    print(f"✅ Migrated {count} memories to v1.0.2 schema")
```

### Backward Compatibility

**Old Format:**
```json
{
  "id": "mem_001",
  "content": "User prefers English docs",
  "tags": ["preference", "documentation"],
  "created_at": "2026-03-24T10:00:00"
}
```

**New Format (v1.0.2):**
```json
{
  "id": "mem_001",
  "content": "User prefers English docs",
  "tags": ["preference", "documentation"],
  "created_at": "2026-03-24T10:00:00",
  "is_critical": false,
  "priority": 3,
  "confidence": 0.5,
  "source": "user",
  "use_count": 0,
  "success_count": 0,
  "flagged_for_review": false
}
```

**Migration Rules:**
1. Missing fields get default values
2. Old memories load without error
3. New fields saved on next update

---

## 🧪 Testing

### Unit Tests

```python
def test_memory_creation():
    memory = Memory(id="test", content="Test memory")
    assert memory.is_critical == False
    assert memory.priority == 3
    assert memory.confidence == 0.5
    assert memory.source == 'inferred'

def test_mark_critical():
    memory = Memory(id="test", content="Test")
    memory.mark_critical()
    assert memory.is_critical == True
    assert memory.priority == 5
    assert memory.source == 'user'

def test_reinforce_success():
    memory = Memory(id="test", content="Test", confidence=0.5)
    memory.reinforce(success=True)
    assert memory.use_count == 1
    assert memory.success_count == 1
    assert memory.confidence == 0.55

def test_reinforce_failure():
    memory = Memory(id="test", content="Test", confidence=0.5)
    memory.reinforce(success=False)
    assert memory.use_count == 1
    assert memory.success_count == 0
    assert memory.confidence == 0.3
    assert memory.flagged_for_review == True

def test_backward_compatibility():
    old_data = {
        'id': 'old',
        'content': 'Old memory',
        'tags': [],
        'created_at': '2026-03-24T10:00:00'
    }
    memory = Memory.from_dict(old_data)
    assert memory.confidence == 0.5  # Default
    assert memory.source == 'inferred'  # Default
```

---

## 📝 Usage Examples

### Mark Critical Rule

```python
# Create memory
memory = memory_system.create("Apache docs must be 100% English")

# Mark as critical
memory_system.mark_as_critical(memory.id)

# Verify
assert memory.is_critical == True
assert memory.priority == 5
assert memory.source == 'user'
```

### Pre-Action Check

```python
# Get critical rules before action
critical_rules = memory_system.get_critical_rules()

# Check for violations
for rule in critical_rules:
    if action_violates_rule(action, rule):
        raise CriticalRuleViolation(rule)
```

### Reinforce Memory

```python
# After successful action
memory.reinforce(success=True)
# confidence increases

# After failed action
memory.reinforce(success=False)
# confidence decreases, flagged for review
```

---

## 📊 Performance

### Benchmarks

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| **Create Memory** | <10ms | TBD | 📋 TODO |
| **Load Memory** | <5ms | TBD | 📋 TODO |
| **Save Memory** | <10ms | TBD | 📋 TODO |
| **Get Critical Rules** | <50ms | TBD | 📋 TODO |
| **Pre-Action Check** | <100ms | TBD | 📋 TODO |

---

## 📄 Related Documents

- [ITERATION_PLAN_v1.0.2.md](./ITERATION_PLAN_v1.0.2.md)
- [ISSUE_002_Memory_System_Improvement.md](./ISSUE_002_Memory_System_Improvement.md)
- [ARCHITECTURE_DECISION_001.md](./ARCHITECTURE_DECISION_001.md)

---

*Document Created: 2026-03-25T09:00+08:00*  
*Version: 1.0*  
*Status: 🔄 In Development*  
*Component: Memory System*  
*Target Release: v1.0.2*
