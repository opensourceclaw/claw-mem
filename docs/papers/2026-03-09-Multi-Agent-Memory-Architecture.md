# Multi-Agent Memory from a Computer Architecture Perspective

> **论文信息**
> - 标题: Multi-Agent Memory from a Computer Architecture Perspective: Visions and Challenges Ahead
> - 作者: Zhongming Yu, Naicheng Yu et al. (UCSD, Georgia Tech)
> - 发布: arXiv:2603.10062v1, 2026-03-09
> - 会议: Architecture 2.0 '26

---

## 核心贡献

> "我们将多 Agent 记忆框架化为计算机架构问题，区分共享和分布式记忆范式，提出三层记忆层次结构。"

**关键挑战**:
- Cache 跨 Agent 共享
- 结构化记忆访问控制
- 多 Agent 记忆一致性

---

## 背景: 记忆为何重要

### 上下文正在变化

| 趋势 | 基准 | 挑战 |
|------|------|------|
| **长上下文** | RULER | 多跳追踪、聚合、持续推理 |
| **多模态** | MMMU, VideoMME | 图像、视频联合推理 |
| **结构化** | Spider, BIRD | 可执行轨迹、模式 |
| **自定义环境** | SWE-bench, OSWorld | 长期状态跟踪 |

**核心观点**:
> "上下文不再是静态提示，而是具有带宽、缓存和一致性约束的动态记忆系统。"

---

## 两种记忆范式

```
┌─────────────────────────────────────────────────────────────┐
│              Shared vs. Distributed Memory                   │
│                                                             │
│  Shared Memory:                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  所有 Agent 访问共享池                                  │  │
│  │  • 共享向量存储 / 文档数据库                            │  │
│  │  • 知识重用容易                                        │  │
│  │  • 需要一致性支持                                      │  │
│  │  • 问题: 覆盖、过时信息、版本不一致                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Distributed Memory:                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  每个 Agent 拥有本地记忆                                │  │
│  │  • 选择性同步                                          │  │
│  │  • 隔离性和可扩展性                                    │  │
│  │  • 需要显式同步                                        │  │
│  │  • 问题: 状态分歧                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  实际系统: 本地工作记忆 + 选择性共享构件                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 三层记忆层次结构

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Memory Hierarchy                    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Agent I/O Layer                                       │  │
│  │  • 接口: 摄入和发出信息                                 │  │
│  │  • 音频、文本文档、图像、网络调用                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Agent Cache Layer                                     │  │
│  │  • 快速、有限容量记忆                                   │  │
│  │  • 压缩上下文、最近工具调用                             │  │
│  │  • 短期潜在存储 (KV cache, embeddings)                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Agent Memory Layer                                    │  │
│  │  • 大容量、较慢记忆                                     │  │
│  │  • 完整对话历史、向量 DB、图 DB、文档存储                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  关键原则: Agent 性能是端到端数据移动问题                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 协议缺口

### Missing Piece 1: Agent Cache Sharing Protocol

**问题**:
- 缺乏跨 Agent 共享缓存构件的原则性协议
- 目标: 一个 Agent 的缓存结果可被另一个转换和重用

### Missing Piece 2: Agent Memory Access Protocol

**问题**:
- 访问协议 (权限、范围、粒度) 未充分指定
- 关键问题:
  - Agent 能否读取另一个的长期记忆？
  - 访问是只读还是读写？
  - 访问单位: 文档、块、键值记录、轨迹段？

---

## 一致性: 下一个前沿

### 单 Agent 一致性

- 时间一致性
- 新信息整合不矛盾
- 检索反映最新状态

### 多 Agent 一致性

**两个要求**:
1. **读时冲突处理**: 版本迭代下的冲突
2. **更新时可见性和顺序**: 写入何时对其他 Agent 可见

**挑战**:
- 记忆构件异构 (证据、工具轨迹、计划)
- 冲突通常是语义的且与环境状态耦合

---

## 对 claw-mem 的启发

### v2.1.0 增强

| 功能 | 来源 | 优先级 |
|------|------|--------|
| **三层层次结构** | Architecture | P0 |
| **Cache 共享协议** | Architecture | P1 |
| **记忆访问协议** | Architecture | P1 |
| **一致性模型** | Architecture | P0 |

### 多 Agent 记忆系统

```python
# claw-mem v2.1.0
class MultiAgentMemory:
    """多 Agent 记忆系统"""
    
    def __init__(self, mode: str = "shared"):
        self.mode = mode
        
        # 三层层次结构
        self.io_layer = AgentIOLayer()
        self.cache_layer = AgentCacheLayer()
        self.memory_layer = AgentMemoryLayer()
        
        # 一致性管理
        self.consistency = ConsistencyManager()
    
    def read(self, agent_id, query):
        """读取记忆"""
        # 1. 检查 Cache
        cached = self.cache_layer.get(agent_id, query)
        if cached:
            return cached
        
        # 2. 从 Memory Layer 检索
        results = self.memory_layer.retrieve(query)
        
        # 3. 更新 Cache
        self.cache_layer.set(agent_id, query, results)
        
        return results
    
    def write(self, agent_id, item):
        """写入记忆"""
        # 1. 一致性检查
        if not self.consistency.check(agent_id, item):
            raise ConsistencyError("Conflict detected")
        
        # 2. 写入 Memory Layer
        self.memory_layer.store(item)
        
        # 3. 更新 Cache
        self.cache_layer.invalidate(agent_id, item.scope)
        
        # 4. 通知其他 Agent (如果共享模式)
        if self.mode == "shared":
            self._notify_agents(agent_id, item)
```

---

## 对 neoclaw 的启发

### 多 Agent 协调

```python
# neoclaw v2.1.0
class MultiAgentCoordinator:
    """多 Agent 协调器"""
    
    def __init__(self):
        self.memory = MultiAgentMemory(mode="shared")
        self.agents = {}
    
    def register_agent(self, agent_id, agent):
        """注册 Agent"""
        self.agents[agent_id] = agent
    
    def coordinate(self, task):
        """协调多 Agent"""
        # 1. 分配任务
        assignments = self._assign(task)
        
        # 2. 并行执行
        results = {}
        for agent_id, subtask in assignments.items():
            # 读取共享记忆
            context = self.memory.read(agent_id, subtask)
            
            # 执行
            result = self.agents[agent_id].execute(subtask, context)
            
            # 写入共享记忆
            self.memory.write(agent_id, result)
            
            results[agent_id] = result
        
        return results
```

---

## 关键引用

- Yu et al. (2026). *Multi-Agent Memory from a Computer Architecture Perspective*.
- Computer Architecture Consistency Models.

---

## 总结

**Architecture Perspective 的核心贡献**:
1. **两种范式**: Shared vs. Distributed
2. **三层层次**: I/O → Cache → Memory
3. **协议缺口**: Cache 共享 + 记忆访问
4. **一致性**: 多 Agent 记忆一致性

**对 Project Neo 的意义**:
- claw-mem: 三层层次结构 + 一致性模型
- neoclaw: 多 Agent 协调
