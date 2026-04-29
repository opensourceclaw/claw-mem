# claw-mem 文档目录

> **最后更新**: 2026-04-21

---

## 目录结构

```
docs/
├── architecture/          # 架构设计文档 (5)
│   ├── ARCHITECTURE.md
│   ├── ARCHITECTURE_DECISION_001.md
│   ├── AGENT_MEMORY_STRATEGY.md
│   ├── VECTOR_DB_PLUGINS.md
│   └── ...
│
├── papers/                # 论文阅读摘要 (17)
│   ├── 2026-03-08-Memory-for-Autonomous-LLM-Agents.md
│   ├── 2026-03-29-GAAMA.md
│   ├── 2026-03-09-Multi-Agent-Memory-Architecture.md
│   ├── 2026-03-16-Selective-Memory.md
│   ├── 2026-04-07-MIA.md
│   ├── 2026-MEMENTO.md
│   ├── 2026-ICLR-ACE.md
│   └── ...
│
├── development/           # 开发相关文档 (19)
│   ├── P0_DEVELOPMENT_PLAN.md
│   ├── REQUIREMENTS.md
│   ├── COMPETITIVE_ANALYSIS_REPORT.md
│   ├── business-model.md
│   ├── market-analysis-v1.0.0.md
│   ├── product-positioning.md
│   └── ...
│
├── operations/            # 运维相关文档 (19)
│   ├── DEPLOYMENT.md
│   ├── RELEASE_PROCESS_COMPLETE.md
│   ├── APACHE_RELEASE_PROCESS.md
│   ├── ERROR_CODES.md
│   ├── IMPORTANCE_SCORING_GUIDE.md
│   └── ...
│
├── research/              # 研究笔记 (5)
│   ├── best-practices.md
│   └── technical-research-v1.0.0/
│
├── roadmaps/              # 版本规划 (1)
│   └── CLAW_MEM_200_MIGRATION_PLAN.md
│
├── adr/                   # 架构决策记录
├── archive/               # 历史归档
├── design/                # 详细设计
├── experiments/           # 实验记录
├── user-guide/            # 用户指南
│
└── v{version}/            # 版本特定文档
    ├── v1.0.0/
    ├── v2.0.0/
    ├── v2.1.0/
    └── ...
```

---

## 文档分类说明

| 目录 | 用途 | 文档数 |
|------|------|--------|
| `architecture/` | 架构设计,技术选型 | 5 |
| `papers/` | 论文阅读摘要 | 17 |
| `development/` | 开发计划,需求分析,产品规划 | 19 |
| `operations/` | 部署运维,发布流程 | 19 |
| `research/` | 技术调研,最佳实践 | 5 |
| `roadmaps/` | 版本规划,迁移计划 | 1 |
| `v{version}/` | 版本特定文档 | - |

---

## 论文摘要索引

### 核心论文 (P0)

| 论文 | 核心启发 | 文档 |
|------|----------|------|
| Memory for Autonomous LLM Agents | Write–Manage–Read 循环 | `papers/2026-03-08-*.md` |
| GAAMA | 概念介导图谱 | `papers/2026-03-29-*.md` |
| Selective Memory | 写时门控 | `papers/2026-03-16-*.md` |
| ACE | Evolving Playbook | `papers/2026-ICLR-ACE.md` |
| MEMENTO | 自管理上下文 | `papers/2026-MEMENTO.md` |
| MIA | 参数/非参数转换 | `papers/2026-04-07-MIA.md` |

### 优化论文 (P1)

| 论文 | 核心启发 | 文档 |
|------|----------|------|
| HISA | 层次化索引 | `papers/2026-04-01-*.md` |
| NSA | 三路稀疏注意力 | `papers/2025-02-27-*.md` |

---

## v2.1.0 规划

基于论文洞察,v2.1.0 将实现:

| Phase | 功能 | 论文来源 |
|-------|------|----------|
| Phase 1 | 写时门控 | Selective Memory |
| Phase 2 | 概念介导图谱 | GAAMA |
| Phase 3 | 演化记忆 | ACE |
| Phase 4 | 双向记忆转换 | MIA |

---

## 相关链接

- **GitHub**: https://github.com/opensourceclaw/claw-mem
- **ClawHub**: https://clawhub.ai/petercheng/opensourceclaw-claw-mem
- **安装**: `pip install git+https://github.com/opensourceclaw/claw-mem.git`
