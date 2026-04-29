# Memory Intelligence Agent (MIA)

> **论文信息**
> - 标题: Memory Intelligence Agent
> - 作者: Jingyang Qiao, Weicheng Meng et al. (East China Normal University, Shanghai Innovation Institute)
> - 发布: arXiv:2604.04503v2, 2026-04-07
> - GitHub: https://github.com/ECNU-SII/MIA
> - HuggingFace: https://huggingface.co/LightningCreeper/MIA

---

## 核心贡献

> "记忆的本质不是存储,而是进化.压缩即智能,反思即成长."

**MIA**: 一个新颖的记忆框架,通过 Manager-Planner-Executor 架构增强 Deep Research Agent 的推理性能和自我进化能力.

---

## 问题: 长上下文记忆的局限

| 问题 | 描述 |
|------|------|
| **注意力稀释** | 长上下文稀释注意力,阻碍模型理解当前问题 |
| **噪声引入** | 无关或弱相关内容引入噪声,降低推理能力 |
| **存储挑战** | 持续增长的上下文历史带来存储挑战 |
| **检索成本** | 大规模记忆检索带来计算成本 |

### 知识导向 vs 过程导向记忆

| 类型 | 描述 | 示例 |
|------|------|------|
| **知识导向** | 描述"结果是什么" | 用户属性,历史事实,检索文档 |
| **过程导向** | 描述"如何获得结果" | 搜索轨迹,失败尝试,成功策略 |

> "Deep Research Agent 需要辅助搜索路径规划和策略重用的记忆机制,而非简单扩展存储的文本上下文."

---

## MIA 架构

```
┌─────────────────────────────────────────────────────────────┐
│                MIA: Manager-Planner-Executor                │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Memory Manager (非参数化)                 │  │
│  │  • 海马体般的情景记忆                                   │  │
│  │  • 存储压缩的历史搜索轨迹                               │  │
│  │  • 提取高质量正负范式                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Planner (参数化)                          │  │
│  │  • 生成搜索计划                                        │  │
│  │  • 测试时学习 (Test-Time Learning)                     │  │
│  │  • 反思和重规划                                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Executor                                  │  │
│  │  • 搜索和分析信息                                      │  │
│  │  • 遵循搜索计划执行                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ←─── 双向转换: 非参数化 ↔ 参数化 ───→                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心创新

### 1. 三维度检索

> "选择 few-shot 示例时,不仅基于相关性,还考虑质量和频率."

```python
# 三维度检索权重
score = 0.5 * semantic_similarity \
      + 0.3 * quality_reward \
      + 0.2 * frequency_reward
```

### 2. 测试时学习 (Test-Time Learning)

```
┌─────────────────────────────────────────────────────────────┐
│                    测试时学习                                │
│                                                             │
│  上下文层面:                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  提取高质量正负范式 → 显式上下文对比学习                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  参数层面:                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  同步更新 Planner → 捕获潜在知识表示                    │   │
│  │                   → 内化规划能力                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3. 双向记忆转换

```
非参数化记忆 (Manager) ←→ 参数化记忆 (Planner)

压缩轨迹 → 结构化工作流 → Planner 训练
     ↑                          ↓
     └── 正负范式 ←── 推理结果 ──┘
```

### 4. 反思机制

```python
# 反思重规划流程
def reflect_and_replan(execution_trace):
    # 1. 评估执行轨迹
    assessment = assess_trace(execution_trace)
    
    # 2. 如果需要反思
    if assessment.needs_reflection:
        # 3. 生成反思
        reflection = generate_reflection(assessment)
        
        # 4. 重规划
        new_plan = replan(reflection)
        return new_plan
    
    return None
```

**重要约束**: 反思重规划次数限制为 **1 次**.

### 5. 交替强化学习

```
┌─────────────────────────────────────────────────────────────┐
│                    交替 RL 范式                              │
│                                                             │
│  Stage 1: 固定 Executor,训练 Planner                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Planner 学习生成精确计划                             │   │
│  │  Planner 学习自主反思                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  Stage 2: 固定 Planner,训练 Executor                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Executor 学习理解计划                                │   │
│  │  Executor 学习遵循计划                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  → 协同优化,确保高层规划和低层检索相互对齐                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 实验结果

### 增强前沿 LLM

| 模型 | LiveVQA | 提升 | HotpotQA | 提升 |
|------|---------|------|----------|------|
| GPT-5.4 | 基线 | - | 基线 | - |
| GPT-5.4 + MIA | +9% | 显著 | +6% | 显著 |

### 小模型超越大模型

| 模型 | 平均提升 | 对比 |
|------|----------|------|
| Qwen2.5-VL-7B + MIA | +31% | - |
| Qwen2.5-VL-32B (无 MIA) | 基线 | 被 7B+MIA 超越 18% |

### 自我进化 (无监督)

| 迭代 | FVQA-test | LiveVQA | 2Wiki | HotpotQA |
|------|-----------|---------|-------|----------|
| Base | 61.4 | 33.0 | 61.2 | 51.0 |
| Epoch-1 | 65.1 | 40.1 | 71.6 | 61.7 |
| Epoch-2 | 66.4 | 41.4 | 73.4 | 63.1 |
| Epoch-3 | 67.1 | 41.8 | 74.7 | 63.2 |

> "多次训练迭代中观察到一致的性能增长,验证了自主进化机制的有效性."

---

## 对 claw-mem 的启发

### v2.1.0 增强

| 功能 | 来源 | 优先级 |
|------|------|--------|
| **三维度检索** | MIA | P0 |
| **轨迹压缩器** | MIA | P0 |
| **正负范式存储** | MIA | P1 |
| **Meta Plan Memory** | MIA | P2 |

### 三维度检索实现

```python
# claw-mem v2.1.0
class MIAHybridRetriever:
    """三维度混合检索器 (MIA 启发)"""
    
    def __init__(self):
        self.semantic_retriever = SemanticRetriever()
        self.quality_scorer = QualityScorer()
        self.frequency_tracker = FrequencyTracker()
    
    def retrieve(self, query: str, k: int = 10) -> List[Memory]:
        # 语义检索
        candidates = self.semantic_retriever.retrieve(query, k * 3)
        
        # 三维度评分
        scored = []
        for mem in candidates:
            score = (
                0.5 * self.semantic_retriever.similarity(query, mem) +
                0.3 * self.quality_scorer.score(mem) +
                0.2 * self.frequency_tracker.frequency(mem)
            )
            scored.append((mem, score))
        
        # 排序返回 top-k
        scored.sort(key=lambda x: x[1], reverse=True)
        return [m for m, s in scored[:k]]
