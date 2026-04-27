# Agentic Context Engineering (ACE)

> **论文信息**
> - 标题: Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models
> - 作者: Qizheng Zhang, Changran Hu et al. (Stanford, SambaNova, UC Berkeley)
> - 发布: ICLR 2026, arXiv:2510.04618v2
> - GitHub: https://github.com/ace-agent/ace

---

## 核心贡献

> "上下文应该作为全面的、演化的 Playbook——详细、包容、富含领域洞察。"

**ACE**: 一个框架，将上下文视为演化的 Playbook，通过生成、反思、策展的模块化流程积累、精炼和组织策略。

---

## 问题: 现有上下文适应方法的局限

### 1. 简洁偏见 (Brevity Bias)

> "许多 prompt 优化器优先考虑简洁、广泛适用的指令，而非全面积累。"

**后果**:
- 省略领域特定的启发式规则
- 省略工具使用指南
- 省略常见失败模式

### 2. 上下文坍缩 (Context Collapse)

> "当 LLM 被要求在每次适应步骤完全重写累积上下文时，会发生上下文坍缩。"

**案例**:
- Step 60: 18,282 tokens, 66.7% accuracy
- Step 61: 122 tokens, 57.1% accuracy (坍缩！)
- 基线 (无上下文): 63.7% accuracy

---

## ACE 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    ACE 三角色架构                            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Generator (生成器)                        │  │
│  │  • 产生推理轨迹                                        │  │
│  │  • 标记有用的/误导的 bullets                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Reflector (反思器)                        │  │
│  │  • 从成功和错误中提取具体洞察                           │  │
│  │  • 多轮精炼                                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Curator (策展器)                          │  │
│  │  • 将洞察合成为结构化上下文更新                         │  │
│  │  • 合并 delta 条目                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ←─── 增量 Delta 更新 (非整体重写) ───→                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心创新

### 1. 增量 Delta 更新 (Incremental Delta Updates)

**上下文表示**: 结构化、条目化的 bullets 集合

```python
@dataclass
class Bullet:
    """上下文条目"""
    id: str                    # 唯一标识
    content: str               # 内容 (策略、概念、失败模式)
    helpful_count: int         # 有用次数
    harmful_count: int         # 有害次数
    created_at: datetime
    updated_at: datetime
```

**优势**:
1. **局部性**: 只更新相关 bullets
2. **细粒度检索**: Generator 可聚焦最相关知识
3. **增量适应**: 高效合并、剪枝、去重

### 2. Grow-and-Refine 机制

```
┌─────────────────────────────────────────────────────────────┐
│                    Grow-and-Refine                           │
│                                                             │
│  Grow (增长):                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • 新标识的 bullets 被追加                            │   │
│  │  • 现有 bullets 原地更新 (计数器递增)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  Refine (精炼):                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • 语义嵌入比较进行去重                                │   │
│  │  • 可主动 (每次 delta 后) 或惰性 (超出窗口时)          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3. 无监督学习

> "ACE 可以在没有标注监督的情况下构建有效的上下文，而是利用执行反馈和环境信号。"

**信号来源**:
- 代码执行成功/失败
- 推理轨迹
- 环境交互结果

---

## 实验结果

### Agent Benchmark (AppWorld)

| 方法 | Test-Normal | Test-Challenge | 平均 |
|------|-------------|----------------|------|
| ReAct (基线) | 42.4% | - | 42.4% |
| ReAct + ICL | 46.0% | - | 46.0% |
| ReAct + GEPA | 46.4% | - | 46.4% |
| **ReAct + ACE** | **59.4%** | - | **59.4%** |

**对比生产系统**:
- ACE (DeepSeek-V3.1): 59.4%
- IBM CUGA (GPT-4.1): 60.3%
- **ACE 在更难的 test-challenge 上超越 IBM CUGA**

### Domain-Specific Benchmark (Financial)

| 方法 | FiNER | Formula | 平均 |
|------|-------|---------|------|
| Base LLM | 70.7% | 67.5% | 69.1% |
| GEPA | 73.5% | 71.5% | 72.5% |
| **ACE** | **78.3%** | **85.5%** | **81.9%** |

### 效率对比

| 指标 | GEPA | ACE | 改进 |
|------|------|-----|------|
| 延迟 (s) | 53,898 | 9,517 | -82.3% |
| Rollouts | 1,434 | 357 | -75.1% |

---

## 对 claw-mem 的启发

### v2.1.0 增强

| 功能 | 来源 | 优先级 |
|------|------|--------|
| **Bullet 结构** | ACE | P0 |
| **增量更新** | ACE | P0 |
| **Grow-and-Refine** | ACE | P1 |
| **有用/有害计数** | ACE | P1 |

### Bullet 存储

```python
# claw-mem v2.1.0
class BulletStore:
    """Bullet 存储 (ACE 启发)"""
    
    def __init__(self):
        self.bullets: Dict[str, Bullet] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
    
    def add(self, bullet: Bullet):
        """添加新 bullet"""
        self.bullets[bullet.id] = bullet
        self.embeddings[bullet.id] = self._embed(bullet.content)
    
    def mark_helpful(self, bullet_id: str):
        """标记为有用"""
        self.bullets[bullet_id].helpful_count += 1
    
    def mark_harmful(self, bullet_id: str):
        """标记为有害"""
        self.bullets[bullet_id].harmful_count += 1
    
    def deduplicate(self, threshold: float = 0.95):
        """去重"""
        # 基于语义嵌入比较
        to_remove = []
        for id1, emb1 in self.embeddings.items():
            for id2, emb2 in self.embeddings.items():
                if id1 != id2 and cosine_similarity(emb1, emb2) > threshold:
                    to_remove.append(id2)
        
        for id in to_remove:
            del self.bullets[id]
            del self.embeddings[id]
