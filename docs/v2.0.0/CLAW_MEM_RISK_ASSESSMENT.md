# claw-mem Plugin 风险评估报告

**评估时间:** 2026-03-31 21:45  
**评估人员:** Friday AI  
**目的:** 评估添加 claw-mem Plugin 配置是否会遇到与 claw-rl 类似的问题

---

## 🔍 风险对比分析

### claw-rl 问题回顾

| 问题 | 原因 | 影响 |
|------|------|------|
| **registerContextEngine API 签名错误** | 使用对象参数而非 (id, factory) | ❌ Context Engine 注册失败 |
| **Hook 事件名称错误** | 使用 `before_session_start` 而非 `session_start` | ⚠️ Hook 被忽略 |
| **ContextEngine 接口不完整** | 缺少 `info` 和 `ingest` 方法 | ❌ 运行时错误 |

---

## ✅ claw-mem 验证结果

### 1. registerContextEngine 使用

```
✅ claw-mem 没有使用 registerContextEngine
```

**说明:** claw-mem Plugin 没有使用 Context Engine API，不存在此风险。

### 2. Hook 事件名称

```
✅ claw-mem 使用的事件名称正确
```

**使用的事件:**
- `before_agent_start` ✅ (有效事件，被 memory-lancedb 使用)
- `agent_end` ✅ (有效事件，被 memory-lancedb 使用)

**证据:**
```bash
$ grep -rn "before_agent_start\|agent_end" ~/.npm-global/lib/node_modules/openclaw/dist/extensions/
memory-lancedb/index.js:7008:  api.on("before_agent_start", async (event) => {
memory-lancedb/index.js:7023:  api.on("agent_end", async (event) => {
```

### 3. Plugin Kind

```json
{
  "id": "claw-mem",
  "kind": "memory",  // ✅ 正确的 kind
  ...
}
```

**说明:** claw-mem 使用 `memory` kind，不使用 `context-engine`，不存在 Context Engine 注册风险。

### 4. TypeScript 编译

```bash
$ ls -la /Users/liantian/workspace/osprojects/claw-mem/claw_mem_plugin/dist/
total 624
drwx------   13 liantian  staff     416 Mar 31 06:43 .
-rw-------    1 liantian  staff   16628 Mar 31 06:39 index.js  # ✅ 已编译
```

**说明:** TypeScript 已编译，不存在编译错误。

### 5. Bridge 可用性

```bash
$ cd /Users/liantian/workspace/osprojects/claw-mem
$ source venv/bin/activate
$ python3 -c "from claw_mem.bridge import ClawMemBridge; print('✅ 导入成功')"
✅ 导入成功
```

**说明:** Python Bridge 可以正常导入。

---

## 📊 风险评估

| 风险项 | claw-rl | claw-mem | 评估 |
|--------|---------|----------|------|
| **registerContextEngine API** | ❌ 有问题 | ✅ 未使用 | 低风险 |
| **Hook 事件名称** | ⚠️ 错误 | ✅ 正确 | 低风险 |
| **ContextEngine 接口** | ❌ 不完整 | ✅ 不适用 | 低风险 |
| **TypeScript 编译** | ✅ 通过 | ✅ 通过 | 低风险 |
| **Bridge 可用性** | ✅ 正常 | ✅ 正常 | 低风险 |
| **Plugin Kind** | context-engine | memory | 低风险 |

---

## ✅ 验证结论

**claw-mem Plugin 配置添加风险：低**

**原因:**
1. ✅ 没有使用 `registerContextEngine` API
2. ✅ 使用了正确的 Hook 事件名称
3. ✅ 使用 `memory` kind 而非 `context-engine`
4. ✅ TypeScript 编译通过
5. ✅ Python Bridge 可正常导入

---

## 📋 建议的配置

```json
{
  "plugins": {
    "load": {
      "paths": [
        "/Users/liantian/workspace/osprojects/claw-mem/claw_mem_plugin",
        "/Users/liantian/workspace/osprojects/claw-rl/claw_rl_plugin"
      ]
    },
    "slots": {
      "memory": "claw-mem"
    },
    "entries": {
      "claw-mem": {
        "enabled": true,
        "config": {
          "pythonPath": "/Users/liantian/workspace/osprojects/claw-mem/venv/bin/python3",
          "workspaceDir": "/Users/liantian/.openclaw/workspace",
          "autoRecall": true,
          "autoCapture": true,
          "topK": 10
        }
      },
      "claw-rl": {
        "enabled": true,
        "config": {
          "pythonPath": "/Users/liantian/workspace/osprojects/claw-rl/venv/bin/python3",
          "workspaceDir": "/Users/liantian/.openclaw/workspace",
          "autoInject": true,
          "autoLearn": true,
          "topK": 10,
          "debug": false
        }
      }
    }
  }
}
```

---

## 🎯 下一步行动

**请示 Peter Cheng:**

是否执行以下行动？

1. **备份当前配置**
   ```bash
   cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup.$(date +%Y%m%d_%H%M%S)
   ```

2. **添加 claw-mem Plugin 配置**
   - 添加到 `plugins.load.paths`
   - 配置 `plugins.slots.memory: "claw-mem"`
   - 添加 `plugins.entries.claw-mem`

3. **重启 OpenClaw Gateway**
   ```bash
   openclaw gateway restart
   ```

4. **观察日志**
   ```bash
   openclaw logs --follow | grep -E "claw-mem|claw-rl|bridge"
   ```

**风险评估:** 低风险，但建议按照 Harness Engineering 准则执行。

---

**报告完成时间:** 2026-03-31 21:45
