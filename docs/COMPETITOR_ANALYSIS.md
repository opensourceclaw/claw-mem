# AI 记忆系统竞品调研报告

**调研时间:** 2026-03-17  
**调研范围:** 11 个主流记忆系统  
**调研维度:** 架构设计、核心功能、实现方式、优点、缺陷、对 claw-mem 的启发

---

## 📊 竞品总览

| 项目 | 类型 | GitHub Stars | 核心特点 | 状态 |
|------|------|-------------|---------|------|
| **Mem0** | 通用记忆层 | 49.5k+ | 混合检索、云持久化 | 🔥 活跃 |
| **MemGPT/Letta** | 记忆操作系统 | 21k+ | 虚拟上下文管理 | 🔥 活跃 |
| **Cognee** | 知识图谱记忆 | - | ECL 管道、图数据库 | 🔥 活跃 |
| **Zep** | 时序知识图谱 | - | 时间知识图谱 | 🔥 活跃 |
| **memU** | 分层记忆 | - | 文件系统层次架构 | 🔥 活跃 |
| **memOS** | 记忆操作系统 | - | MemCube 模块化架构 | 🔥 活跃 |
| **EverMemOS** | 类脑记忆 | - | 四层类脑架构 | 🔥 活跃 |
| **QMD** | 记忆检索 | - | 混合搜索、Obsidian 集成 | 🔥 活跃 |
| **Mem9** | OpenClaw 专用 | 273 | OpenClaw 持久记忆 | 🔥 活跃 |
| **LanceDB** | 向量数据库 | - | 混合检索、多模态 | 🔥 活跃 |
| **LangMem** | LangChain 记忆 | - | LangGraph 集成 | 🔥 活跃 |

---

## 🔍 详细调研

### 1. Mem0

**定位:** Universal memory layer for AI Agents

**架构设计:**
```
┌─────────────────────────────────────────────────────────┐
│                    Mem0 Architecture                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  API Layer                                              │
│  ├── Python SDK                                         │
│  └── TypeScript SDK                                     │
│                                                         │
│  Core Layer                                             │
│  ├── Memory Manager                                     │
│  ├── Fact Extractor (LLM-based)                         │
│  └── Search Engine (Hybrid: Vector + Keywords)          │
│                                                         │
│  Storage Layer                                          │
│  ├── Vector Stores (FAISS, Qdrant, Pinecone)            │
│  ├── Cloud DBs (Azure MySQL, etc.)                      │
│  └── Local Storage (SQLite)                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**核心功能:**
- ✅ 混合检索（向量 + 关键词）
- ✅ 自动事实提取（LLM 驱动）
- ✅ 跨 Agent 共享记忆
- ✅ 多存储后端支持
- ✅ 云持久化

**优点:**
- 50k+ GitHub stars，社区活跃
- 干净的 SDK，文档完善
- 支持多种向量数据库
- 托管云服务，快速上手

**缺陷:**
- LLM 驱动的事实提取成本高（每次写入都需要 LLM 调用）
- 延迟较高（500ms-2s per operation）
- 对简单用例可能过度设计
- 记忆类型单一（主要是事实记忆）

**对 claw-mem 的启发:**
- ✅ 混合检索是必须的
- ❌ 避免每次写入都调用 LLM（成本太高）
- ✅ 多存储后端支持（可扩展性）

---

### 2. MemGPT / Letta

**定位:** LLMs as Operating Systems

**架构设计:**
```
┌─────────────────────────────────────────────────────────┤
│              MemGPT Virtual Context Management           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Fast Memory (LLM Context Window)                       │
│  ├── System Prompt                                      │
│  ├── Core Memory (用户信息、关键事实)                    │
│  ├── Chat Summary                                       │
│  └── Chat History (最近 N 轮)                             │
│                                                         │
│  Slow Memory (External Storage)                         │
│  ├── Archival Memory (长期归档)                         │
│  └── Recall Memory (检索增强)                           │
│                                                         │
│  Paging System                                          │
│  ├── Memory Load (Slow → Fast)                          │
│  └── Memory Save (Fast → Slow)                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**核心功能:**
- ✅ 虚拟上下文管理（类似 OS 虚拟内存）
- ✅ 自编辑记忆（Agent 可以修改自己的记忆）
- ✅ 工具调用 + 多步推理
- ✅ 核心记忆 + 归档记忆双层设计

