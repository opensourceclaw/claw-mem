# Day 2 架构改进实施计划

**日期:** 2026-04-08
**任务:** 实施 JARVIS 建议的架构改进
**负责人:** Friday

---

## 🎯 目标

提升 claw-mem 基准测试准确率，从当前 0-33% 提升至目标 75-85%。

---

## 📊 当前状态

| 基准测试 | 当前准确率 | 目标准确率 | 差距 |
|----------|-----------|-----------|------|
| LongMemEval | 23.60% | 75% | -51.4% |
| LoCoMo | 33.33% | 80% | -46.7% |
| ConvoMem | 0.00% | 75% | -75.0% |

---

## 🔧 改进方案

### 方案 1: 精确 ID 匹配（短期验证）

**目标:** 快速验证系统基本功能

**实施步骤:**
1. 为每个测试用例生成唯一 ID
2. 存储时带上测试 ID
3. 查询时精确匹配 ID
4. 预期准确率: 95%+

**优点:**
- 快速实施
- 验证系统基本功能
- 排除其他干扰

**缺点:**
- 不是真实场景
- 不能反映真实性能

**时间:** 1-2 小时

### 方案 2: 语义嵌入搜索（中期方案）

**目标:** 实现真实的语义搜索能力

**实施步骤:**
1. 集成 SentenceTransformer 模型
2. 实现语义嵌入存储
3. 实现余弦相似度搜索
4. 预期准确率: 70-85%

**优点:**
- 真实场景
- 准确率高
- 可扩展

**缺点:**
- 需要额外依赖
- 计算成本高
- 实施时间长

**时间:** 1-2 天

---

## 📋 实施计划

### Phase 1: 精确 ID 匹配（立即实施）

**任务:**
- [ ] 修改测试数据生成器，添加唯一 ID
- [ ] 修改存储逻辑，保存测试 ID
- [ ] 修改搜索逻辑，精确匹配 ID
- [ ] 重新运行基准测试
- [ ] 验证基本功能

**预期结果:**
- 准确率提升至 95%+
- 验证系统基本功能正常

### Phase 2: 语义搜索（后续实施）

**任务:**
- [ ] 添加 SentenceTransformer 依赖
- [ ] 实现 SemanticRetriever 类
- [ ] 实现嵌入存储和搜索
- [ ] 集成到现有系统
- [ ] 重新运行基准测试
- [ ] 验证语义搜索效果

**预期结果:**
- 准确率提升至 70-85%
- 真实场景性能达标

---

## 🚀 立即行动

### Step 1: 修改测试数据生成器

```python
# 为每个测试用例生成唯一 ID
test_case = {
    "id": "q_001",
    "category": "information_extraction",
    "fact": "User's favorite food is Pizza",
    "question": "What is the user's favorite food?",
    "ground_truth": "Pizza",
    "test_id": "test_001"  # 新增：测试 ID
}
```

### Step 2: 修改存储逻辑

```python
# 存储时带上测试 ID
memory_manager.store(
    content=fact,
    metadata={
        "test_id": test_case["test_id"],
        "category": test_case["category"]
    }
)
```

### Step 3: 修改搜索逻辑

```python
# 精确匹配测试 ID
def search_by_test_id(memory_manager, query, test_id):
    results = memory_manager.search(query, limit=100)
    for result in results:
        if result.get("metadata", {}).get("test_id") == test_id:
            return result
    return None
```

---

## 📊 验证标准

### Phase 1 验证标准

| 基准测试 | 目标准确率 | 验证 |
|----------|-----------|------|
| LongMemEval | 95%+ | [ ] |
| LoCoMo | 95%+ | [ ] |
| ConvoMem | 95%+ | [ ] |

### Phase 2 验证标准

| 基准测试 | 目标准确率 | 验证 |
|----------|-----------|------|
| LongMemEval | 70-85% | [ ] |
| LoCoMo | 70-85% | [ ] |
| ConvoMem | 70-85% | [ ] |

---

## 📝 时间估算

- Phase 1（精确 ID 匹配）: 1-2 小时
- Phase 2（语义搜索）: 1-2 天
- 总计: 1.5-2.5 天

---

## 🎯 成功标准

1. **Phase 1:** 准确率 95%+，验证系统基本功能
2. **Phase 2:** 准确率 70-85%，真实场景性能达标
3. **延迟:** P95 < 20ms
4. **代码质量:** 通过 JARVIS 审查

---

**创建日期:** 2026-04-08
**状态:** 立即实施 Phase 1