```

---

## 对 claw-rl 的启发

### Reflector 作为评判器

```python
# claw-rl v2.1.0
class ACEReflector:
    """反思器 (ACE 启发)"""
    
    def __init__(self, max_rounds: int = 5):
        self.max_rounds = max_rounds
    
    def reflect(self, trajectory: Trajectory) -> List[Insight]:
        """从轨迹提取洞察"""
        insights = []
        
        # 提取成功策略
        if trajectory.is_successful():
            insights.extend(self._extract_success_patterns(trajectory))
        
        # 提取失败模式
        else:
            insights.extend(self._extract_failure_patterns(trajectory))
        
        # 多轮精炼
        for _ in range(self.max_rounds - 1):
            refined = self._refine(insights)
            if refined == insights:
                break
            insights = refined
        
        return insights
```

---

## 对 neoclaw 的启发

### 三角色架构集成

```python
# neoclaw v2.1.0
class ACEIntegration:
    """ACE 三角色集成"""
    
    def __init__(self):
        self.generator = Generator()
        self.reflector = Reflector()
        self.curator = Curator()
        self.bullet_store = BulletStore()
    
    def execute_with_adaptation(self, task: Task) -> Result:
        # 1. Generator 产生轨迹
        trajectory = self.generator.generate(task, self.bullet_store)
        
        # 2. 标记有用的/误导的 bullets
        for bullet_id in trajectory.used_bullets:
            if trajectory.is_bullet_helpful(bullet_id):
                self.bullet_store.mark_helpful(bullet_id)
            else:
                self.bullet_store.mark_harmful(bullet_id)
        
        # 3. Reflector 提取洞察
        insights = self.reflector.reflect(trajectory)
        
        # 4. Curator 更新上下文
        deltas = self.curator.curate(insights)
        for delta in deltas:
            self.bullet_store.add(delta)
        
        # 5. 定期去重
        if self._should_deduplicate():
            self.bullet_store.deduplicate()
        
        return trajectory.result
```

---

## 关键引用

- Zhang et al. (2026). *Agentic Context Engineering*. ICLR 2026.
- Zhang et al. (2025). *Dynamic Cheatsheet*.
- Shinn et al. (2023). *Reflexion*.

---

## 总结

**ACE 的核心贡献**:
1. **增量 Delta 更新**: 避免上下文坍缩
2. **Grow-and-Refine**: 平衡扩展和精炼
3. **三角色架构**: Generator + Reflector + Curator
4. **无监督学习**: 利用执行反馈

**对 Project Neo 的意义**:
- claw-mem: Bullet 存储 + 增量更新
- claw-rl: Reflector 作为评判器
- neoclaw: 三角色架构集成