**优点:**
- 开创性工作，影响力大
- OS 启发的设计很优雅
- 支持自编辑记忆
- 完整的工具生态系统

**缺陷:**
- 复杂性高，学习曲线陡峭
- 分页逻辑需要手动管理
- 对简单对话场景过度设计
- 性能开销大（频繁的内存交换）

**对 claw-mem 的启发:**
- ✅ 虚拟上下文管理是核心思路
- ✅ 快慢记忆分层是必要的
- ❌ 避免过度复杂的分页逻辑
- ✅ 自编辑记忆很有价值

---

### 3. Cognee

**定位:** Knowledge Engine for AI Agent Memory

**架构设计:**
```
┌─────────────────────────────────────────────────────────┤
│                 Cognee Knowledge Graph                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ECL Pipeline                                           │
│  ├── Extract (提取原始数据)                             │
│  ├── Cognify (转化为知识图谱)                           │
│  └── Load (存储到图数据库)                              │
│                                                         │
│  Storage                                                │
│  ├── Memgraph (内存图数据库)                            │
│  └── LanceDB (向量索引)                                 │
│                                                         │
│  Query Interface                                        │
│  ├── Semantic Search                                    │
│  └── Graph Traversal                                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**核心功能:**
- ✅ ECL 管道（Extract-Cognify-Load）
- ✅ 知识图谱存储
- ✅ 语义检索 + 图遍历
- ✅ 支持实时 web 数据

**优点:**
- 知识图谱架构，关系表达能力强
- ECL 管道设计清晰
- 与 LanceDB 集成良好
- 支持实时数据源

**缺陷:**
- 图数据库复杂度高
- 需要额外的图数据库基础设施
- 学习曲线陡峭
- 对简单场景可能过重

**对 claw-mem 的启发:**
- ✅ 知识图谱可以增强关系表达
- ❌ MVP 阶段避免图数据库（太复杂）
- ✅ ECL 管道思路可以借鉴

---

### 4. Zep

**定位:** Temporal Knowledge Graph Memory

**架构设计:**
```
┌─────────────────────────────────────────────────────────┤
│              Zep Temporal Knowledge Graph                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Memory Types                                           │
│  ├── Episodic Memory (时间戳 + 事件)                    │
│  ├── Semantic Memory (事实知识)                         │
│  └── Procedural Memory (技能)                           │
│                                                         │
│  Temporal Layer                                         │
│  ├── Time-indexed Nodes                                 │
│  └── Temporal Relations                                 │
│                                                         │
│  Storage                                                │
│  └── Graph Database (Neo4j/Memgraph)                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**核心功能:**
- ✅ 时序知识图谱
- ✅ 三种记忆类型（情景/语义/程序）
- ✅ 时间索引检索
- ✅ 上下文工程平台

**优点:**
- 时序设计独特，适合对话历史
- 三种记忆类型覆盖全面
- 企业级合规支持
- 完整的上下文工程平台

**缺陷:**
- 需要图数据库基础设施
- 复杂度高
- 资源消耗大
- 对小型项目过重

**对 claw-mem 的启发:**
- ✅ 三种记忆类型设计很好
- ✅ 时序索引对对话很重要
- ❌ MVP 避免图数据库

---

### 5. memU

**定位:** Hierarchical Memory Architecture

