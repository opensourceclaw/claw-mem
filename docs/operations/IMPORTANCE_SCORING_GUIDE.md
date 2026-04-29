# Memory Importance Scoring Guide

**Version**: 0.8.0  
**Feature**: F003 - Memory Importance Scoring  
**Last Updated**: 2026-03-20

---

## 🎯 Overview

claw-mem v0.8.0 introduces **memory importance scoring**, enabling smarter retrieval and context injection.

---

## 📊 Scoring Formula

```
Importance Score = Base (1.0) + Type Weight + Frequency Weight + Recency Weight

Maximum Score: 2.0
```

### Components

| Component | Weight Range | Description |
|-----------|--------------|-------------|
| **Base Score** | 1.0 | Every memory starts with 1.0 |
| **Type Weight** | 0.0 - 0.5 | Semantic > Procedural > Episodic |
| **Frequency Weight** | 0.0 - 0.3 | More accesses = higher weight |
| **Recency Weight** | 0.0 - 0.2 | Recent accesses = higher weight |

---

## 🏷️ Type Weights

| Memory Type | Weight | Rationale |
|-------------|--------|-----------|
| **Semantic** | +0.5 | Core facts (permanent, critical) |
| **Procedural** | +0.3 | Skills and processes (stable) |
| **Episodic** | +0.0 | Daily conversations (expire over time) |

---

## 📈 Frequency Weights

| Access Count | Weight |
|--------------|--------|
| > 10 times | +0.3 |
| > 5 times | +0.2 |
| > 1 time | +0.1 |
| 1 time | +0.0 |

---

## 🕐 Recency Weights

| Days Since Access | Weight |
|-------------------|--------|
| < 7 days | +0.2 |
| < 30 days | +0.1 |
| > 30 days | +0.0 |

---

## 🎖️ Priority Levels

| Score Range | Label | Description |
|-------------|-------|-------------|
| **≥ 1.7** | 高 (High) | Critical memories, always prioritize |
| **1.3 - 1.7** | 中 (Medium) | Important memories, normal priority |
| **< 1.3** | 低 (Low) | Less important, may archive if episodic |

---

## 🚀 Usage Examples

### Example 1: Calculate Importance

```python
from claw_mem import ImportanceScorer
from datetime import datetime, timedelta

scorer = ImportanceScorer()

# High-priority memory (semantic + frequent + recent)
high_priority = {
    'memory_type': 'semantic',
    'access_count': 15,
    'accessed_at': datetime.now() - timedelta(days=1),
    'content': '用户偏好使用中文'
}

importance = scorer.calculate(high_priority)
print(f"Score: {importance.total_score:.2f}")
# Output: Score: 2.00

print(f"Priority: {scorer.get_importance_label(importance.total_score)}")
# Output: Priority: 高
```

---

### Example 2: Rank Memories

```python
from claw_mem import ImportanceScorer

scorer = ImportanceScorer()

memories = [
    {
        'memory_type': 'episodic',
        'access_count': 1,
        'accessed_at': datetime.now() - timedelta(days=60),
        'content': '用户询问天气'
    },
    {
        'memory_type': 'semantic',
        'access_count': 15,
        'accessed_at': datetime.now() - timedelta(days=1),
        'content': '用户偏好中文'
    }
]

# Sort by importance
ranked = scorer.rank_memories(memories)

for i, mem in enumerate(ranked, 1):
    imp = scorer.calculate(mem)
    print(f"{i}. [{scorer.get_importance_label(imp.total_score)}] {mem['content']}")

# Output:
# 1. [高] 用户偏好中文
# 2. [低] 用户询问天气
```

---

### Example 3: Filter High-Priority Memories

```python
from claw_mem import ImportanceScorer

scorer = ImportanceScorer()

# Get only high-priority memories (threshold: 1.5)
high_priority = scorer.filter_high_priority(
    memories,
    threshold=1.5,
    limit=10  # Max 10 results
)
```

---

### Example 4: Check if Should Archive

```python
from claw_mem import ImportanceScorer

scorer = ImportanceScorer()

# Low-priority episodic memory
old_memory = {
    'memory_type': 'episodic',
    'access_count': 1,
    'accessed_at': datetime.now() - timedelta(days=90),
    'content': '旧对话'
}

if scorer.should_archive(old_memory):
    print("✅ Should archive (low priority episodic)")
else:
    print("❌ Keep (still relevant)")
```

---

### Example 5: Explain Score

```python
from claw_mem import ImportanceScorer

scorer = ImportanceScorer()

memory = {
    'memory_type': 'semantic',
    'access_count': 15,
    'accessed_at': datetime.now() - timedelta(days=2),
    'content': '用户偏好'
}

explanation = scorer.explain_score(memory)
print(explanation)

# Output:
# 重要性评分:2.00/2.00
#   - 基础分:1.0
#   - 类型权重:0.5 (semantic)
#   - 频率权重:0.3 (访问 15 次)
#   - 新近度权重:0.2 (2 天前访问)
#
# 优先级:高
```

---

## 🔍 Integration with MemoryManager

### Automatic Ranking in Search

```python
from claw_mem import MemoryManager

mm = MemoryManager()

# Search automatically ranks by importance
results = mm.search("用户偏好")

# Results are sorted by importance (high to low)
for mem in results:
    print(f"[{mm.importance_scorer.get_importance_label(...)}] {mem['content']}")
```

### Disable Importance Ranking

