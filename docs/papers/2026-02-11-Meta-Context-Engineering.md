# Meta Context Engineering via Agentic Skill Evolution

> **论文信息**
> - 标题: Meta Context Engineering via Agentic Skill Evolution
> - 作者: Haoran Ye, Xuning He et al. (Peking University)
> - 发布: arXiv:2601.21557v2, 2026-02-11
> - GitHub: https://github.com/metaevo-ai/meta-context-engineering

---

## 核心贡献

> "我们引入 Meta Context Engineering (MCE),一个双层框架,通过 CE 技能与上下文物件的共同进化取代静态 CE 启发式方法."

**关键结果**:
- 相对 SOTA 提升: 5.6%–53.8% (平均 16.9%)
- 训练效率: 13.6× 加速
- 上下文适应性: 1.5K–86K tokens 灵活调整

---

## 问题: 手工 Harness 的局限

### 现有 CE 方法的偏见

| 层面 | 方法 | 偏见 | 问题 |
|------|------|------|------|
| **表示层** | Case-based | 保留丰富轨迹 | 缺乏泛化 |
| **表示层** | Itemized lists | 累积抽象洞察 | 扁平,结构受限 |
| **表示层** | Graph-based | 灵活组织 | 高延迟 |
| **优化层** | Prompt-rewriting (GEPA) | 偏好简洁 | 缺乏详细策略 |
| **优化层** | Additive-curation (ACE) | 偏好冗长 | 上下文膨胀 |

**核心问题**:
> "这些启发式选择将 CE 限制在一个狭窄的设计子空间,排除了超越人类直觉的任务最优策略发现."

---

## MCE 双层框架

```
┌─────────────────────────────────────────────────────────────┐
│                    MCE 双层框架                              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Meta-Level: 技能进化                                  │  │
│  │                                                       │  │
│  │  Agentic Crossover:                                   │  │
│  │  • 推理任务规范                                        │  │
│  │  • 分析历史 CE 轨迹                                    │  │
│  │  • 综合性能指标                                        │  │
│  │  • 合成更优技能                                        │  │
│  │                                                       │  │
│  │  输出: CE 技能 (可执行指令 + 代码)                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Base-Level: 上下文优化                                │  │
│  │                                                       │  │
│  │  执行技能:                                             │  │
│  │  • 使用 Coding Toolkits                                │  │
│  │  • 访问文件系统                                        │  │
│  │  • 从训练轮次学习                                      │  │
│  │  • 构建上下文物件                                      │  │
│  │                                                       │  │
│  │  输出: 灵活的程序化上下文                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  共同进化: 技能 ↔ 上下文物件                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心创新

### 1. Agentic Skill Evolution

**技能抽象**:
- 可执行指令 + 代码
- 控制 CE 过程
- 通过 Agentic Crossover 进化

**进化算子**:
```python
def agentic_crossover(skills_history, task_spec, metrics):
    """Agentic Crossover: 合成更优技能"""
    # 1. 分析历史技能执行
    # 2. 推理任务规范
    # 3. 综合性能指标
    # 4. 合成新技能
    return new_skill
```

### 2. Fully Agentic Context Optimization

**能力**:
- 生成任意代码
- 调用其他 LLM
- 操作文件结构
- 实例化灵活的程序化上下文

### 3. 通用设计空间

**超越静态 Harness**:
- ACE 的 generation-reflection-curation 只是 MCE 设计空间中的一个点
- MCE 可以重构现有管道
- MCE 可以发现新颖 CE 架构
- MCE 可以动态调整 CE 策略

---

## 实验结果

### 五个领域

| 领域 | 设置 | 相对提升 |
|------|------|----------|
| Finance | Offline | +89.1% |
| Chemistry | Online | +74.1% |
| Medicine | - | - |
| Law | - | - |
| AI Safety | - | - |

### 相对 SOTA 提升

| 设置 | 相对提升 |
|------|----------|
| Offline | 18.4% |
| Online | 33.0% |

### 上下文效率

| 指标 | MCE |
|------|-----|
| 上下文长度 | 1.5K–86K tokens |
| 训练加速 | 13.6× |
| 轮次减少 | 4.8× |

---

## 对 claw-mem 的启发

### v2.1.0 增强

| 功能 | 来源 | 优先级 |
|------|------|--------|
| **技能进化** | MCE | P0 |
| **双层优化** | MCE | P0 |
| **灵活上下文** | MCE | P1 |

### MCE 风格记忆系统

```python
# claw-mem v2.1.0
class MetaContextEngineering:
    """MCE 风格记忆系统"""
    
    def __init__(self):
        # Meta-Level
        self.skill_evolver = SkillEvolver()
        self.skill_db = SkillDatabase()
        
        # Base-Level
        self.context_optimizer = ContextOptimizer()
        self.coding_toolkit = CodingToolkit()
    
    def evolve_skill(self, task_spec):
        """Meta-Level: 技能进化"""
        # 获取历史技能
        history = self.skill_db.get_history()
        
        # Agentic Crossover
        new_skill = self.skill_evolver.crossover(
            history, 
            task_spec,
            metrics=self._compute_metrics()
        )
        
        # 存储新技能
        self.skill_db.store(new_skill)
        
        return new_skill
    
    def optimize_context(self, skill, rollouts):
        """Base-Level: 上下文优化"""
        # 执行技能
        context = self.context_optimizer.execute(
            skill,
            rollouts,
            toolkit=self.coding_toolkit
        )
        
        return context
```

---

## 对 claw-rl 的启发

### 技能进化机制

```python
# claw-rl v2.1.0
class SkillEvolution:
    """技能进化"""
    
    def __init__(self):
        self.population = []
        self.fitness_fn = None
    
    def crossover(self, skill_a, skill_b):
        """Agentic Crossover"""
        # 分析两个技能的优势
        strengths_a = self._analyze_strengths(skill_a)
        strengths_b = self._analyze_strengths(skill_b)
        
        # 合成新技能
        new_skill = self._synthesize(
            strengths_a, 
            strengths_b
        )
        
        return new_skill
    
    def evolve(self, generations: int):
        """进化循环"""
        for gen in range(generations):
            # 评估
            fitness = [
                self.fitness_fn(skill) 
                for skill in self.population
            ]
            
            # 选择
            parents = self._select(fitness)
            
            # 交叉
            offspring = [
                self.crossover(p1, p2) 
                for p1, p2 in parents
            ]
            
            # 变异
            offspring = [
                self._mutate(skill) 
                for skill in offspring
            ]
            
            # 更新种群
            self.population = offspring
```

---

## 关键引用

- Ye & He et al. (2026). *Meta Context Engineering*.
- Zhang et al. (2026). *Agentic Context Engineering (ACE)*.
- Agrawal et al. (2025). *GEPA*.

---

## 总结

**MCE 的核心贡献**:
1. **双层框架**: Meta-Level + Base-Level
2. **技能进化**: Agentic Crossover
3. **灵活上下文**: 程序化上下文物件
4. **共同进化**: 技能 ↔ 上下文

**对 Project Neo 的意义**:
- claw-mem: 技能进化 + 双层优化
- claw-rl: 技能进化机制
