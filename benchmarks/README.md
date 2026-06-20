# claw-mem Performance Benchmarks

This directory contains performance benchmarks for claw-mem.

## 📁 Directory Structure

```
benchmarks/
├── README.md                   # This file
└── scripts/                   # Benchmark scripts (TypeScript)
```

## 🚀 Quick Start

Run performance benchmarks:

```bash
# Run all benchmarks
npm test -- tests/performance/benchmark.test.ts
```

## Benchmark Metrics

| Metric | Target |
|--------|--------|
| Store latency (p95) | < 80ms |
| Search latency (p95) | < 65ms |
| Compress latency (p95) | < 150ms |
| Initialize latency (p95) | < 30ms |

## Implementation

Benchmarks are implemented in TypeScript using Vitest:
- `tests/performance/benchmark.test.ts`

---

*Note: Legacy Python benchmarks have been removed. Use TypeScript benchmarks for accurate performance testing.*
