# MIA 论文启发 - claw-mem v2.1.0 规划

**来源论文**: Memory Intelligence Agent (MIA)  
**作者**: 华东师范大学、上海创新研究院、哈尔滨工业大学等  
**日期**: 2026-04-07 (arXiv:2604.04503v2)  
**记录日期**: 2026-04-21  

---

## 1. 核心洞察

### 1.1 传统长上下文记忆的问题

MIA 论文明确指出了传统"长上下文记忆"的四大问题：

| 问题 | 描述 |
|------|------|
| **注意力稀释** | 长上下文会稀释注意力，阻碍模型理解当前问题 |
| **噪声干扰** | 无关或弱相关内容引入噪声，降低推理能力 |
| **存储膨胀** | 持续增长的历史记录带来存储挑战 |
| **检索成本** | 海量记忆检索带来计算开销增长 |

> "Long contexts may dilute attention, hindering the model's understanding of the current problem."

**这验证了 claw-mem 的核心设计选择 — 压缩与结构化，而非无限扩展上下文。**

### 1.2 过程导向记忆 vs 知识导向记忆

| 类型 | 描述 | 示例 |
|------|------|------|
| **知识导向记忆** | 描述"结果是什么" | 用户属性、历史事实、检索文档 |
| **过程导向记忆** | 描述"如何得到结果" | 搜索轨迹、失败尝试、成功策略 |

> "The objective of adopting memory is not merely to store retrieved knowledge, but to leverage historical experiences to guide future planning and exploration."

**关键认知**：记忆的目标不仅是存储知识，更是利用历史经验指导未来规划。

---

## 2. MIA 功能在 claw-mem 中的实现

### 2.1 功能分配表

| MIA 组件 | claw-mem 对应 | 实现状态 |
|----------|---------------|----------|
| Memory Manager | `MemoryManager` | ✅ 已有，需增强压缩能力 |
| Non-parametric Memory | `MEMORY.md` + `memory/*.md` | ✅ 已有 |
| 三维度检索 | `HybridRetriever` | ⚠️ 需扩展 |
| 轨迹压缩 | 新模块 | ❌ 待开发 |
| 正负范式提取 | 新模块 | ❌ 待开发 |
| Meta Plan Memory | 新模块 | ❌ 待开发 |

### 2.2 新增功能设计

#### 2.2.1 轨迹压缩器 (TrajectoryCompressor)

将冗长的交互轨迹压缩为结构化 workflow：

```python
class TrajectoryCompressor:
    """将冗长的交互轨迹压缩为结构化 workflow"""
    
    def compress(self, trajectory: List[Turn]) -> Workflow:
        """
        输入: 多轮对话轨迹
        输出: 结构化 workflow
        
        压缩策略:
        1. 提取关键步骤
        2. 保留关键查询内容
        3. 抽象为高层动作模式
        """
        steps = []
        for turn in trajectory:
            step = self._extract_step(turn)
            if step.is_significant():
                steps.append(step)
        
        return Workflow(
            steps=steps,
            summary=self._summarize(steps),
            metadata={
                'success': trajectory.metadata.get('success'),
                'compressed_at': datetime.now()
            }
        )
    
    def _extract_step(self, turn: Turn) -> Step:
        """提取单步关键信息"""
        return Step(
            action=turn.action_type,
            query=turn.key_query,
            insight=turn.result_insight,
            state_change=turn.state_transition
        )
```

**存储格式** (memory/workflows/YYYY-MM-DD.md):

```markdown
# Workflow: 2026-04-21-001

## Question
Based on the provided image, what event is taking place?

## Workflow Steps
1. Use visual search to generate candidate locations (image → possible locations)
2. Use text search to narrow hypothesis (possible locations → likely country)
3. Use text search to verify with specific query → confirmed answer

## Outcome
- Success: true
- Answer: The event is taking place in Culver City, California.

## Metadata
- retrieval_frequency: 0
- quality_reward: 1
- created_at: 2026-04-21T08:42:00
```

#### 2.2.2 三维度检索器 (MIAHybridRetriever)

扩展现有 `HybridRetriever`，添加三维度评分：

```python
class MIAHybridRetriever(HybridRetriever):
    """
    三维度检索器
    
    维度:
    1. 语义相似度 (Semantic Similarity) - 上下文相关性
    2. 价值奖励 (Value Reward) - 成功率优先
    3. 频率奖励 (Frequency Reward) - 鼓励探索长尾
    """
    
    def __init__(self, store: MarkdownStore, weights: dict = None):
        super().__init__(store)
        self.weights = weights or {
            'semantic': 0.5,
            'value': 0.3,
            'frequency': 0.2
        }
    
    def retrieve(self, query: str, limit: int = 10) -> List[Tuple[Memory, float]]:
        """三维度综合检索"""
        results = []
        
        for memory in self.store.get_all():
            # 1. 语义相似度
            semantic = self._semantic_score(query, memory)
            
            # 2. 价值奖励 (成功率)
            value = memory.metadata.get('success_rate', 0.5)
            
            # 3. 频率奖励 (低频优先，鼓励探索)
            frequency = 1.0 / (memory.metadata.get('access_count', 0) + 1)
            
            # 综合评分
            score = (
                self.weights['semantic'] * semantic +
                self.weights['value'] * value +
                self.weights['frequency'] * frequency
            )
            
            results.append((memory, score))
        
        # 按评分排序
        return sorted(results, key=lambda x: x[1], reverse=True)[:limit]
    
    def _semantic_score(self, query: str, memory: Memory) -> float:
        """计算语义相似度"""
        # 复用现有的 BM25 + N-gram 混合检索
        return super().search(query, limit=1)[0][1] if super().search(query) else 0.0
```

