# Write-Time Gating API

## WriteTimeGating

Write-time gating main controller.

### Constructor

```python
WriteTimeGating(
    threshold: float = 0.6,
    active_memory: Optional[Storage] = None,
    cold_storage: Optional[Storage] = None
)
```

**Parameters**:
- `threshold`: Salience threshold, default 0.6
- `active_memory`: Active memory storage
- `cold_storage`: Cold storage

### Methods

#### write(item: Dict) -> GatingResult

Write memory item.

**Parameters**:
- `item`: Memory item dictionary, containing:
  - `content`: Content (required)
  - `source`: Source (user/agent/system/external)
  - `context`: Context (optional)
  - `verified`: Verification status (optional)

**Returns**: `GatingResult`

```python
result = gating.write({
    'content': 'Important decision',
    'source': 'user',
    'context': {'topic': 'tech'}
})

print(result.stored)  # True
print(result.tier)    # 'active' or 'cold'
print(result.salience_score)  # 0.85
```

#### get_stats() -> Dict

Get statistics.

```python
stats = gating.get_stats()
# {
#     'active_count': 10,
#     'cold_count': 5,
#     'version_chain_length': 15,
#     'threshold': 0.6
# }
```

#### promote(item_id: str, target_tier: str = 'active') -> bool

Promote memory item to higher tier.

**Parameters**:
- `item_id`: Memory item ID
- `target_tier`: Target tier ('active' or 'cold')

**Returns**: Success status

#### get_version_history(item_id: str) -> List[Dict]

Get version history for a memory item.

**Parameters**:
- `item_id`: Memory item ID

**Returns**: List of version entries

---

## SalienceScorer

Salience scorer.

### Methods

#### compute(item: Dict) -> float

Compute salience score.

**Parameters**:
- `item`: Memory item dictionary

**Returns**: 0.0 ~ 1.0

```python
scorer = SalienceScorer()
score = scorer.compute({
    'content': 'Important decision',
    'source': 'user',
    'verified': True
})
# score: 0.85
```

#### compute_source_reputation(source: str) -> float

Compute source reputation score.

**Parameters**:
- `source`: Source (user/agent/system/external)

**Returns**: 0.0 ~ 1.0

#### compute_novelty(content: str) -> float

Compute novelty score based on recent memories.

**Parameters**:
- `content`: Memory content

**Returns**: 0.0 ~ 1.0

#### compute_reliability(item: Dict) -> float

Compute reliability score.

**Parameters**:
- `item`: Memory item dictionary

**Returns**: 0.0 ~ 1.0

---

## GatingResult

Gating result data class.

### Attributes

- `stored: bool` - Whether stored
- `tier: str` - Storage tier ('active' / 'cold')
- `salience_score: float` - Salience score
- `reason: Optional[str]` - Reason explanation
- `item_id: Optional[str]` - Memory item ID (if stored)
- `version: int` - Version number

---

## Storage Classes

### InMemoryStorage

In-memory storage for active memories.

```python
storage = InMemoryStorage()
storage.store({'content': 'test'})
count = storage.count()
items = storage.list()
```

### DiskStorage

Disk-based storage for cold memories.

```python
storage = DiskStorage(base_dir='./cold_storage')
storage.store({'content': 'test'})
count = storage.count()
items = storage.list()
```

---

## Usage Examples

### Basic Usage

```python
from claw_mem import MemoryManager

# Create manager with gating enabled
manager = MemoryManager(enable_gating=True, gating_threshold=0.6)

# Write memory through gating
result = manager.gating.write({
    'content': 'Important decision: Use Python',
    'source': 'user',
    'context': {'topic': 'tech'},
    'verified': True
})

# Check result
if result.stored:
    print(f"Stored to {result.tier} tier with score {result.salience_score}")

# Get statistics
stats = manager.get_gating_stats()
print(f"Active: {stats['active_count']}, Cold: {stats['cold_count']}")
```

### Custom Threshold

```python
# High threshold - only very important memories go to active
manager = MemoryManager(enable_gating=True, gating_threshold=0.8)
```

### Manual Tier Promotion

```python
# Promote a memory to active tier
success = manager.gating.promote(item_id='abc123', target_tier='active')
```

---

## GatingFilter (v2.3.0)

基于 ImportanceScorer 的门控过滤器.

### Constructor

```python
GatingFilter(
    scorer: Optional[Any] = None,
    threshold: float = 1.0,
    custom_score_func: Optional[Callable[[Dict], float]] = None
)
```

**Parameters**:
- `scorer`: ImportanceScorer 实例
- `threshold`: 存储阈值 (默认 1.0)
- `custom_score_func`: 自定义评分函数

### Methods

#### should_store(memory: Dict) -> GatingFilterResult

判断是否应该存储.

```python
from claw_mem.gating import GatingFilter

filter = GatingFilter(threshold=1.0)

result = filter.should_store({
    'memory_type': 'semantic',
    'access_count': 5,
    'content': 'Important fact',
    'source': 'user'
})

print(result.should_store)  # True/False
print(result.importance_score)  # 1.5
print(result.reason)  # "High importance (1.50 >= 1.00): type=semantic, source=user"
```

#### set_threshold(threshold: float)

设置新阈值.

```python
filter.set_threshold(1.5)
```

---

## AdaptiveThreshold (v2.3.0)

自适应阈值 - 根据记忆数量动态调整.

### Constructor

```python
AdaptiveThreshold(
    base_threshold: float = 1.0,
    min_threshold: float = 0.5,
    max_threshold: float = 1.5,
    memory_capacity: int = 1000,
    scale_factor: float = 0.5
)
```

### Methods

#### get_threshold(current_memory_count: int) -> float

根据当前记忆数量计算阈值.

```python
from claw_mem.gating import AdaptiveThreshold

adapter = AdaptiveThreshold(
    base_threshold=1.0,
    min_threshold=0.5,
    max_threshold=1.5,
    memory_capacity=1000
)

# 记忆少时,阈值较低
threshold = adapter.get_threshold(100)  # ~0.6

# 记忆多时,阈值较高
threshold = adapter.get_threshold(900)  # ~1.3
```

#### get_stats(current_memory_count: int) -> Dict

获取统计信息.

```python
stats = adapter.get_stats(500)
# {
#     'current_count': 500,
#     'capacity': 1000,
#     'usage_ratio': 0.5,
#     'current_threshold': 1.0,
#     'base_threshold': 1.0,
#     'min_threshold': 0.5,
#     'max_threshold': 1.5
# }
```

---

## Complete Example (v2.3.0)

```python
from claw_mem import MemoryManager
from claw_mem.gating import GatingFilter, AdaptiveThreshold

# 创建 MemoryManager,启用写时门控
mm = MemoryManager(
    workspace='./workspace',
    enable_gating=True,
    gating_threshold=0.6
)

# 存储记忆 - 自动门控判断
mm.store('User preference: Dark mode', memory_type='semantic')
mm.store('Casual chat message', memory_type='episodic')

# 获取门控统计
stats = mm.get_gating_stats()
print(f"Active: {stats['active_count']}, Cold: {stats['cold_count']}")

# 使用 GatingFilter 单独判断
filter = GatingFilter(threshold=1.0)
result = filter.should_store({
    'memory_type': 'semantic',
    'access_count': 10,
    'content': 'Important information'
})
print(f"Should store: {result.should_store}")

# 使用自适应阈值
adapter = AdaptiveThreshold(base_threshold=1.0)
dynamic_threshold = adapter.get_threshold(current_memory_count=800)
print(f"Dynamic threshold: {dynamic_threshold}")
```