```

### 轨迹压缩器

```python
class TrajectoryCompressor:
    """轨迹压缩器 (MIA 启发)"""
    
    def compress(self, trajectory: Trajectory) -> CompressedTrajectory:
        """压缩执行轨迹为结构化工作流"""
        return CompressedTrajectory(
            # 提取关键步骤
            key_steps=self._extract_key_steps(trajectory),
            
            # 提取成功策略
            successful_strategies=self._extract_strategies(trajectory, success=True),
            
            # 提取失败模式
            failed_patterns=self._extract_patterns(trajectory, success=False),
            
            # 元数据
            metadata=trajectory.metadata
        )
```

---

## 对 claw-rl 的启发

### v2.1.0 增强

| 功能 | 来源 | 优先级 |
|------|------|--------|
| **多维度评判** | MIA | P0 |
| **测试时学习 (TTL)** | MIA | P1 |
| **反思机制** | MIA | P1 |
| **Planner RL Training** | MIA | P2 |

### 多维度评判器

```python
# claw-rl v2.1.0
class MIAMultiDimensionalJudge:
    """多维度评判器 (MIA 启发)"""
    
    def __init__(self):
        self.logic_judge = LogicJudge()
        self.credibility_judge = CredibilityJudge()
        self.validity_judge = ValidityJudge()
    
    def judge(self, response: Response) -> Judgment:
        # 多维度评分
        logic_score = self.logic_judge.judge(response)
        credibility_score = self.credibility_judge.judge(response)
        validity_score = self.validity_judge.judge(response)
        
        # 加权融合
        final_score = (
            0.40 * logic_score +
            0.35 * credibility_score +
            0.25 * validity_score
        )
        
        return Judgment(
            score=final_score,
            logic=logic_score,
            credibility=credibility_score,
            validity=validity_score
        )
```

### 测试时学习

```python
class TestTimeLearner:
    """测试时学习器 (MIA 启发)"""
    
    def __init__(self, planner: Planner):
        self.planner = planner
        self.paradigm_store = ParadigmStore()
    
    def learn_during_inference(self, trace: ExecutionTrace):
        """推理过程中学习"""
        # 上下文层面:提取正负范式
        if trace.is_successful():
            self.paradigm_store.add_positive(trace.to_paradigm())
        else:
            self.paradigm_store.add_negative(trace.to_paradigm())
        
        # 参数层面:更新 Planner
        self.planner.update(trace.to_training_sample())
```

---

## 联动机制: claw-mem ↔ claw-rl

```
┌─────────────────────────────────────────────────────────────┐
│                claw-mem ↔ claw-rl 联动                       │
│                                                             │
│  claw-mem 提供:                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • 压缩轨迹存储                                       │   │
│  │  • 正负范式检索                                       │   │
│  │  • 三维度检索接口                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  claw-rl 使用:                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • 多维度评判                                         │   │
│  │  • 测试时学习                                         │   │
│  │  • 反思重规划                                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  反馈到 claw-mem:                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • 更新质量评分                                       │   │
│  │  • 更新频率统计                                       │   │
│  │  • 存储新范式                                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 关键引用

- Qiao et al. (2026). *Memory Intelligence Agent*. ECNU.
- Zhang et al. (2025). *Agentic Context Engineering*.
- Packer et al. (2023). *MemGPT: Towards LLMs as Operating Systems*.

---

## 总结

**MIA 的核心贡献**:
1. **Manager-Planner-Executor**: 解耦历史记忆,参数化规划,动态执行
2. **三维度检索**: 语义 + 质量 + 频率
3. **测试时学习**: 推理过程中持续进化
4. **双向转换**: 非参数化 ↔ 参数化
5. **反思机制**: 自主重规划能力

**对 Project Neo 的意义**:
- claw-mem: 三维度检索 + 轨迹压缩
- claw-rl: 多维度评判 + 测试时学习
- neoclaw: 双向记忆转换机制