**架构设计:**
```
┌─────────────────────────────────────────────────────────┤
│                  memU Hierarchy                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Layer 1: Resource Layer                                │
│  ├── 原始数据（文档、对话、图片）                       │
│  └── 后台监控新数据                                     │
│                                                         │
│  Layer 2: Memory Item Layer                             │
│  ├── 结构化记忆项                                       │
│  └── 目标检索                                           │
│                                                         │
│  Layer 3: Category Layer                                │
│  ├── 记忆分类                                           │
│  └── 主动上下文加载                                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**核心功能:**
- ✅ 三层分层架构（Resource/Item/Category）
- ✅ 文件系统启发设计
- ✅ 主动记忆管理（proactive）
- ✅ 企业级部署（SOC2 友好）

**优点:**
- 分层设计清晰，类似文件系统
- 支持主动记忆管理
- 企业级特性（本地优先、SOC2）
- 多平台集成

**缺陷:**
- 社区相对较小
- 文档不够完善
- 配置复杂

**对 claw-mem 的启发:**
- ✅ 分层架构是共识
- ✅ 文件系统启发设计很实用
- ✅ 主动记忆管理有价值

---

### 6. memOS

**定位:** Memory OS for AI System

**架构设计:**
```
┌─────────────────────────────────────────────────────────┤
│                    memOS Architecture                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Interface Layer                                        │
│  ├── API Gateway                                        │
│  └── SDK (Python/TypeScript)                            │
│                                                         │
│  Operation Layer                                        │
│  ├── Memory Scheduling                                  │
│  ├── Dynamic Invocation                                 │
│  └── Compliance Governance                              │
│                                                         │
│  Infrastructure Layer                                   │
│  ├── MemCube (模块化记忆单元)                           │
│  ├── Textual Memory                                     │
│  ├── Activation/KV-cache Memory                         │
│  └── Parametric Memory                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**核心功能:**
- ✅ 三层架构（Interface/Operation/Infrastructure）
- ✅ MemCube 模块化设计
- ✅ 多种记忆类型（文本/激活/参数）
- ✅ 动态调度 + 合规治理

**优点:**
- 系统级设计，考虑全面
- 模块化 MemCube 设计
- 支持多种记忆类型
- 强调合规治理

**缺陷:**
- 复杂度高
- 还在早期阶段
- 文档不够完善

**对 claw-mem 的启发:**
- ✅ 三层架构是行业共识
- ✅ 模块化设计值得借鉴
- ❌ MVP 避免过度模块化

---

### 7. EverMemOS

**定位:** Brain-Inspired Long-Term Memory

**架构设计:**
```
┌─────────────────────────────────────────────────────────┤
│              EverMemOS Brain-Inspired Architecture       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Layer 1: MemCells (记忆细胞)                           │
│  ├── 基本记忆单元                                       │
│  └── 类似神经元                                         │
│                                                         │
│  Layer 2: MemScenes (记忆场景)                          │
│  ├── 语义聚合                                           │
│  └── 主题组织                                           │
│                                                         │
│  Layer 3: MemNetworks (记忆网络)                        │
│  ├── 关联网络                                           │
│  └── 知识图谱                                           │
│                                                         │
│  Layer 4: Reconstruction (重构回忆)                     │
│  ├── MemScene 引导检索                                  │
│  └── 上下文重组                                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**核心功能:**
- ✅ 四层类脑架构
- ✅ MemCells → MemScenes → MemNetworks
- ✅ 语义聚合
- ✅ 重构式回忆

**优点:**
- 类脑设计，理论基础强
- 四层架构完整
- 支持语义聚合
- 有论文支持（arXiv:2601.02163）

**缺陷:**
- 还在早期阶段
- 实现复杂度高
- 性能数据有限

**对 claw-mem 的启发:**
- ✅ 类脑设计有理论价值
- ❌ 四层对 MVP 太复杂
- ✅ 语义聚合思路很好

---

### 8. QMD

**定位:** Hybrid Search for Agent Memory

**架构设计:**
```
┌─────────────────────────────────────────────────────────┤
│                    QMD Architecture                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Storage                                                │
│  ├── SQLite (结构化事实)                                │
│  ├── QMD Index (模糊/上下文搜索)                        │
│  └── Obsidian (人类可读知识)                            │
│                                                         │
│  Search                                                 │
│  ├── Keyword Search                                     │
│  └── Semantic Search                                    │
│                                                         │
│  Integration                                            │
│  └── OpenClaw Plugin                                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**核心功能:**
- ✅ 混合检索（SQLite + QMD + Obsidian）
- ✅ 结构化 + 模糊搜索
- ✅ Obsidian 集成
- ✅ OpenClaw 后端优化

**优点:**
- 简单实用，适合个人使用
- 混合检索效果好
- Obsidian 集成受用户欢迎
- OpenClaw 社区认可

**缺陷:**
- 功能相对简单
- 主要是个人项目
- 缺乏企业级特性

