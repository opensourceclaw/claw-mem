# MEMORY.md — Claw Memory System

<!-- Core Memory - Permanent Storage -->

## 项目角色定位
OpenClaw 记忆子系统：持久化存储、检索、搜索与记忆管理，为 Agent 提供跨会话记忆。

## 关键决策记录
- v7.3.0（2026-08-20）：发布 GitHub Packages（@opensourceclaw/claw-mem），依赖 claw-gov/claw-ctx 从 file: 迁移 registry
- T40（2026-08-21）：CI 注入 NODE_AUTH_TOKEN（PACKAGES_TOKEN）修复跨仓库包 401；test matrix 收敛 Node 22（Node 24 benchmark 阈值 CI 慢机器失败）
- manifest contracts.tools 已声明 16 个 memory_* 工具（MDT H5-MANIFEST）

## 待办/已完成
- [x] v7.3.0 发布 + CI 全绿
- [ ] Node 24 benchmark 阈值测试恢复（需放宽 p95 阈值或 CI 标记跳过）