#### 2.2.3 正负范式存储 (ParadigmMemory)

存储成功和失败案例对比，提供显式参考：

```python
class ParadigmMemory:
    """
    正负范式存储
    
    目的: 提供成功/失败案例对比，引导推理
    """
    
    def __init__(self, store: MarkdownStore):
        self.store = store
        self.success_paradigms = []  # 成功范式
        self.failure_paradigms = []  # 失败范式
    
    def store_paradigm(self, workflow: Workflow, success: bool):
        """存储范式"""
        paradigm = Paradigm(
            workflow=workflow,
            success=success,
            stored_at=datetime.now()
        )
        
        if success:
            self.success_paradigms.append(paradigm)
        else:
            self.failure_paradigms.append(paradigm)
        
        # 持久化
        self._persist_paradigm(paradigm)
    
    def get_contrastive_examples(self, query: str, limit: int = 3) -> dict:
        """
        获取对比案例
        
        返回: {
            'positive': [成功案例],
            'negative': [失败案例]
        }
        """
        # 检索相似的成功案例
        positive = [
            p for p in self.success_paradigms
            if self._is_similar(query, p.workflow)
        ][:limit]
        
        # 检索相似的失败案例
        negative = [
            p for p in self.failure_paradigms
            if self._is_similar(query, p.workflow)
        ][:limit]
        
        return {
            'positive': positive,
            'negative': negative
        }
```

**存储格式** (memory/paradigms/positive.md / negative.md):

```markdown
# Positive Paradigms

## Paradigm 001
- Question: What is the capital of France?
- Workflow: Search("France capital") → Extract answer
- Success Rate: 1.0
- Access Count: 5

## Paradigm 002
...
```

#### 2.2.4 Meta Plan Memory

存储高质量计划模板：

```python
class MetaPlanMemory:
    """
    高质量计划模板库
    
    用途: 在 TTL 过程中选择最优轨迹作为最终输出
    """
    
    def __init__(self):
        self.plans: Dict[str, MetaPlan] = {}  # plan_id -> MetaPlan
        self.router = None  # 路由器，选择最优计划
    
    def store_plan(self, plan: Plan, trajectory: Trajectory, success: bool):
        """存储计划"""
        meta_plan = MetaPlan(
            plan=plan,
            trajectory=trajectory,
            success=success,
            quality_score=self._calculate_quality(trajectory)
        )
        self.plans[meta_plan.id] = meta_plan
    
    def select_best_plan(self, plans: List[Plan], query: str) -> Plan:
        """选择最优计划"""
        # 参考历史高质量计划
        reference = self._get_reference(query)
        
        # 路由器选择
        return self.router.select_best(plans, reference)
```

---

## 3. 开发计划

### Phase 1: 核心增强 (v2.1.0)

| 优先级 | 功能 | 工作量 | 负责模块 |
|--------|------|--------|----------|
| P0 | 三维度检索 (相似度+价值+频率) | 2 天 | `retrieval/hybrid.py` |
| P0 | 轨迹压缩器 | 2 天 | `learning/compressor.py` |
| P1 | 正负范式存储 | 1 天 | `memory/paradigm.py` |
| P1 | Workflow 结构化存储格式 | 1 天 | `storage/workflow_store.py` |
| P2 | Meta Plan Memory | 1 天 | `memory/meta_plan.py` |

### Phase 2: 与 claw-rl 联动 (v2.2.0)

| 功能 | 描述 | 依赖 |
|------|------|------|
| 双向记忆转换接口 | 非参数化 ↔ 参数化 | claw-rl v2.1.0 |
| 在线学习循环 | 实时更新记忆与规则 | claw-rl TTL 模块 |
| 自我进化管道 | 驱动持续进化 | claw-rl LearningLoop |

---

## 4. 设计决策

### 4.1 为什么压缩而非扩展？

| 方案 | 优点 | 缺点 |
|------|------|------|
| 长上下文 | 信息完整 | 注意力稀释、存储膨胀、检索成本高 |
| **压缩结构化** | 高效、精准、可检索 | 可能丢失细节 |

**MIA 验证**: 压缩后的结构化 workflow 比原始长上下文更有效。

### 4.2 为什么三维度检索？

| 维度 | 作用 |
|------|------|
| 语义相似度 | 确保上下文相关性 |
| 价值奖励 | 优先高质量成功案例 |
| 频率奖励 | 鼓励探索长尾知识，避免过拟合 |

**平衡**: 相关性 + 质量 + 探索，三者缺一不可。

### 4.3 为什么正负范式对比？

```
仅成功案例 → 可能过拟合，忽略错误模式
仅失败案例 → 缺乏正面引导
正负对比 → 显式学习边界，避免重复错误
```

---

## 5. 参考文献

1. **Memory Intelligence Agent (MIA)** - arXiv:2604.04503v2, 2026-04-07
   - 华东师范大学、上海创新研究院、哈尔滨工业大学等
   - https://arxiv.org/abs/2604.04503

2. **Mnemosyne/SuperLocalMemory V3** - Qualixar, 2025
   - 五层架构 + Zero LLM Pipeline

3. **Engram: Conditional Memory** - DeepSeek-AI, 2025
   - N-gram 哈希 + 稀疏分配

---

## 6. 变更历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-21 | 1.0 | 初始文档，基于 MIA 论文分析 |