**对 claw-mem 的启发:**
- ✅ 混合检索是实用方案
- ✅ SQLite + 向量是好的组合
- ✅ Obsidian 集成思路很好

---

### 9. Mem9

**定位:** Unlimited Memory for OpenClaw

**架构设计:**
```
┌─────────────────────────────────────────────────────────┤
│                    Mem9 Architecture                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  API Layer                                              │
│  ├── REST API (v1alpha2)                                │
│  └── API Key Authentication                             │
│                                                         │
│  Core Layer                                             │
│  ├── Hybrid Search (Vector + Keywords)                  │
│  ├── Shared Spaces                                      │
│  └── Cross-Agent Recall                                 │
│                                                         │
│  Storage                                                │
│  └── Cloud-Persistent (Secure Backup)                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**核心功能:**
- ✅ OpenClaw 专用记忆
- ✅ 混合检索
- ✅ 跨 Agent 回忆
- ✅ 云持久化 + 安全备份

**优点:**
- 专为 OpenClaw 设计，集成度高
- 混合检索
- 云持久化
- 273 GitHub stars，社区活跃

**缺陷:**
- 仅支持 OpenClaw
- 依赖云服务
- 功能相对简单

**对 claw-mem 的启发:**
- ✅ OpenClaw 专用记忆有价值
- ✅ 混合检索是标配
- ❌ 避免云服务依赖（本地优先）

---

### 10. LanceDB

**定位:** Vector Database for RAG, Agents & Hybrid Search

**架构设计:**
```
┌─────────────────────────────────────────────────────────┤
│                   LanceDB Architecture                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Storage                                                │
│  ├── Vector Index (ANN Search)                          │
│  ├── Full-Text Search (BM25)                            │
│  └── Metadata Store                                     │
│                                                         │
│  Query                                                  │
│  ├── Hybrid Search (Vector + Text)                      │
│  └── Multi-Modal Support                                │
│                                                         │
│  Deployment                                             │
│  ├── Local (Embedded)                                   │
│  └── Cloud (Server)                                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**核心功能:**
- ✅ 混合检索（向量 + 全文）
- ✅ 多模态支持
- ✅ 本地 + 云部署
- ✅ 高效内存架构

**优点:**
- 混合检索性能好
- 本地部署简单
- 多模态支持
- 与 Cognee 等集成良好

**缺陷:**
- 主要是向量数据库，不是完整记忆系统
- 需要额外基础设施
- 记忆管理功能有限

**对 claw-mem 的启发:**
- ✅ 混合检索（向量 +BM25）是标配
- ✅ 本地部署很重要
- ❌ 仅向量数据库不够

---

### 11. LangMem

**定位:** Long-Term Memory for AI Agents (by LangChain)

