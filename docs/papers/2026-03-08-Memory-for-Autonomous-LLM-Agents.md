# Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers

> **论文信息**
> - 标题: Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers
> - 作者: Pengfei Du (Hong Kong Research Institute of Technology)
> - 发布: arXiv:2603.07670v1, 2026-03-08
> - 类型: 综述论文 (Survey)

---

## 核心贡献

> "Memory——持久化、组织和选择性召回信息的能力——是将无状态文本生成器转变为真正自适应 Agent 的关键。"

**综述范围**: 2022–2026 年 LLM Agent Memory 研究

---

## 问题: 无记忆的后果

### 场景: 调试助手

| 无记忆 | 有记忆 |
|--------|--------|
| 每周一重新发现目录布局 | 已知热点位置 |
| 重读相同 README | 跳过死胡同 |
| 重试周五失败的修复 | 避免重复错误 |
| 无项目特定启发式 | 逐渐提炼启发式 |

**核心观点**:
> "这不是边际改进，而是质变。Memory 将无状态 LLM 转变为自进化 Agent。"

---

## Agent Memory 形式化

### Write–Manage–Read 循环

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Memory 循环                        │
│                                                             │
│  at = πθ(xt, R(Mt, xt), gt)    ← 读取记忆，决策              │
│                                                             │
│  Mt+1 = U(Mt, xt, at, ot, rt)  ← 写入/管理记忆               │
│                                                             │
│  组件:                                                       │
│  • πθ: 策略 (LLM)                                           │
│  • R: 读取 (检索)                                            │
│  • U: 写入 + 管理 (更新)                                     │
│  • gt: 活跃目标                                              │
│  • ot: 环境反馈                                              │
│  • rt: 奖励信号                                              │
└─────────────────────────────────────────────────────────────┘
```

### POMDP 视角

- Memory Mt = Agent 的信念状态
- 维护交互历史的充分统计量
- 在计算和存储预算约束下优化行动选择

---

## 三维分类法

| 维度 | 选项 |
|------|------|
| **时间范围** | 短期 (上下文) / 中期 (会话) / 长期 (跨会话) |
| **表示基底** | 向量 / 符号 / 混合 |
| **控制策略** | 固定 / 启发式 / 学习 |

---

## 五大机制家族

### 1. Context-Resident Compression

**方法**: 压缩当前上下文
**代表**: LLMA, AutoCompressor

### 2. Retrieval-Augmented Stores

**方法**: 外部检索存储
**代表**: RAG, MemGPT

### 3. Reflective Self-Improvement

**方法**: 反思改进
**代表**: Reflexion, Generative Agents

### 4. Hierarchical Virtual Context

**方法**: 分层虚拟内存
**代表**: MemGPT, OS 风格内存

### 5. Policy-Learned Management

**方法**: 策略学习管理
**代表**: Agentic Memory

---

## 五大设计目标与张力

| 目标 | 描述 | 张力 |
|------|------|------|
| **Utility** | 改善任务结果 | 存储一切 → 膨胀 |
| **Efficiency** | Token/延迟/存储成本 | 压缩 → 丢失关键事实 |
| **Adaptivity** | 增量更新 | - |
| **Faithfulness** | 准确且当前 | 过时/幻觉召回 |
| **Governance** | 隐私/合规 | 删除请求支持 |

---

## 评估基准

### 四大基准 (2025–2026)

| 基准 | 特点 |
|------|------|
| **MemBench** | 多维度评估 |
| **MemoryAgent-Bench** | Agent 测试 |
| **MemoryArena** | 多会话任务 |
| **Agentic Memory** | 学习控制 |

### 消融结果

| 系统 | 移除记忆 | 性能下降 |
|------|----------|----------|
| Generative Agents | 移除反思 | 48h 内退化 |
| Voyager | 移除技能库 | 15.3× 速度下降 |
| MemoryArena | 长上下文替代 | 80% → 45% |

---

## 对 claw-mem 的启发

### v2.1.0 增强

| 功能 | 来源 | 优先级 |
|------|------|--------|
| **Write–Manage–Read** | Survey | P0 |
| **三维分类** | Survey | P0 |
| **五大机制** | Survey | P0 |
| **设计目标权衡** | Survey | P1 |

### 完整 Memory 系统

```python
# claw-mem v2.1.0
class AgentMemory:
    """Agent Memory 系统"""
    
    def __init__(self):
        # 三维分类
        self.temporal_scope = "long"  # short/mid/long
        self.representation = "hybrid"  # vector/symbolic/hybrid
        self.control_policy = "learned"  # fixed/heuristic/learned
        
        # Write–Manage–Read
        self.writer = MemoryWriter()
        self.manager = MemoryManager()
        self.reader = MemoryReader()
    
    def read(self, query, context):
        """R: 读取记忆"""
        return self.reader.retrieve(query, context)
    
    def write(self, item, feedback):
        """U: 写入 + 管理"""
        # 1. 写入
        self.writer.write(item)
        
        # 2. 管理
        self.manager.summarize()
        self.manager.deduplicate()
        self.manager.resolve_contradictions()
        self.manager.score_priority()
    
    def update(self, experience):
        """更新循环"""
        # 读取
        relevant = self.read(experience.query, experience.context)
        
        # 决策 (由 Agent 策略完成)
        action = self.policy(experience, relevant)
        
        # 写入 + 管理
        self.write(experience, action.feedback)
```

---

## 对 neoclaw 的启发

### 记忆增强 Agent

```python
# neoclaw v2.1.0
class MemoryAugmentedAgent:
    """记忆增强 Agent"""
    
    def __init__(self):
        self.memory = AgentMemory()
        self.policy = LLMPolicy()
    
    def act(self, observation):
        """行动循环"""
        # 1. 读取记忆
        relevant = self.memory.read(observation, self.goals)
        
        # 2. 决策
        action = self.policy(observation, relevant, self.goals)
        
        # 3. 执行
        feedback = self.execute(action)
        
        # 4. 更新记忆
        self.memory.update(Experience(
            observation=observation,
            action=action,
            feedback=feedback
        ))
        
        return action
```

---

## 关键引用

- Du (2026). *Memory for Autonomous LLM Agents*.
- Park et al. (2023). *Generative Agents*.
- Wang et al. (2023). *Voyager*.

---

## 总结

**Survey 的核心贡献**:
1. **形式化**: Write–Manage–Read 循环
2. **分类**: 三维分类法
3. **机制**: 五大机制家族
4. **评估**: 四大基准
5. **设计目标**: 五大目标与张力

**对 Project Neo 的意义**:
- claw-mem: 完整 Memory 系统设计
- neoclaw: 记忆增强 Agent
