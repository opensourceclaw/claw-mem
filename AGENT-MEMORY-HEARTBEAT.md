# Agent-Memory × Heartbeat 集成文档

> 创建时间：2026-03-08  
> 配置者：Friday 🤖

---

## ✅ 集成完成

### 📁 文件位置

| 文件 | 位置 | 用途 |
|------|------|------|
| **Heartbeat 配置** | `~/.openclaw/workspace/HEARTBEAT.md` | 心跳任务定义 |
| **加载脚本** | `~/.openclaw/workspace/scripts/load-memory-heartbeat.py` | 自动加载记忆 |
| **集成文档** | `~/.openclaw/workspace/AGENT-MEMORY-HEARTBEAT.md` | 本文档 |

---

## 🚀 使用方法

### 方式 1：运行加载脚本

```bash
python3 ~/.openclaw/workspace/scripts/load-memory-heartbeat.py
```

**输出示例：**
```
==================================================
🧠 Agent-Memory 心跳加载
==================================================

📌 用户偏好:
   • Peter 喜欢用列表呈现信息
   • Peter 喜欢直接、干练的交流风格
   • Peter 的时区：Asia/Shanghai
   • 关键决策需要等待 Peter 指令
   • 执行前先汇报，等 Peter 确认

📁 项目上下文:
   • OctoPulse = GitHub 维护者助手

🎓 最近教训:
   ✅ [技能定位] 组合使用效果最佳
   ⚠️ [技能安装] 需要等待 5-10 分钟
   ⚠️ [macOS 兼容性] macOS 11 太旧

📊 记忆统计:
   事实：8 条
   教训：3 条
   实体：2 个
==================================================
```

### 方式 2：在 Heartbeat 中调用

在 `HEARTBEAT.md` 中已配置：

```markdown
## 🧠 Agent-Memory 集成

### 会话开始时加载记忆

```bash
# 1. 加载 Peter 的偏好
python3 ~/.openclaw/workspace/skills/agent-memory/cli/memory-cli.py recall "Peter preference"

# 2. 加载当前项目上下文
python3 ~/.openclaw/workspace/skills/agent-memory/cli/memory-cli.py recall "OctoPulse"

# 3. 查看最近的教训
python3 ~/.openclaw/workspace/skills/agent-memory/cli/memory-cli.py list
```
```

---

## 📋 心跳检查清单

每次心跳/会话开始时，自动检查：

- [ ] **加载用户偏好**（交流风格、工作流）
- [ ] **加载当前项目上下文**（OctoPulse 等）
- [ ] **回顾最近的教训**（避免重复错误）
- [ ] **检查是否有新的重要信息需要记录**

---

## 🎯 使用场景

### 场景 1：每日开始工作时

```bash
# 运行加载脚本，快速回顾上下文
python3 ~/.openclaw/workspace/scripts/load-memory-heartbeat.py
```

### 场景 2：开始新任务前

```bash
# 加载特定项目的记忆
python3 ~/.openclaw/workspace/skills/agent-memory/cli/memory-cli.py recall "OctoPulse"
```

### 场景 3：避免重复错误

```bash
# 查看相关教训
python3 ~/.openclaw/workspace/skills/agent-memory/cli/memory-cli.py recall "教训"
```

### 场景 4：会话结束时

```bash
# 记录新发现
python3 ~/.openclaw/workspace/skills/agent-memory/cli/memory-cli.py remember "新发现" "标签"

# 记录教训
python3 -c "
import sys
sys.path.insert(0, '/Users/liantian/.openclaw/workspace/skills/agent-memory/src')
from memory import AgentMemory
mem = AgentMemory()
mem.learn('行动', '情境', 'positive/negative', '教训')
print('✅ 已记录')
"
```

---

## 📊 当前记忆状态

### 事实 (8 条)

| 类别 | 数量 | 示例 |
|------|------|------|
| 用户偏好 | 5 条 | 交流风格、时区、工作流 |
| 项目信息 | 1 条 | OctoPulse 定位 |
| 身份信息 | 1 条 | Friday 定位 |
| 爱好 | 1 条 | 爬山、阅读等 |

### 教训 (3 条)

| 情境 | 结果 | 教训 |
|------|------|------|
| 技能安装 | ⚠️ negative | ClawHub 速率限制 |
| macOS 兼容性 | ⚠️ negative | gh CLI 需要 macOS 12+ |
| 技能定位 | ✅ positive | Friday+Claude Code 组合 |

### 实体 (2 个)

| 名字 | 类型 | 说明 |
|------|------|------|
| Peter | person | 用户 |
| OctoPulse | project | GitHub 维护者助手项目 |

---

## 🔄 与 OpenClaw Memory 配合

| 系统 | 用途 | 触发时机 |
|------|------|----------|
| **Agent-Memory** | 结构化事实、教训、实体 | 心跳加载、快速查询 |
| **OpenClaw Memory** | 日常对话记录、长期记忆 | 会话自动保存 |

**配合方式：**
- Agent-Memory → 快速加载关键上下文
- OpenClaw Memory → 详细对话历史

---

## 🛠️ 维护建议

### 每周回顾

```bash
# 查看所有记忆
python3 ~/.openclaw/workspace/skills/agent-memory/cli/memory-cli.py list

# 清理过期记忆（可选）
python3 -c "
import sys
sys.path.insert(0, '/Users/liantian/.openclaw/workspace/skills/agent-memory/src')
from memory import AgentMemory
mem = AgentMemory()
deleted = mem.forget_stale(days=90)
print(f'清理了 {deleted} 条过期记忆')
"
```

### 每月整理

- 审查事实的准确性
- 合并重复的记忆
- 删除过时的信息
- 添加新的项目上下文

---

## 📝 最佳实践

### ✅ 推荐

- 会话开始时加载记忆
- 重要发现及时记录
- 失败后立即记录教训
- 定期回顾和整理

### ❌ 避免

- 记录过多琐碎信息
- 重复记录相同内容
- 记录敏感个人信息
- 从不回顾和清理

---

## 🎯 下一步扩展

**可选增强：**

1. **自动记录** - 会话结束时自动提取关键信息
2. **语义搜索** - 集成更好的搜索算法
3. **记忆优先级** - 重要记忆优先显示
4. **跨会话同步** - 多台机器同步记忆

---

*集成完成：2026-03-08 by Friday* 🤖
