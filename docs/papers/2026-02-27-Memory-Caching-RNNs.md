# Memory Caching: RNNs with Growing Memory

> **论文信息**
> - 标题: Memory Caching: RNNs with Growing Memory
> - 作者: Ali Behrouz, Zeman Li et al. (Google Research)
> - 发布: arXiv:2602.24281v1, 2026-02-27

---

## 核心贡献

> "我们引入 Memory Caching，通过缓存记忆状态检查点，使 RNN 的有效记忆容量随序列长度增长。"

**关键结果**:
- 复杂度: O(NL) — RNN O(L) 和 Transformer O(L²) 之间
- 缩小 RNN 和 Transformer 在召回密集任务上的差距
- 灵活权衡记忆容量和计算成本

---

## 问题: 固定记忆的瓶颈

### Transformer vs. RNN

| 架构 | 记忆容量 | 复杂度 | 问题 |
|------|----------|--------|------|
| **Transformer** | O(L²) 增长 | O(L²) | 二次复杂度 |
| **RNN** | O(1) 固定 | O(L) | 召回密集任务欠佳 |

### RNN 的困境

- 固定容量压缩增长序列
- 被迫遗忘过去信息
- 长上下文和召回密集任务瓶颈

---

## Memory Caching 方法

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory Caching                            │
│                                                             │
│  序列分段:                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  x ∈ R^{L×d} → S(1), S(2), ..., S(N)                  │  │
│  │  每段大小 L(1), L(2), ..., L(N)                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  记忆压缩:                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  M(s)_t = f(M(s)_{t-1}; k_t, v_t)                     │  │
│  │                                                       │  │
│  │  每段结束时缓存: {M(1), M(2), ..., M(N)}               │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  聚合输出:                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  y_t = Agg({M(1), ..., M(s-1)}; M(s)_t; q_t)          │  │
│  │                                                       │  │
│  │  使用所有缓存记忆 + 当前在线记忆                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  复杂度: O(NL) — RNN O(L) 和 Transformer O(L²) 之间         │
└─────────────────────────────────────────────────────────────┘
```

---

## 四种聚合策略

### 1. Residual Memory

- 残差连接聚合缓存记忆

### 2. Gated Residual Memory

- 上下文感知门控机制
- 自适应选择相关记忆

### 3. Memory Soup

- 受 weight souping 启发
- 平均缓存记忆模块参数

### 4. Sparse Selective Caching (SSC)

- MoE 风格路由器
- 仅选择最上下文相关的缓存记忆
- 高效聚合

---

## 核心创新

### 1. 记忆检查点

- 缓存每段的压缩记忆状态
- 直接访问整个历史的压缩信息

### 2. 灵活权衡

```
O(L) ←────────────────→ O(L²)
  RNN    Memory Caching    Transformer
         (O(NL))
```

### 3. 架构无关

- 适用于 Linear Attention
- 适用于 Titans (deep memory)
- 适用于 SWLA, DLA

---

## 对 claw-mem 的启发

### v2.1.0 增强

| 功能 | 来源 | 优先级 |
|------|------|--------|
| **记忆缓存** | MC | P0 |
| **分段压缩** | MC | P0 |
| **稀疏选择性** | MC | P1 |
| **门控聚合** | MC | P1 |

### 缓存记忆系统

```python
# claw-mem v2.1.0
class CachedMemorySystem:
    """缓存记忆系统"""
    
    def __init__(self, segment_size: int = 1024):
        self.segment_size = segment_size
        self.cached_memories = []  # 缓存检查点
        self.online_memory = None   # 当前在线记忆
    
    def process(self, tokens):
        """处理序列"""
        # 分段
        segments = self._segment(tokens)
        
        for seg in segments:
            # 更新在线记忆
            self.online_memory = self._compress(seg)
            
            # 段结束时缓存
            if self._is_segment_end(seg):
                self.cached_memories.append(
                    self.online_memory.copy()
                )
    
    def retrieve(self, query):
        """检索"""
        # 聚合所有缓存记忆 + 在线记忆
        outputs = []
        
        # 缓存记忆
        for cached in self.cached_memories:
            outputs.append(cached(query))
        
        # 在线记忆
        outputs.append(self.online_memory(query))
        
        # 门控聚合
        return self._gated_aggregate(outputs)
    
    def _gated_aggregate(self, outputs):
        """门控聚合"""
        # 上下文感知门控
        gates = self._compute_gates(outputs)
        return sum(g * o for g, o in zip(gates, outputs))
```

---

## 对 claw-rl 的启发

### 稀疏选择性缓存

```python
# claw-rl v2.2.0
class SparseSelectiveCache:
    """稀疏选择性缓存"""
    
    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self.router = MoERouter()
    
    def select_memories(self, query, cached_memories):
        """选择相关记忆"""
        # MoE 风格路由
        scores = self.router.score(query, cached_memories)
        
        # 选择 top-k
        top_indices = scores.topk(self.top_k)
        
        return [cached_memories[i] for i in top_indices]
```

---

## 关键引用

- Behrouz & Li et al. (2026). *Memory Caching*.
- Titans (deep memory module)
- Linear Attention

---

## 总结

**Memory Caching 的核心贡献**:
1. **记忆检查点**: 缓存分段记忆状态
2. **灵活复杂度**: O(NL) 在 O(L) 和 O(L²) 之间
3. **四种聚合**: Residual, Gated, Soup, Sparse
4. **架构无关**: 适用于多种 RNN 变体

**对 Project Neo 的意义**:
- claw-mem: 缓存记忆系统
- claw-rl: 稀疏选择性缓存
