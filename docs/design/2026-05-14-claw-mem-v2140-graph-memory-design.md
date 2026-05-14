# claw-mem v2.14.0 — 图结构记忆详细设计

**版本**: v1.0
**日期**: 2026-05-14
**作者**: Jarvis
**状态**: 设计完成

---

## 1. 设计概览

从当前向量存储升级为四正交图 + 双层结构 + 遗忘控制。

### 1.1 模块总览

```
claw-mem v2.14.0:
├── MultiGraphMemory (MAGMA 四正交图)
│   ├── SemanticGraph   — 语义相似
│   ├── TemporalGraph   — 时间先后
│   ├── CausalGraph     — 因果依赖
│   └── EntityGraph     — 实体关联
├── DualLayerMemory (GAM 双层)
│   ├── EventProgressionGraph — 当前对话流
│   └── TopicAssociativeNetwork — 长期主题网
├── DecayController (Oblivion 遗忘)
│   ├── DecayScheduler
│   ├── ReadGate (不确定性门控)
│   └── WriteGate (反馈驱动更新)
└── GroundTruthStore
    ├── Raw Episodes
    └── Extracted Facts
```

### 1.2 集成点

与现有 `EpisodicStorage` / `MemoryManager` 集成：
- MemoryManager.graph — MultiGraphMemory 实例
- MemoryManager._dual_layer — DualLayerMemory 实例
- MemoryManager.store() → 同时写入图结构
- MemoryManager.search() → 跨图查询

---

## 2. 类设计

### 2.1 MultiGraphMemory

```python
class MultiGraphMemory:
    """四正交图记忆架构 (MAGMA: Multi-Angle Graph Memory Architecture)."""

    def __init__(self):
        self.semantic = SemanticGraph()
        self.temporal = TemporalGraph()
        self.causal = CausalGraph()
        self.entity = EntityGraph()
        self._node_counter = 0

    def add_memory(self, memory: Dict) -> str:
        """Add a memory to all four graphs."""

    def query(self, query: str, top_k: int = 10) -> List[Dict]:
        """Cross-graph query with score fusion."""

    def remove_memory(self, memory_id: str) -> None:
        """Remove a memory from all graphs."""

    def get_stats(self) -> Dict:
        """Per-graph statistics."""
```

### 2.2 SemanticGraph

```python
class SemanticGraph:
    """Semantic similarity graph — edges based on text similarity."""

    def add_node(self, memory_id: str, text: str) -> None
    def add_edge(self, src: str, dst: str, weight: float) -> None
    def query(self, text: str, top_k: int = 10) -> List[Dict]
    def get_neighbors(self, node_id: str, depth: int = 1) -> List[str]

class TemporalGraph:
    """Temporal ordering graph — edges based on chronological order."""

    def add_node(self, memory_id: str, timestamp: float) -> None
    def get_before(self, timestamp: float, limit: int = 10) -> List[str]
    def get_after(self, timestamp: float, limit: int = 10) -> List[str]
    def get_range(self, start: float, end: float) -> List[str]

class CausalGraph:
    """Causal dependency graph — edges based on cause-effect relations."""

    def add_node(self, memory_id: str) -> None
    def add_causal_link(self, cause: str, effect: str) -> None
    def get_causes(self, node_id: str) -> List[str]
    def get_effects(self, node_id: str) -> List[str]

class EntityGraph:
    """Entity association graph — edges based on shared entities."""

    def add_node(self, memory_id: str, entities: List[str]) -> None
    def get_by_entity(self, entity: str) -> List[str]
    def get_shared_entities(self, id1: str, id2: str) -> List[str]
```

### 2.3 DualLayerMemory

```python
class DualLayerMemory:
    """GAM: Graph-Augmented Memory — double-layer memory architecture."""

    def __init__(self):
        self.event_graph = EventProgressionGraph()   # 当前对话流
        self.topic_net = TopicAssociativeNetwork()   # 长期主题网

    def add_interaction(self, text: str, session_id: str) -> None
    def build_context(self, session_id: str, limit: int = 10) -> List[Dict]
    def get_related_topics(self, topic: str, limit: int = 5) -> List[str]
    def merge_sessions(self, by_topic: bool = True) -> None
```

### 2.4 DecayController

