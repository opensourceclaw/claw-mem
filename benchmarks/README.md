# claw-mem Performance Benchmarks

This directory contains performance benchmarks for claw-mem based on three industry-standard benchmarks:

1. **LongMemEval** - Long-term interactive memory evaluation
2. **LoCoMo** - Long conversation memory evaluation
3. **ConvoMem** - Conversational memory evaluation

## 📁 Directory Structure

```
benchmarks/
├── README.md                   # This file
├── data/                       # Test data
│   ├── longmemeval/
│   ├── locomo/
│   └── convomem/
├── scripts/                    # Test scripts
│   ├── longmemeval_runner.py
│   ├── locomo_runner.py
│   ├── convomem_runner.py
│   └── run_all_benchmarks.py
├── results/                    # Test results
│   ├── longmemeval/
│   ├── locomo/
│   └── convomem/
└── reports/                    # Comprehensive reports
```

## 🚀 Quick Start

### Run All Benchmarks

```bash
# Run all benchmarks with default settings
python benchmarks/scripts/run_all_benchmarks.py

# Run with custom workspace
python benchmarks/scripts/run_all_benchmarks.py --workspace /path/to/workspace

# Run with custom data directories
python benchmarks/scripts/run_all_benchmarks.py \
  --longmemeval-data data/longmemeval \
  --locomo-data data/locomo \
  --convomem-data data/convomem
```

### Run Individual Benchmarks

```bash
# LongMemEval
python benchmarks/scripts/longmemeval_runner.py

# LoCoMo
python benchmarks/scripts/locomo_runner.py

# ConvoMem
python benchmarks/scripts/convomem_runner.py --limit 1000  # Limit test cases
```

## 📊 Benchmarks

### 1. LongMemEval

**Reference:** Wu et al., 2024 - "Benchmarking Chat Assistants on Long-Term Interactive Memory"

**Evaluates:**
- Information Extraction
- Cross-Session Reasoning
- Temporal Reasoning
- Knowledge Updates
- Abstention

**Target Metrics:**
- Accuracy: > 85%
- Recall@k: > 80%
- Temporal Reasoning: > 70%

### 2. LoCoMo

**Reference:** Maharana et al., 2024 - "Evaluating Very Long-Term Conversational Memory of LLM Agents"

**Evaluates:**
- Question Answering (single-hop, multi-hop, temporal, open-domain, adversarial)
- Event Graph Summarization
- Multi-modal Dialog Generation

**Target Metrics:**
- QA Accuracy: > 80%
- Event Summary F1: > 75%
- Dialog Coherence: > 85%

### 3. ConvoMem

**Reference:** Salesforce AI Research, 2024 - "ConvoMem Benchmark"

**Evaluates:**
- Single-Turn Memory
- Multi-Turn Memory
- Temporal Memory
- Entity Memory
- Preference Memory
- Factual Memory

**Target Metrics:**
- Memory Recall: > 85%
- Memory Precision: > 80%
- Response Accuracy: > 75%

## 📈 Performance Targets

| Benchmark | Metric | Target | Priority |
|-----------|--------|--------|----------|
| **LongMemEval** | Accuracy | > 85% | P0 |
| | Recall@k | > 80% | P0 |
| | Temporal Reasoning | > 70% | P1 |
| **LoCoMo** | QA Accuracy (Avg) | > 80% | P0 |
| | Event Summary F1 | > 75% | P1 |
| | Dialog Coherence | > 85% | P1 |
| **ConvoMem** | Memory Recall | > 85% | P0 |
| | Memory Precision | > 80% | P0 |
| | Response Accuracy | > 75% | P1 |

## 🔧 Test Data Preparation

### LongMemEval Test Data

```json
{
  "id": "q001",
  "category": "information_extraction",
  "question": "What is the user's favorite programming language?",
  "ground_truth": "Python",
  "context": {
    "session_id": "s001",
    "turns": [...]
  }
}
```

### LoCoMo Test Data

```json
{
  "id": "conv001",
  "turns": [
    {
      "id": "t001",
      "speaker": "user",
      "content": "I love Python",
      "timestamp": "2024-01-01T10:00:00Z"
    }
  ],
  "qa_pairs": [
    {
      "category": "single_hop",
      "question": "What programming language does the user like?",
      "answer": "Python"
    }
  ]
}
```

### ConvoMem Test Data

```json
{
  "id": "test001",
  "scenario": "entity",
  "conversation": [...],
  "question": "What is the user's job?",
  "expected": "Software Engineer",
  "context": {
    "entity": "user"
  }
}
```

## 🤝 JARVIS Collaboration

### Test Execution Request

After preparing test data, send execution request to JARVIS:

```markdown
# JARVIS Test Execution Request

**From:** Friday
**Date:** 2026-04-XX
**Subject:** claw-mem Performance Benchmarks

## Test Suite

1. LongMemEval (500 questions, 5 categories)
2. LoCoMo (hundreds of conversations, 3 tasks)
3. ConvoMem (75,336 QA pairs, 6 scenarios)

## Execution Steps

1. Prepare test data in `benchmarks/data/`
2. Run: `python benchmarks/scripts/run_all_benchmarks.py`
3. Collect results from `benchmarks/results/`
4. Generate report in `benchmarks/reports/`

## Expected Outputs

1. Performance metrics JSON
2. Bottleneck analysis
3. Optimization recommendations
```

## 📝 Output Format

### Results JSON

```json
{
  "benchmark": "LongMemEval",
  "timestamp": "2026-04-08T...",
  "summary": {
    "accuracy": 0.85,
    "target_achieved": true
  },
  "by_category": {
    "information_extraction": 0.90,
    "cross_session_reasoning": 0.82,
    "temporal_reasoning": 0.75,
    "knowledge_updates": 0.88,
    "abstention": 0.90
  },
  "latency": {
    "mean": 0.008,
    "p50": 0.006,
    "p95": 0.015,
    "p99": 0.025
  }
}
```

## 📚 References

1. **LongMemEval**: Wu et al., 2024 - "Benchmarking Chat Assistants on Long-Term Interactive Memory"
2. **LoCoMo**: Maharana et al., 2024 - "Evaluating Very Long-Term Conversational Memory of LLM Agents"
3. **ConvoMem**: Salesforce AI Research, 2024 - "ConvoMem Benchmark"

## 📄 License

Apache License 2.0

---

**Created:** 2026-04-08
**Author:** Friday (Main Agent)
**Collaboration:** JARVIS (Test Execution)


