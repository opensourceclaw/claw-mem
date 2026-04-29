# claw-mem 基准测试实施指南

**日期:** 2026-04-08
**研究者:** Friday
**协作:** JARVIS (测试执行和效果评估)

---

## 📋 执行策略

### Friday 负责的工作(Day 1-2)

1. **研究基准测试** ✅
   - LongMemEval 论文研究
   - LoCoMo 论文研究
   - ConvoMem 论文研究

2. **设计测试用例** (Day 2)
   - 设计 LongMemEval 风格测试集
   - 设计 LoCoMo 风格测试集
   - 设计 ConvoMem 风格测试集

3. **搭建测试环境** (Day 2)
   - 准备测试数据
   - 编写测试脚本框架
   - 配置测试环境

### JARVIS 负责的工作(Day 3-4)

1. **测试执行**
   - 运行 LongMemEval 测试
   - 运行 LoCoMo 测试
   - 运行 ConvoMem 测试

2. **效果评估**
   - 收集测试结果
   - 分析性能指标
   - 识别性能瓶颈

3. **优化建议**
   - 提供优化方案
   - 验证优化效果
   - 生成性能报告

---

## 🎯 基准测试实施计划

### 1. LongMemEval 实施方案

#### 测试数据集

**来源:** MemPalace GitHub (https://github.com/milla-jovovich/mempalace/tree/main/benchmarks)

**数据规模:** 500 个问题

**评测维度:**
1. Information Extraction (100 题)
2. Cross-Session Reasoning (100 题)
3. Temporal Reasoning (100 题)
4. Knowledge Updates (100 题)
5. Abstention (100 题)

#### 测试脚本

```python
# benchmarks/longmemeval_runner.py

import json
from pathlib import Path
from typing import List, Dict, Any
from claw_mem import MemoryManager

class LongMemEvalRunner:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.results = []

    def load_test_data(self, data_path: str) -> List[Dict]:
        """加载测试数据"""
        with open(data_path) as f:
            return json.load(f)

    def run_test(self, test_data: List[Dict]) -> Dict:
        """运行测试"""
        results = {
            "total": len(test_data),
            "correct": 0,
            "by_category": {},
            "latencies": []
        }

        for test_case in test_data:
            # 记录开始时间
            start_time = time.time()

            # 执行测试
            answer = self.evaluate_question(
                test_case["question"],
                test_case["category"]
            )

            # 记录结束时间
            latency = time.time() - start_time
            results["latencies"].append(latency)

            # 评估答案
            if self.check_answer(answer, test_case["ground_truth"]):
                results["correct"] += 1
                category = test_case["category"]
                if category not in results["by_category"]:
                    results["by_category"][category] = 0
                results["by_category"][category] += 1

        return results

    def evaluate_question(self, question: str, category: str) -> str:
        """评估问题"""
        # 根据类别使用不同的记忆检索策略
        if category == "information_extraction":
            return self.extract_information(question)
        elif category == "cross_session_reasoning":
            return self.cross_session_reason(question)
        elif category == "temporal_reasoning":
            return self.temporal_reason(question)
        elif category == "knowledge_updates":
            return self.update_knowledge(question)
        elif category == "abstention":
            return self.check_abstention(question)

    def generate_report(self, results: Dict) -> Dict:
        """生成报告"""
        return {
            "accuracy": results["correct"] / results["total"],
            "by_category": {
                cat: count / (results["total"] / 5)
                for cat, count in results["by_category"].items()
            },
            "latency": {
                "mean": np.mean(results["latencies"]),
                "p50": np.percentile(results["latencies"], 50),
                "p95": np.percentile(results["latencies"], 95),
                "p99": np.percentile(results["latencies"], 99)
            }
        }
```

#### 目标指标

| 指标 | 目标值 | MemPalace | Mem0 | Zep |
|------|--------|-----------|------|-----|
| **Raw Accuracy** | > 85% | 96.6% | ~85% | ~82% |
| **Recall@k** | > 80% | - | - | - |
| **Latency (P95)** | < 20ms | - | - | - |

---

### 2. LoCoMo 实施方案

#### 测试数据集

**来源:** Snap Research GitHub (https://github.com/snap-research/locomo)

**数据规模:** 数百轮对话

**评测维度:**
1. Single-hop Questions
2. Multi-hop Questions
3. Temporal Reasoning
4. Open-domain Knowledge
5. Adversarial Questions

#### 测试脚本

```python
# benchmarks/locomo_runner.py

import json
from typing import List, Dict
from claw_mem import MemoryManager

class LoCoMoRunner:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.results = []

    def load_conversations(self, data_path: str) -> List[Dict]:
        """加载对话数据"""
        with open(data_path) as f:
            return json.load(f)

    def run_evaluation(self, conversations: List[Dict]) -> Dict:
        """运行评估"""
        results = {
            "qa_accuracy": {},
            "event_summarization": {},
            "dialog_generation": {}
        }

        # QA 评估
        results["qa_accuracy"] = self.evaluate_qa(conversations)

        # 事件摘要评估
        results["event_summarization"] = self.evaluate_event_summarization(conversations)

        # 对话生成评估
        results["dialog_generation"] = self.evaluate_dialog_generation(conversations)

        return results

    def evaluate_qa(self, conversations: List[Dict]) -> Dict:
        """评估问答能力"""
        qa_results = {
            "single_hop": [],
            "multi_hop": [],
            "temporal": [],
            "open_domain": [],
            "adversarial": []
        }

        for conv in conversations:
            for qa in conv["qa_pairs"]:
                category = qa["category"]
                answer = self.answer_question(qa["question"], conv["history"])
                correct = self.check_answer(answer, qa["answer"])
                qa_results[category].append(correct)

        return {
            cat: sum(corrects) / len(corrects)
            for cat, corrects in qa_results.items()
        }
```

#### 目标指标

| 指标 | 目标值 | MemMachine | 最佳实践 |
|------|--------|------------|----------|
| **QA Accuracy (Avg)** | > 80% | 92.09% | - |
| **Single-hop** | > 90% | - | - |
| **Multi-hop** | > 75% | - | - |
| **Temporal** | > 70% | - | - |
| **Open-domain** | > 80% | - | - |
| **Adversarial** | > 85% | - | - |

---

### 3. ConvoMem 实施方案

#### 测试数据集

**来源:** Salesforce GitHub (https://github.com/SalesforceAIResearch/ConvoMem)

**数据规模:** 75,336 个问答对

**评测维度:**
1. Single-Turn Memory
2. Multi-Turn Memory
3. Temporal Memory
4. Entity Memory
5. Preference Memory
6. Factual Memory

#### 测试脚本

```python
# benchmarks/convomem_runner.py

import json
from typing import List, Dict
from claw_mem import MemoryManager

class ConvoMemRunner:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.results = []

    def load_dataset(self, data_path: str) -> List[Dict]:
        """加载数据集"""
        with open(data_path) as f:
            return json.load(f)

    def run_evaluation(self, dataset: List[Dict]) -> Dict:
        """运行评估"""
        results = {
            "memory_recall": 0.0,
            "memory_precision": 0.0,
            "response_accuracy": 0.0,
            "context_utilization": 0.0,
            "by_scenario": {}
        }

        # 按场景评估
        for scenario in ["single_turn", "multi_turn", "temporal",
                         "entity", "preference", "factual"]:
            results["by_scenario"][scenario] = self.evaluate_scenario(
                dataset, scenario
            )

        # 计算总体指标
        results["memory_recall"] = np.mean([
            s["recall"] for s in results["by_scenario"].values()
        ])
        results["memory_precision"] = np.mean([
            s["precision"] for s in results["by_scenario"].values()
        ])

        return results
```

#### 目标指标

| 指标 | 目标值 | 基准 |
|------|--------|------|
| **Memory Recall** | > 85% | - |
| **Memory Precision** | > 80% | - |
| **Response Accuracy** | > 75% | - |
| **Context Utilization** | > 80% | - |

---

## 📁 测试环境搭建

### 目录结构

```
claw-mem/
├── benchmarks/
│   ├── data/
│   │   ├── longmemeval/
│   │   │   ├── test_data.json
│   │   │   └── ground_truth.json
│   │   ├── locomo/
│   │   │   ├── conversations.json
│   │   │   └── qa_pairs.json
│   │   └── convomem/
│   │       ├── dataset.json
│   │       └── scenarios.json
│   ├── scripts/
│   │   ├── longmemeval_runner.py
│   │   ├── locomo_runner.py
│   │   ├── convomem_runner.py
│   │   └── run_all_benchmarks.py
│   ├── results/
│   │   ├── longmemeval/
│   │   ├── locomo/
│   │   └── convomem/
│   ├── reports/
│   │   └── performance_report.md
│   └── README.md
```

### 依赖安装

```bash
# 安装依赖
pip install numpy pandas scikit-learn matplotlib

# 安装测试工具
pip install pytest pytest-benchmark pytest-cov
```

### 运行测试

```bash
# 运行所有基准测试
python benchmarks/scripts/run_all_benchmarks.py

# 运行单个基准测试
python benchmarks/scripts/longmemeval_runner.py
python benchmarks/scripts/locomo_runner.py
python benchmarks/scripts/convomem_runner.py

# 生成报告
python benchmarks/scripts/generate_report.py
```

---

## 🤝 JARVIS 协作协议

### 测试执行请求

当准备好测试集后,Friday 向 JARVIS 发送执行请求:

```markdown
# JARVIS 测试执行请求

**From:** Friday
**Date:** 2026-04-XX
**Subject:** claw-mem 性能基准测试执行
**Priority:** P0

## 测试范围

1. **LongMemEval** - 500 个问题,5 大任务
2. **LoCoMo** - 数百轮对话,3 大任务
3. **ConvoMem** - 75,336 个问答对,6 大场景

## 测试目标

| 指标 | 目标值 |
|------|--------|
| QA Accuracy | > 75% |
| Recall@k | > 80% |
| Latency (P95) | < 20ms |

## 测试数据

- 测试数据路径: `benchmarks/data/`
- 测试脚本路径: `benchmarks/scripts/`
- 结果输出路径: `benchmarks/results/`

## 测试要求

1. 运行所有基准测试
2. 收集性能指标
3. 识别性能瓶颈
4. 提供优化建议
5. 生成性能报告

## 输出格式

请提供:
1. 测试结果 JSON
2. 性能分析报告
3. 瓶颈识别
4. 优化建议

---

**Friday**
2026-04-XX
```

### 期望输出

JARVIS 应提供:

1. **测试结果 JSON**
   ```json
   {
     "benchmark": "LongMemEval",
     "accuracy": 0.XXX,
     "by_category": {...},
     "latency": {...},
     "bottlenecks": [...]
   }
   ```

2. **性能分析报告**
   - 各项指标得分
   - 与目标对比
   - 性能瓶颈分析

3. **优化建议**
   - 代码层面优化
   - 算法层面优化
   - 架构层面优化

---

## 📊 性能目标总结

### 核心指标

| 基准测试 | 指标 | 目标值 | 参考值 |
|----------|------|--------|--------|
| **LongMemEval** | Accuracy | > 85% | MemPalace 96.6% |
| | Recall@k | > 80% | - |
| | Temporal Reasoning | > 70% | - |
| **LoCoMo** | QA Accuracy (Avg) | > 80% | MemMachine 92.09% |
| | Multi-hop | > 75% | - |
| | Temporal | > 70% | - |
| **ConvoMem** | Memory Recall | > 85% | - |
| | Memory Precision | > 80% | - |

### 性能指标

| 指标 | 目标值 |
|------|--------|
| **Latency (P50)** | < 10ms |
| **Latency (P95)** | < 20ms |
| **Latency (P99)** | < 50ms |
| **Memory Usage** | < 100MB |
| **Storage Efficiency** | > 80% |

---

## 📝 下一步

### Day 1 (今天) - 完成 ✅

- [x] 研究三大基准测试
- [x] 制定测试策略
- [x] 设定性能目标

### Day 2 - 测试集构建

- [ ] 实现 LongMemEval 测试集
- [ ] 实现 LoCoMo 测试集
- [ ] 实现 ConvoMem 测试集
- [ ] 搭建测试环境
- [ ] 准备测试数据

### Day 3-4 - JARVIS 执行

- [ ] 发送测试执行请求给 JARVIS
- [ ] 等待 JARVIS 执行测试
- [ ] 接收测试结果和优化建议
- [ ] 实施优化方案

### Day 5-6 - 优化和报告

- [ ] 根据优化建议改进代码
- [ ] 重新运行测试验证效果
- [ ] 生成最终性能报告

---

**创建日期:** 2026-04-08
**最后更新:** 2026-04-08
**状态:** Day 1 完成,准备 Day 2
**协作模式:** Friday (设计) + JARVIS (执行)
