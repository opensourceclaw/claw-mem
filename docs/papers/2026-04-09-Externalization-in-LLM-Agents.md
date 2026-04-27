# Externalization in LLM Agents: Memory Externalization

> **论文信息**
> - 标题: Externalization in LLM Agents: A Unified Review
> - 发布: arXiv:2604.08224v1, 2026-04-09
> - 本文档聚焦: Memory Externalization (状态外部化)

---

## Memory Externalization 核心概念

### 定义

> "Memory systems externalize an agent's state across time and convert long-horizon continuity into selective retrieval."

**核心转换**: **回忆 → 识别**

- Agent 不再需要从潜在权重重新生成过去知识
- 而是从持久、可搜索的存储中检索

### 解决的问题

**连续性问题 (Continuity Problem)**:
- LLM 上下文窗口有限
- 会话记忆弱或不存在
- 累积知识需要跨会话持久化

### 外部化的内容

| 内容类型 | 描述 | 示例 |
|----------|------|------|
| **User Preferences** | 用户偏好 | 语言风格、输出格式 |
| **Prior Trajectories** | 先前轨迹 | 任务执行历史 |
| **Resolved Ambiguities** | 已解决的歧义 | 用户澄清记录 |
| **Domain Facts** | 领域事实 | 项目约定、业务规则 |

---

## Memory 架构演进

### 四代架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory 架构演进                           │
│                                                             │
│  Gen 1: Monolithic Context                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  单一上下文窗口，所有历史在 prompt 中                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  Gen 2: Context + Retrieval Storage                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  RAG: 动态检索外部文档注入上下文                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  Gen 3: Hierarchical Memory + Orchestration                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  分层记忆: Working + Episodic + Semantic             │   │
│  │  + 编排层管理检索和压缩                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  Gen 4: Adaptive Memory Systems                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  自适应: 根据任务动态选择记忆策略                       │   │
│  │  + 学习用户模式                                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 代表性系统

| 系统 | 核心创新 | 论文 |
|------|----------|------|
| **RAG** | 检索增强生成 | Lewis et al., 2020 |
| **MemGPT** | OS 分页式记忆管理 | Packer et al., 2023 |
| **Generative Agents** | 反思式分层记忆 | Park et al., 2023 |
| **GAM** | 通用 Agent 记忆 | Chhikara et al., 2025 |

---

## Memory as Cognitive Artifact

### 认知工件视角

**购物清单类比**:
- 不扩展生物记忆容量
- 将**回忆问题**（"我需要买什么？"）转换为**识别问题**（"看到物品时认出需要它"）

**对 Agent Memory 的含义**:
- Memory 不是"更大的存储"
- 而是"更好的问题转换"

### 关键设计原则

1. **选择性检索** - 不是所有历史都相关
2. **分层抽象** - 原始轨迹 → 压缩摘要 → 抽象规则
3. **持久化** - 跨会话存在
4. **可检查** - 用户可审计

---

## Harness Era 的 Memory 需求

### 与前两代的对比

| Era | Memory 特征 | 局限 |
|-----|-------------|------|
| **Weights** | 无显式记忆 | 依赖模型内部 |
| **Context** | 上下文窗口 | 有限、短暂、噪声敏感 |
| **Harness** | 外部化记忆系统 | 需要检索策略、压缩、编排 |

### Harness Era 的关键能力

1. **Experience Store** - 存储完整执行轨迹
2. **Selective Retrieval** - 智能检索相关记忆
3. **Memory Compression** - 语义压缩历史
4. **Cross-Session Persistence** - 跨会话持久化
5. **Knowledge Sedimentation** - 知识沉淀

---

## 对 claw-mem 的启发

### v2.1.0 增强

| 功能 | 来源 | 实现建议 |
|------|------|----------|
| **Experience Store** | Meta-Harness | 存储代码、分数、执行轨迹 |
| **三层上下文** | SemaClaw | Working + External + Persona |
| **来源追踪** | SAFEHARNESS | 所有外部内容的 provenance |
| **知识沉淀** | SemaClaw | Wiki-based 知识基础设施 |

### 架构建议

```python
# claw-mem v2.1.0 架构
class MemoryManager:
    """
    三层上下文架构
    """
    def __init__(self):
        # Layer 1: 压缩工作记忆
        self.working_memory = WorkingMemory(
            max_tokens=8000,
            compression_strategy="semantic"
        )
        
        # Layer 2: 检索外部记忆
        self.external_memory = ExternalMemory(
            retriever=HybridRetriever(
                semantic_weight=0.5,
                recency_weight=0.3,
                importance_weight=0.2
            ),
            store=VectorStore()
        )
        
        # Layer 3: 人格分区
        self.persona_partition = PersonaPartition(
            soul_file="SOUL.md",
            user_file="USER.md"
        )
        
        # Experience Store (Meta-Harness 启发)
        self.experience_store = ExperienceStore(
            store_code=True,
            store_scores=True,
            store_traces=True
        )
```

### 关键接口

```python
# 来源追踪 (SAFEHARNESS 启发)
@dataclass
class MemoryEntry:
    content: str
    source: Provenance  # 来源追踪
    timestamp: datetime
    importance: float
    tags: List[str]

@dataclass
class Provenance:
    origin: str  # "user" | "agent" | "tool" | "retrieval"
    source_id: str
    confidence: float
```

---

## 与其他模块的交互

### Memory ↔ Skills

- **竞争**: 记忆扩展 vs 技能加载竞争上下文预算
- **协作**: 技能执行生成轨迹 → 后续成为记忆

### Memory ↔ Protocols

- 记忆检索影响协议路径选择
- 协议定义记忆访问接口

### Memory ↔ Harness

- Harness 仲裁记忆检索策略
- Harness 管理上下文预算

---

## 实现路线图

### Phase 1: 基础增强 (v2.1.0)

- [ ] Experience Store 实现
- [ ] 来源追踪 (Provenance)
- [ ] 三层上下文架构

### Phase 2: 智能检索 (v2.2.0)

- [ ] Hybrid Retriever (语义 + 时间 + 重要性)
- [ ] 自适应检索策略
- [ ] 检索质量评估

### Phase 3: 知识沉淀 (v3.0.0)

- [ ] Wiki-based 知识基础设施
- [ ] 知识图谱构建
- [ ] 模式挖掘

---

## 关键引用

- Lewis et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*.
- Packer et al. (2023). *MemGPT: Towards LLMs as Operating Systems*.
- Park et al. (2023). *Generative Agents: Interactive Simulacra of Human Behavior*.
- Norman, D. A. (1993). *Things That Make Us Smart*.

---

## 总结

**Memory Externalization 的本质**:
- 不是"更大的存储"
- 而是"更好的问题转换"（回忆 → 识别）

**claw-mem 的定位**:
- 作为 neoclaw 的 Memory 外部化层
- 提供跨会话状态持久化
- 支持选择性检索和知识沉淀
