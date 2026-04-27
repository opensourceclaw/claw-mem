# Selective Memory for Artificial Intelligence: Write-Time Gating with Hierarchical Archiving

> **论文信息**
> - 标题: Selective Memory for Artificial Intelligence: Write-Time Gating with Hierarchical Archiving
> - 作者: Oliver Zahn, Simran Chana et al. (Independent, Cambridge)
> - 发布: arXiv:2603.15994v1, 2026-03-16

---

## 核心贡献

> "我们引入写时门控，使用复合显著性分数过滤传入知识对象，同时维护版本链保留先前状态。"

**关键结果**:
- 写时门控: **100%** 准确率
- 无门控存储: 13%
- 8:1 干扰比: 写时门控 100% vs Self-RAG 0%

---

## 问题: 现有记忆架构的局限

### 两种极端

| 方法 | 问题 |
|------|------|
| **RAG** | 无差别存储所有内容，噪声累积 |
| **参数记忆** | 压缩到权重，无法选择性更新 |

### 神经记忆模块

- 连续权重矩阵，非离散可寻址单元
- 无法删除特定项
- 无来源追溯

---

## 生物记忆启发

### 两个原则

| 原则 | 生物机制 | AI 实现 |
|------|----------|---------|
| **选择性编码** | 海马体门控巩固 | 显著性门控 |
| **归档而非删除** | 降低可访问性 | 层次化归档 + 版本链 |

---

## Write-Time Gating 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Write-Time Gating                         │
│                                                             │
│  显著性评分:                                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  salience = f(source_reputation, novelty, reliability) │  │
│  │                                                       │  │
│  │  • Source Reputation: 来源信誉                         │  │
│  │  • Novelty: 新颖性                                     │  │
│  │  • Reliability: 可靠性                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  写时门控:                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  if salience > threshold:                             │  │
│  │      store in active_memory                           │  │
│  │  else:                                                │  │
│  │      archive in cold_storage                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  版本链:                                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  新信息 → 创建取代链接 → 保留先前状态                    │  │
│  │                                                       │  │
│  │  CEO_A ←[SUPERSEDES]─ CEO_B                           │  │
│  │                                                       │  │
│  │  可查询历史状态                                         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心创新

### 1. 复合显著性评分

**无需 Oracle 标签**:
- 来源信誉
- 新颖性
- 可靠性

### 2. 写时门控 vs 读时过滤

| 方法 | 时机 | 问题 |
|------|------|------|
| **Self-RAG** | 读时 | 底层存储仍累积噪声 |
| **Write Gating** | 写时 | 阻止低质量内容进入 |

### 3. 层次化归档

- 低于阈值 → 冷存储
- 不丢弃，保留未来可能价值
- 支持时间查询

---

## 实验结果

### 准确率对比

| 方法 | 准确率 |
|------|--------|
| **Write Gating** | **100%** |
| Ungated | 13.3% |
| Self-RAG | 93.8% |

### 干扰比扩展

| 干扰比 | Write Gating | Self-RAG | Ungated |
|--------|--------------|----------|---------|
| 1:1 | 100% | 93% | 13% |
| 4:1 | 100% | ~50% | 0% |
| **8:1** | **100%** | **0%** | **0%** |

### 新领域验证

| 数据集 | 写时门控优势 |
|--------|--------------|
| Wikipedia | +25pp |
| arXiv (post-cutoff) | +48pp |
| 药理学数据 | +65pp |

---

## 对 claw-mem 的启发

### v2.1.0 增强

| 功能 | 来源 | 优先级 |
|------|------|--------|
| **写时门控** | Selective Memory | P0 |
| **显著性评分** | Selective Memory | P0 |
| **版本链** | Selective Memory | P0 |
| **层次化归档** | Selective Memory | P1 |

### 选择性记忆系统

```python
# claw-mem v2.1.0
class SelectiveMemory:
    """选择性记忆系统"""
    
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.active_memory = ActiveMemory()
        self.cold_storage = ColdStorage()
        self.version_chains = VersionChains()
    
    def compute_salience(self, item):
        """计算显著性"""
        score = (
            0.4 * self._source_reputation(item.source) +
            0.3 * self._novelty(item) +
            0.3 * self._reliability(item.source)
        )
        return score
    
    def write(self, item):
        """写时门控"""
        salience = self.compute_salience(item)
        
        if salience >= self.threshold:
            # 检查是否有取代关系
            existing = self.active_memory.find_related(item)
            if existing:
                # 创建版本链
                self.version_chains.add_link(
                    new=item,
                    old=existing,
                    type="SUPERSEDES"
                )
            
            # 存储到活跃记忆
            self.active_memory.store(item)
        else:
            # 归档到冷存储
            self.cold_storage.archive(item)
    
    def query_temporal(self, concept, time):
        """时间查询"""
        return self.version_chains.get_state(concept, time)
```

---

## 对 neoclaw 的启发

### 高风险领域验证

```python
# neoclaw v2.1.0
class HighStakesVerifier:
    """高风险领域验证器"""
    
    def __init__(self, confidence_threshold: float = 0.95):
        self.threshold = confidence_threshold
        self.memory = SelectiveMemory()
    
    def verify(self, claim):
        """多路径验证"""
        # 从活跃记忆检索
        sources = self.memory.retrieve(claim)
        
        # 多路径交叉验证
        confidence = self._cross_validate(sources)
        
        if confidence >= self.threshold:
            return VerifiedResult(claim, sources, confidence)
        else:
            return UnverifiedResult(claim, confidence)
```

---

## 关键引用

- Zahn & Chana et al. (2026). *Selective Memory*.
- Titans (2024). *Test-time Memorization*.
- Self-RAG (2024). *Read-time Filtering*.

---

## 总结

**Selective Memory 的核心贡献**:
1. **写时门控**: 阻止低质量内容进入
2. **显著性评分**: 复合分数无需 Oracle
3. **版本链**: 归档而非删除
4. **渐进鲁棒性**: 8:1 干扰比下 100%

**对 Project Neo 的意义**:
- claw-mem: 写时门控 + 版本链
- neoclaw: 高风险领域验证