**架构设计:**
```
┌─────────────────────────────────────────────────────────┤
│                   LangMem Architecture                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Integration                                            │
│  ├── LangGraph Native                                   │
│  └── LangChain Tools                                    │
│                                                         │
│  Memory Store                                           │
│  ├── InMemoryStore (开发)                               │
│  └── PersistentStore (生产)                             │
│                                                         │
│  Management                                             │
│  ├── Memory Tools                                       │
│  └── Schema Management                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**核心功能:**
- ✅ LangGraph 原生集成
- ✅ 记忆工具（Memory Tools）
- ✅ 模式管理
- ✅ 存储无关设计

**优点:**
- LangChain 官方支持
- LangGraph 原生集成
- 存储无关设计
- 文档完善

**缺陷:**
- 绑定 LangChain 生态
- 功能相对基础
- 还在早期阶段

**对 claw-mem 的启发:**
- ✅ 与框架深度集成有价值
- ✅ 存储无关设计好
- ❌ 避免绑定单一生态

---

## 📊 竞品对比总结

### 架构设计对比

| 项目 | 分层数 | 存储方式 | 检索方式 | 特色 |
|------|--------|---------|---------|------|
| **Mem0** | 2 层 | 向量 DB+ 云 DB | 混合检索 | LLM 事实提取 |
| **MemGPT** | 2 层 | 上下文 + 外部 | 分页交换 | 虚拟上下文 |
| **Cognee** | 3 层 | 图 DB+ 向量 | 图遍历 + 语义 | ECL 管道 |
| **Zep** | 3 层 | 图 DB | 时序检索 | 时序知识图谱 |
| **memU** | 3 层 | 文件系统 | 分层检索 | 主动管理 |
| **memOS** | 3 层 | 模块化 | 动态调度 | MemCube |
| **EverMemOS** | 4 层 | 类脑 | 重构回忆 | 类脑架构 |
| **QMD** | 2 层 | SQLite+QMD | 混合检索 | Obsidian 集成 |
| **Mem9** | 2 层 | 云存储 | 混合检索 | OpenClaw 专用 |
| **LanceDB** | 1 层 | 向量索引 | 混合检索 | 向量 DB |
| **LangMem** | 2 层 | 存储无关 | 工具调用 | LangGraph 集成 |

### 功能特性对比

| 项目 | 混合检索 | 多记忆类型 | 主动管理 | 云持久化 | 本地部署 | 图数据库 |
|------|---------|-----------|---------|---------|---------|---------|
| **Mem0** | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| **MemGPT** | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Cognee** | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| **Zep** | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| **memU** | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **memOS** | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **EverMemOS** | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **QMD** | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Mem9** | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **LanceDB** | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **LangMem** | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

### 缺陷总结

| 缺陷类型 | 受影响项目 | 对 claw-mem 的警示 |
|---------|-----------|-------------------|
| **LLM 调用成本高** | Mem0 | ❌ 避免每次写入都调用 LLM |
| **复杂度高** | MemGPT, Cognee, Zep, memOS, EverMemOS | ❌ MVP 避免过度设计 |
| **需要图数据库** | Cognee, Zep | ❌ MVP 避免图数据库 |
| **云服务依赖** | Mem0, Mem9 | ❌ 本地优先 |
| **生态绑定** | LangMem | ❌ 保持框架无关 |
| **功能单一** | LanceDB | ❌ 需要完整记忆系统 |
| **社区小** | memU, EverMemOS | ⚠️ 需要活跃社区 |

---

## 💡 对 claw-mem 的综合启发

### 必须有的功能（P0）

| 功能 | 参考项目 | 实现建议 |
|------|---------|---------|
| **混合检索** | Mem0, QMD, LanceDB | 向量 + BM25 + 关键词 |
| **分层架构** | 所有项目 | Working/Short-term/Long-term |
| **本地部署** | 所有项目 | SQLite + 本地向量索引 |
| **多记忆类型** | Zep, memU | Episodic/Semantic/Procedural |

### 应该有的功能（P1）

| 功能 | 参考项目 | 实现建议 |
|------|---------|---------|
| **主动管理** | memU, EverMemOS | 后台监控 + 智能加载 |
| **检查点 + 回滚** | - | 安全分析论文启发 |
| **写入验证** | - | 安全分析论文启发 |

### 后续迭代的功能（P2）

| 功能 | 参考项目 | 说明 |
|------|---------|------|
| **图数据库** | Cognee, Zep | MVP 后考虑 |
| **LLM 事实提取** | Mem0 | 可选功能，控制成本 |
| **云持久化** | Mem0, Mem9 | 可选功能 |
| **类脑架构** | EverMemOS | 长期愿景 |

---

## 🎯 claw-mem 的差异化定位

基于竞品分析，claw-mem 的定位应该是：

```
claw-mem = 
  Mem0 的混合检索 +
  MemGPT 的虚拟上下文 +
  memU 的分层架构 +
  QMD 的简单实用 +
  安全分析论文的五层防御 +
  OpenClaw 深度集成
```

**核心价值主张:**
- ✅ **简单高效** - 避免过度设计
- ✅ **可持续迭代** - 渐进式开发
- ✅ **安全优先** - 内置记忆安全
- ✅ **OpenClaw 原生** - 深度集成

---

## 📋 下一步建议

1. **确定 MVP 范围** - 基于竞品分析，聚焦核心功能
2. **设计架构** - 三层架构 + 混合检索 + 基础安全
3. **技术选型** - SQLite + LanceDB（或类似）
4. **实现原型** - 2-3 周完成 MVP
5. **社区测试** - OpenClaw 社区反馈
6. **迭代优化** - 基于反馈持续改进

---

**Peter，竞品调研完成！请查看并讨论下一步方向。** 🙏