```python
from claw_mem import MemoryManager

mm = MemoryManager()

# Disable importance ranking (raw keyword match order)
results = mm.retriever.search(
    query="用户偏好",
    episodic=mm.episodic,
    semantic=mm.semantic,
    procedural=mm.procedural,
    rank_by_importance=False  # Disable ranking
)
```

---

## 📊 Performance Impact

| Metric | Value |
|--------|-------|
| **Scoring Time** | <1ms per memory |
| **Sorting Overhead** | O(n log n) |
| **Memory Usage** | Negligible |
| **Impact on Search** | <10% latency increase |

---

## 🎯 Best Practices

### ✅ Do

```python
# Use importance scoring for context injection
high_priority = scorer.filter_high_priority(memories, threshold=1.5, limit=5)

# Explain scores to users
print(scorer.explain_score(memory))

# Archive low-priority episodic memories
if scorer.should_archive(memory):
    archive(memory)
```

### ❌ Don't

```python
# Don't ignore importance in large memory sets
all_memories = get_all_memories()  # May be slow

# Do filter first
important = scorer.filter_high_priority(all_memories, threshold=1.3)
```

---

## 📈 Real-World Examples

### Example 1: User Preferences (High Priority)

```python
preference = {
    'memory_type': 'semantic',
    'access_count': 50,
    'accessed_at': datetime.now() - timedelta(days=1),
    'content': '用户偏好使用中文交流'
}

# Score: 2.00 (High)
# - Base: 1.0
# - Type: +0.5 (semantic)
# - Frequency: +0.3 (>10 accesses)
# - Recency: +0.2 (<7 days)
```

---

### Example 2: Old Conversation (Low Priority)

```python
old_chat = {
    'memory_type': 'episodic',
    'access_count': 1,
    'accessed_at': datetime.now() - timedelta(days=90),
    'content': '用户询问了天气'
}

# Score: 1.00 (Low)
# - Base: 1.0
# - Type: +0.0 (episodic)
# - Frequency: +0.0 (1 access)
# - Recency: +0.0 (>30 days)
```

---

### Example 3: Technical Skill (Medium Priority)

```python
skill = {
    'memory_type': 'procedural',
    'access_count': 8,
    'accessed_at': datetime.now() - timedelta(days=15),
    'content': 'Python 部署流程'
}

# Score: 1.60 (Medium)
# - Base: 1.0
# - Type: +0.3 (procedural)
# - Frequency: +0.2 (>5 accesses)
# - Recency: +0.1 (<30 days)
```

---

## 🔧 Advanced Features

### Custom Weights

```python
from claw_mem.importance import ImportanceScorer

# Create scorer with custom weights
scorer = ImportanceScorer()
scorer.TYPE_WEIGHTS = {
    'semantic': 0.6,    # Increase semantic weight
    'procedural': 0.3,
    'episodic': 0.1,    # Give episodic some weight
}

scorer.FREQUENCY_THRESHOLDS = [
    (20, 0.3),  # Require more accesses for max weight
    (10, 0.2),
    (5, 0.1),
]
```

---

### Batch Scoring

```python
from claw_mem.importance import ImportanceScorer

scorer = ImportanceScorer()

# Score multiple memories at once
memories = [...]  # List of memory dicts
scored = [(mem, scorer.calculate(mem).total_score) for mem in memories]

# Sort by score
scored.sort(key=lambda x: x[1], reverse=True)
```

---

## 📚 API Reference

### ImportanceScorer Class

#### `calculate(memory)`

Calculate importance score for a memory.

**Parameters**:
- `memory` (dict): Memory with `memory_type`, `access_count`, `accessed_at`

**Returns**:
- `MemoryImportance`: Score details

---

#### `rank_memories(memories)`

Sort memories by importance (high to low).

**Parameters**:
- `memories` (list): List of memory dicts

**Returns**:
- `list`: Sorted memories

---

#### `filter_high_priority(memories, threshold=1.5, limit=None)`

Filter high-priority memories.

**Parameters**:
- `memories` (list): Memory list
- `threshold` (float): Minimum score (default: 1.5)
- `limit` (Optional[int]): Max results

**Returns**:
- `list`: High-priority memories

---

#### `should_archive(memory, threshold=0.3)`

Check if memory should be archived.

**Parameters**:
- `memory` (dict): Memory to check
- `threshold` (float): Archive threshold

**Returns**:
- `bool`: True if should archive

---

#### `get_importance_label(score)`

Get priority label for a score.

**Parameters**:
- `score` (float): Importance score

**Returns**:
- `str`: "高", "中", or "低"

---

#### `explain_score(memory)`

Explain why a memory has a certain score.

**Parameters**:
- `memory` (dict): Memory to explain

**Returns**:
- `str`: Human-readable explanation

---

## 🎉 Summary

**Memory importance scoring** makes claw-mem smarter:

- ✅ **Intelligent ranking** for search results
- ✅ **Prioritized context injection** for LLM
- ✅ **Automatic archiving** of low-priority memories
- ✅ **Transparent scoring** with explanations

**Example use case**:
```python
from claw_mem import MemoryManager

mm = MemoryManager()

# Search returns high-priority memories first
results = mm.search("用户偏好")

# Top results are most important/relevant
for mem in results[:5]:
    print(f"✅ {mem['content']}")
```

---

**Document Version**: 0.8.0  
**Last Updated**: 2026-03-20  
**Author**: Peter Cheng
