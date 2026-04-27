# Agentic Context Engineering (ACE)

> **论文信息**
> - 标题: Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models
> - 作者: Qizheng Zhang, Changran Hu et al. (Stanford, SambaNova, UC Berkeley)
> - 发布: ICLR 2026, arXiv:2510.04618v2
> - GitHub: https://github.com/ace-agent/ace

---

## 核心贡献

> "ACE 将上下文视为演化的 playbook，通过生成、反思、筛选的模块化流程积累、精炼和组织策略。"

**关键结果**:
- Agent 基准: **+10.6%**
- 金融基准: **+8.6%**
- AppWorld: 匹配排名第一的 GPT-4.1 agent
- 适应延迟降低 **86.9%**

---

## 问题: 现有方法的局限

### Brevity Bias (简洁偏见)

| 方法 | 问题 |
|------|------|
| GEPA | 优先简洁、广泛适用的指令 |
| 结果 | 省略领域特定启发式、工具指南、常见失败模式 |

### Context Collapse (上下文坍塌)

```
步骤 60: 18,282 tokens → 准确率 66.7%
步骤 61: 122 tokens → 准确率 57.1% (比无上下文还差!)

原因: LLM 被要求完全重写上下文 → 压缩为短摘要 → 信息丢失
```

---

## ACE 框架

```
┌─────────────────────────────────────────────────────────────┐
│                    ACE Framework                             │
│                                                             │
│  核心理念:                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  上下文不是简洁摘要，而是全面、演化的 playbook          │  │
│  │  • 详细、包容、丰富领域洞察                             │  │
│  │  • LLM 可自主提炼相关性                                 │  │
│  │  • 保留而非压缩领域特定启发式                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  模块化流程:                                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Generation: 生成新策略                             │  │
│  │  2. Reflection: 反思成功/失败                          │  │
│  │  3. Curation: 筛选和整合                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  Grow-and-Refine 原则:                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  • 结构化、增量更新                                     │  │
│  │  • 保留详细知识                                        │  │
│  │  • 防止上下文坍塌                                      │  │
│  │  • 可扩展适应长上下文模型                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心创新

### 1. Evolving Playbook

- 不是静态提示
- 不是压缩摘要
- 持续积累、精炼、组织

### 2. Grow-and-Refine

- **Grow**: 增量添加新策略
- **Refine**: 精炼现有策略
- 避免 monolithic rewriting

### 3. 无标签监督

- 利用执行反馈
- 环境信号
- 自然演化

---

## 实验结果

### Agent 基准

| 方法 | AppWorld 准确率 |
|------|----------------|
| Base LLM | 42.4% |
| ICL | 46.0% |
| GEPA | 46.4% |
| Dynamic Cheatsheet | 51.9% |
| **ACE** | **59.5%** |

### 领域基准

| 基准 | Base | ACE |
|------|------|-----|
| FiNER (金融) | 70.7% | **78.3%** |
| Formula (数值推理) | 67.5% | **76.5%** |

### AppWorld Leaderboard

- ACE 匹配排名第一的 IBM-CUGA (GPT-4.1)
- test-challenge split 上超越 IBM-CUGA
- 使用更小的开源模型 (DeepSeek-V3.1)

---

## 对 claw-mem 的启发

### v2.1.0 增强

| 功能 | 来源 | 优先级 |
|------|------|--------|
| **Evolving Playbook** | ACE | P0 |
| **Grow-and-Refine** | ACE | P0 |
| **防止坍塌** | ACE | P0 |
| **无标签演化** | ACE | P1 |

### 演化记忆系统

```python
# claw-mem v2.1.0
class EvolvingPlaybook:
    """演化记忆系统"""
    
    def __init__(self):
        self.strategies = []  # 策略库
        self.reflections = []  # 反思记录
    
    def grow(self, new_strategy):
        """增量添加策略"""
        # 不覆盖，不压缩
        self.strategies.append({
            "content": new_strategy,
            "source": "generation",
            "timestamp": time.now()
        })
    
    def refine(self, strategy_id, refinement):
        """精炼现有策略"""
        # 增量更新，保留历史
        old = self.strategies[strategy_id]
        self.strategies[strategy_id] = {
            "content": refinement,
            "source": "refinement",
            "derived_from": old,
            "timestamp": time.now()
        }
    
    def curate(self, feedback):
        """筛选和整合"""
        # 基于执行反馈筛选
        for strategy in self.strategies:
            strategy["score"] = self._evaluate(strategy, feedback)
    
    def evolve(self, execution_trace):
        """演化流程"""
        # 1. Generation
        new = self._generate_strategy(execution_trace)
        self.grow(new)
        
        # 2. Reflection
        reflection = self._reflect(execution_trace)
        self.reflections.append(reflection)
        
        # 3. Curation
        self.curate(execution_trace.feedback)
```

---

## 对 neoclaw 的启发

### 自改进 Agent

```python
# neoclaw v2.1.0
class SelfImprovingAgent:
    """自改进 Agent"""
    
    def __init__(self):
        self.playbook = EvolvingPlaybook()
    
    def execute(self, task):
        """执行任务"""
        # 获取相关策略
        strategies = self.playbook.get_relevant(task)
        
        # 执行
        result = self._execute(task, strategies)
        
        # 演化
        self.playbook.evolve(result.trace)
        
        return result
```

---

## 关键引用

- Zhang & Hu et al. (2026). *ACE*. ICLR 2026.
- Dynamic Cheatsheet (ACE 的基础)

---

## 总结

**ACE 的核心贡献**:
1. **Evolving Playbook**: 上下文是演化的 playbook
2. **Grow-and-Refine**: 增量更新防止坍塌
3. **三阶段流程**: Generation → Reflection → Curation
4. **无标签监督**: 利用执行反馈
5. **高性能**: +10.6% (Agent), +8.6% (Domain)

**对 Project Neo 的意义**:
- claw-mem: 演化记忆系统
- neoclaw: 自改进 Agent
