# Memory in the Age of AI Agents: A Survey

> **论文信息**
> - 标题: Memory in the Age of AI Agents: A Survey - Forms, Functions and Dynamics
> - 作者: Yuyang Hu, Shichun Liu et al. (NUS, Renmin Univ, Fudan, Peking Univ, etc.)
> - 发布: arXiv:2512.13564v2, 2026-01-13
> - GitHub: https://github.com/Shichun-Liu/Agent-Memory-Paper-List

---

## 核心贡献

> "我们从 Forms,Functions,Dynamics 三个统一视角审视 Agent 记忆,提供当前最全面的研究图景."

**三大视角**:
- **Forms**: Token-level, Parametric, Latent
- **Functions**: Factual, Experiential, Working
- **Dynamics**: Formation, Evolution, Retrieval

---

## 范围界定

### Agent Memory vs. 相关概念

| 概念 | 区别 |
|------|------|
| **LLM Memory** | LLM 内部记忆 vs. Agent 外部记忆系统 |
| **RAG** | 静态文档检索 vs. 动态记忆演化 |
| **Context Engineering** | 单次上下文优化 vs. 持久记忆管理 |

---

## Forms: 记忆的载体

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory Forms                              │
│                                                             │
│  Token-level Memory (1D → 2D → 3D):                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Flat (1D): 线性序列                                  │  │
│  │  Planar (2D): 二维结构 (如表格)                        │  │
│  │  Hierarchical (3D): 层次结构 (如树/图)                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Parametric Memory:                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Internal: 模型权重                                    │  │
│  │  External: 外部参数存储 (如 LoRA)                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Latent Memory:                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Generate: 动态生成                                    │  │
│  │  Reuse: 缓存重用                                       │  │
│  │  Transform: 变换压缩                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Functions: 记忆的功能

### 细粒度分类

| 功能 | 描述 | 子类型 |
|------|------|--------|
| **Factual Memory** | 事实知识 | User factual, Environment factual |
| **Experiential Memory** | 经验知识 | Case-based, Strategy-based, Skill-based, Hybrid |
| **Working Memory** | 工作记忆 | Single-turn, Multi-turn |

### 超越传统分类

> "传统的长/短期记忆分类已不足以捕捉当代 Agent 记忆系统的多样性和动态性."

---

## Dynamics: 记忆的动态

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory Dynamics                           │
│                                                             │
│  Formation (形成):                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  • Semantic Summarization (语义总结)                   │  │
│  │  • Knowledge Distillation (知识蒸馏)                   │  │
│  │  • Structured Construction (结构化构建)                │  │
│  │  • Latent Representation (潜在表示)                    │  │
│  │  • Parametric Internalization (参数内化)               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Evolution (演化):                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  • Consolidation (巩固)                               │  │
│  │  • Updating (更新)                                    │  │
│  │  • Forgetting (遗忘)                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Retrieval (检索):                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  • Retrieval Timing & Intent (时机和意图)              │  │
│  │  • Query Construction (查询构建)                       │  │
│  │  • Retrieval Strategies (检索策略)                     │  │
│  │  • Post-Retrieval Processing (后处理)                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 前沿方向

### 七大前沿

| 前沿 | 描述 |
|------|------|
| **Memory Generation** | 从检索到生成 |
| **Automated Management** | 自动化记忆管理 |
| **RL Integration** | RL 与记忆系统深度集成 |
| **Multimodal Memory** | 多模态记忆 |
| **Shared Memory** | 多 Agent 共享记忆 |
| **World Model** | 记忆用于世界模型 |
| **Trustworthy Memory** | 可信记忆 |

---

## 对 claw-mem 的启发

### v2.1.0 增强

| 功能 | 来源 | 优先级 |
|------|------|--------|
| **Forms 三分类** | Survey | P0 |
| **Functions 细粒度** | Survey | P0 |
| **Dynamics 三阶段** | Survey | P0 |
| **自动化管理** | Survey | P1 |
| **RL 集成** | Survey | P2 |

### 完整记忆系统

```python
# claw-mem v2.1.0
class AgentMemorySystem:
    """完整 Agent 记忆系统"""
    
    def __init__(self):
        # Forms
        self.token_memory = TokenLevelMemory()
        self.param_memory = ParametricMemory()
        self.latent_memory = LatentMemory()
        
        # Functions
        self.factual_memory = FactualMemory()
        self.experiential_memory = ExperientialMemory()
        self.working_memory = WorkingMemory()
        
        # Dynamics
        self.formation = MemoryFormation()
        self.evolution = MemoryEvolution()
        self.retrieval = MemoryRetrieval()
    
    # Formation
    def form(self, experience):
        """记忆形成"""
        # 语义总结
        summary = self.formation.summarize(experience)
        # 结构化构建
        structured = self.formation.structure(summary)
        # 存储
        self._store(structured)
    
    # Evolution
    def evolve(self, new_experience):
        """记忆演化"""
        # 巩固
        self.evolution.consolidate()
        # 更新
        self.evolution.update(new_experience)
        # 遗忘
        self.evolution.forget_outdated()
    
    # Retrieval
    def retrieve(self, query):
        """记忆检索"""
        # 查询构建
        queries = self.retrieval.construct_queries(query)
        # 检索策略
        results = self.retrieval.execute(queries)
        # 后处理
        processed = self.retrieval.post_process(results)
        return processed
```

---

## 对 neoclaw 的启发

### 多 Agent 共享记忆

```python
# neoclaw v2.1.0
class SharedMemoryHub:
    """多 Agent 共享记忆中心"""
    
    def __init__(self):
        self.memory = AgentMemorySystem()
        self.agents = {}
    
    def register(self, agent_id, permissions):
        """注册 Agent"""
        self.agents[agent_id] = permissions
    
    def share(self, agent_id, memory_item):
        """共享记忆"""
        if self.agents[agent_id].can_write:
            self.memory.form(memory_item)
    
    def access(self, agent_id, query):
        """访问共享记忆"""
        if self.agents[agent_id].can_read:
            return self.memory.retrieve(query)
```

---

## 关键引用

- Hu & Liu et al. (2026). *Memory in the Age of AI Agents*.
- GitHub Paper List: https://github.com/Shichun-Liu/Agent-Memory-Paper-List

---

## 总结

**Survey 的核心贡献**:
1. **范围界定**: Agent Memory vs. LLM Memory/RAG/Context Engineering
2. **Forms 三分类**: Token/Parametric/Latent
3. **Functions 细粒度**: Factual/Experiential/Working
4. **Dynamics 三阶段**: Formation/Evolution/Retrieval
5. **七大前沿**: Generation, Automation, RL, Multimodal, Shared, World Model, Trustworthy

**对 Project Neo 的意义**:
- claw-mem: 完整记忆系统设计
- neoclaw: 多 Agent 共享记忆