```python
class DecayController:
    """Oblivion: memory decay and forgetting control."""

    def __init__(self, decay_rate: float = 0.1, decay_period: int = 86400):
        self.decay_rate = decay_rate
        self._decay_schedule: Dict[str, float] = {}

    def apply_decay(self, memories: List[Dict]) -> List[Dict]:
        """Apply Ebbinghaus-style decay to memories."""

    def get_accessibility(self, memory_id: str, last_access: float) -> float:
        """Compute memory accessibility score (0-1)."""

    def should_forget(self, memory_id: str, threshold: float = 0.1) -> bool:
        """Determine if memory should be forgotten."""

class ReadGate:
    """Uncertainty-gated retrieval."""

    def filter(self, results: List[Dict], threshold: float = 0.3) -> List[Dict]:
        """Filter results below confidence threshold."""

class WriteGate:
    """Feedback-driven write control."""

    def should_store(self, content: str, feedback: Optional[float] = None) -> bool:
        """Decide whether to store based on content significance."""
```

### 2.5 GroundTruthStore

```python
class GroundTruthStore:
    """Raw episodic storage with extracted facts."""

    def __init__(self):
        self._episodes: List[Dict] = []
        self._facts: List[Dict] = []

    def store_episode(self, text: str, metadata: Dict) -> str:
        """Store raw conversation as ground truth."""

    def store_fact(self, fact: str, source_episode_id: str) -> str:
        """Extract and store a fact."""

    def extract_facts(self, text: str) -> List[str]:
        """Extract facts from text using keyword patterns."""

    def verify_fact(self, fact_id: str) -> bool:
        """Verify a fact against stored episodes."""
```

---

## 3. 数据结构

```python
# 图节点 (内存于内存中)
GraphNode = {
    "id": str,           # UUID
    "text": str,         # 记忆文本
    "timestamp": float,  # Unix时间戳
    "accessibility": float, # 可访问性 (0-1)
    "entities": List[str],  # 实体列表
}

# 图边 (存储于邻接表)
GraphEdge = {
    "src": str,
    "dst": str,
    "weight": float,     # 边权重
    "type": str,         # "semantic" | "temporal" | "causal" | "entity"
}
```

---

## 4. 算法

### 4.1 跨图查询融合

```
MultiGraphMemory.query(query, top_k):
1. results_semantic = semantic.query(query, top_k)
2. results_temporal = temporal.get_before(now, top_k)
3. results_entity = entity.get_by_entities(extract_entities(query), top_k)
4. fused = weighted_merge(results, weights={semantic: 0.5, temporal: 0.3, entity: 0.2})
5. return fused[:top_k]
```

### 4.2 Ebbinghaus 遗忘曲线

```
DecayController.apply_decay(memories):
对于每个 memory:
  days = (now - memory.timestamp) / 86400
  accessibility = exp(-days * decay_rate)
  memory.accessibility = accessibility
  if accessibility < forget_threshold: mark_for_deletion()
```

### 4.3 事实提取

```
GroundTruthStore.extract_facts(text):
1. 分割文本为句子
2. 对每个句子匹配模式:
   - "X is Y" → 实体关系
   - "X did Y" → 事件记录
   - 数字+单位 → 度量事实
3. 返回提取的事实列表
```

---

## 5. 文件结构

```
src/claw_mem/
├── graph/
│   ├── __init__.py
│   ├── multi_graph.py          ← MultiGraphMemory
│   ├── semantic_graph.py       ← SemanticGraph
│   ├── temporal_graph.py       ← TemporalGraph
│   ├── causal_graph.py         ← CausalGraph
│   ├── entity_graph.py         ← EntityGraph
│   └── dual_layer.py           ← DualLayerMemory + GAM
├── decay.py                    ← DecayController + ReadGate + WriteGate
├── ground_truth.py             ← GroundTruthStore
└── storage/
    └── (现有)
```

---

## 6. 测试计划

| 模块 | 测试数 |
|------|:------:|
| MultiGraphMemory | 5 |
| SemanticGraph | 3 |
| TemporalGraph | 3 |
| CausalGraph | 2 |
| EntityGraph | 3 |
| DualLayerMemory | 3 |
| DecayController | 4 |
| GroundTruthStore | 4 |
| **总计** | **27** |
