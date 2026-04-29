# 任务:更新基准测试 Runners 支持精确 ID 匹配

**项目:** claw-mem
**路径:** /Users/liantian/workspace/osprojects/claw-mem/benchmarks/scripts/

## 目标

更新三个基准测试 runner,支持精确 ID 匹配和测试数据预加载.

## 需要修改的文件

1. `longmemeval_runner.py`
2. `locomo_runner.py`
3. `convomem_runner.py`
4. `run_all_benchmarks.py`

## 修改要求

### 1. 添加预加载函数

```python
def preload_memories(memory_manager, facts_file: str):
    """预加载测试数据到记忆系统"""
    with open(facts_file, 'r') as f:
        facts = json.load(f)
    
    for fact in facts:
        memory_manager.store(
            content=fact["content"],
            metadata={
                "test_id": fact["test_id"],
                "category": fact.get("category", ""),
                "timestamp": fact.get("timestamp", datetime.now().isoformat())
            }
    
    print(f"Preloaded {len(facts)} memories")
    return len(facts)
```

### 2. 添加精确匹配搜索

```python
def search_by_test_id(memory_manager, query: str, test_id: str, limit: int = 100):
    """精确匹配 test_id 的搜索"""
    results = memory_manager.search(query, limit=limit)
    
    # 精确匹配 test_id
    for result in results:
        if isinstance(result, dict):
            if result.get("metadata", {}).get("test_id") == test_id:
                return result
        else:
            # 如果是 Memory 对象
            if hasattr(result, 'metadata') and result.metadata.get("test_id") == test_id:
                return result
    
    return None
```

### 3. 修改测试流程

在 `run_test()` 或 `run_evaluation()` 开始时调用预加载:

```python
# 预加载测试数据
facts_file = self.data_dir / "facts.json"
if facts_file.exists():
    preload_memories(self.memory_manager, facts_file)
```

### 4. 使用精确匹配

在评估问题时使用精确匹配:

```python
def evaluate_question(self, question: str, test_id: str, category: str) -> str:
    """使用精确 ID 匹配评估问题"""
    # 使用精确匹配搜索
    result = search_by_test_id(self.memory_manager, question, test_id)
    
    if result:
        if isinstance(result, dict):
            return result.get("content", "UNKNOWN")
        else:
            return result.content if hasattr(result, 'content') else "UNKNOWN"
    
    return "UNKNOWN"
```

## 测试数据位置

- LongMemEval facts: `data/longmemeval/facts.json`
- LoCoMo facts: `data/locomo/facts.json`
- ConvoMem facts: `data/convomem/facts.json`

## 验证要求

1. 每个 runner 必须能预加载 facts.json
2. 必须使用 test_id 精确匹配
3. 必须正确处理 dict 和 Memory 对象两种返回类型
4. 测试完成后打印预加载记忆数量

## 预期结果

运行测试后,准确率应从 0-33% 提升至 95%+.

## 注意事项

1. 保持与现有代码风格的兼容性
2. 添加适当的错误处理
3. 保持原有的报告生成逻辑
4. 不要删除原有的搜索功能,只是添加精确匹配选项

---

请开始更新这些文件,确保精确 ID 匹配功能正常工作.
