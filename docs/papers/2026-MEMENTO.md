# MEMENTO: Teaching LLMs to Manage Their Own Context

> **论文信息**
> - 标题: MEMENTO: Teaching LLMs to Manage Their Own Context
> - 作者: Vasilis Kontonis, Yuchen Zeng et al. (Microsoft Research)
> - 发布: arXiv 2026
> - 数据集: OPENMEMENTOS (228K traces)

---

## 核心贡献

> "我们教模型将推理分段成块，压缩每块为 memento，仅通过 memento 向前推理，减少上下文、KV cache 和计算。"

**关键结果**:
- KV cache 减少 ~2.5×
- AIME'26 准确率仅下降 2.6 pp (Qwen3-32B)
- 双信息流: memento 文本 + KV 状态

---

## 问题: 推理模型无组织能力

### 当前局限

| 问题 | 描述 |
|------|------|
| **扁平流** | 32K-token CoT 是扁平、无结构的流 |
| **无压缩** | 无机制标记值得保留的中间结果 |
| **等价成本** | 每个过去 token 在注意力窗口中等价 |
| **无丢弃** | 模型没学会如何丢弃 token |

---

## MEMENTO 方法

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMENTO Pipeline                          │
│                                                             │
│  推理分段:                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  T1 (思考块 1) → M1 (memento 1)                       │  │
│  │  T2 (思考块 2) → M2 (memento 2)                       │  │
│  │  ...                                                 │  │
│  │  Tn (思考块 n) → Mn (memento n) → Answer              │  │
│  │                                                       │  │
│  │  Memento = 最小记录 (结论 + 中间值 + 关键决策)          │  │
│  │  压缩比: ~5–20×                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  稀疏注意力:                                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  生成 memento 后:                                      │  │
│  │  • 掩码前导思考块                                      │  │
│  │  • 仅 attend 到过去 mementos + 当前块                  │  │
│  │  • KV cache 条目物理移除                               │  │
│  │                                                       │  │
│  │  锯齿状 KV 轨迹 (see Figure 1)                         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心创新

### 1. 双信息流

```
┌─────────────────────────────────────────────────────────────┐
│                    Dual Information Stream                   │
│                                                             │
│  显式通道: Memento 文本                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  压缩的总结文本                                        │  │
│  │  可读、可解释                                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                           +                                  │
│  隐式通道: Memento KV 状态                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  计算时完整块仍在上下文中                               │  │
│  │  KV 状态编码了块信息                                   │  │
│  │  掩码后仍保留隐式表示                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  验证: 移除隐式通道 → AIME'24 -15 pp                        │
└─────────────────────────────────────────────────────────────┘
```

### 2. In-Place 掩码

- 单一生成调用内
- 不重启生成
- KV cache 条目物理移除

### 3. Native Block Masking in vLLM

- 支持高效 RL rollouts
- 启用 RL fine-tuning 关闭准确率差距

---

## OPENMEMENTOS 数据集

### 构建管道

1. **LLM 边界评分**: 评分每个句子边界
2. **算法分段**: 优化边界选择
3. **迭代总结**: Judge-refined summarization

### 规模

- **228K** 推理轨迹
- 来源: OpenThoughts-v3
- 分段 + 注释中间总结

---

## 实验结果

### KV Cache 减少

| 模型 | Peak KV 减少 |
|------|-------------|
| Qwen3-8B | ~2× |
| Qwen3-32B | ~2.5× |
| Phi-4-r (14B) | ~2× |

### 准确率保持

| 模型 | 基准 | MEMENTO | 差距 |
|------|------|---------|------|
| Qwen3-32B | 75.2% | 72.6% | -2.6 pp |
| Qwen3-8B | Baseline | -6.3 pp | -6.3 pp |

### RL Fine-tuning

- RL 可关闭准确率差距
- vLLM 支持 RL + block masking

---

## 对 claw-mem 的启发

### v2.1.0 增强

| 功能 | 来源 | 优先级 |
|------|------|--------|
| **自管理上下文** | MEMENTO | P0 |
| **分段压缩** | MEMENTO | P0 |
| **双信息流** | MEMENTO | P1 |
| **In-Place 掩码** | MEMENTO | P2 |

### 自管理记忆

```python
# claw-mem v2.1.0
class SelfManagingMemory:
    """自管理记忆系统"""
    
    def __init__(self, compression_ratio: int = 10):
        self.ratio = compression_ratio
        self.blocks = []
        self.mementos = []
        self.kv_states = {}  # 隐式通道
    
    def add_reasoning_block(self, block):
        """添加推理块"""
        # 生成 memento
        memento = self._compress(block)
        
        # 存储显式通道
        self.mementos.append(memento)
        
        # 存储隐式通道 (KV 状态)
        self.kv_states[len(self.mementos)] = self._extract_kv(block)
        
        # 掩码原块
        self._mask_block(block)
    
    def retrieve_for_reasoning(self, query):
        """检索用于推理"""
        # 显式: memento 文本
        explicit = self.mementos
        
        # 隐式: KV 状态 (如果可用)
        implicit = [self.kv_states[i] for i in range(len(self.mementos))]
        
        return explicit, implicit
    
    def _compress(self, block):
        """压缩为 memento"""
        # 最小记录: 结论 + 中间值 + 关键决策
        return {
            "conclusion": block.conclusion,
            "intermediate_values": block.key_values,
            "decisions": block.decisions
        }
```

---

## 对 claw-rl 的启发

### RL 优化压缩

```python
# claw-rl v2.2.0
class MementoRLTrainer:
    """Memento RL 训练器"""
    
    def __init__(self, model):
        self.model = model
    
    def train_with_block_masking(self, traces):
        """带 block masking 的 RL 训练"""
        for trace in traces:
            # 生成推理
            blocks = self._segment(trace)
            
            # 压缩为 mementos
            mementos = [self._compress(b) for b in blocks]
            
            # RL 优化: 准确率 + 压缩质量
            reward = self._compute_reward(
                accuracy=trace.accuracy,
                compression_ratio=len(mementos) / len(trace)
            )
            
            # 更新模型
            self._update(reward)
```

---

## 关键引用

- Kontonis & Zeng et al. (2026). *MEMENTO*.
- Film reference: Christopher Nolan's Memento (2000)

---

## 总结

**MEMENTO 的核心贡献**:
1. **自管理上下文**: 模型学会压缩自己的推理
2. **分段压缩**: 思考块 → memento
3. **双信息流**: 显式文本 + 隐式 KV 状态
4. **In-Place 掩码**: 单一生成调用内
5. **OPENMEMENTOS**: 228K 公开数据集

**对 Project Neo 的意义**:
- claw-mem: 自管理记忆 + 分段压缩
- claw-rl: RL 优化压缩质量
