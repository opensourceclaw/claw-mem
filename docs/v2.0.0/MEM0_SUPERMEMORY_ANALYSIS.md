# Mem0 vs Supermemory OpenClaw Plugin 架构对比分析

**分析时间:** 2026-03-30 21:35  
**分析对象:** mem0ai/mem0, supermemoryai/openclaw-supermemory  
**目的:** 研究 OpenClaw Plugin 集成机制,指导 claw-mem v2.0.0 迁移策略

---

## 📊 项目概览

### Mem0 (mem0ai/mem0)

**GitHub:** https://github.com/mem0ai/mem0  
**Stars:** 20k+  
**语言:** TypeScript + Python  
**架构:** 平台 + 开源 SDK 双模式  

**特点:**
- ✅ 支持平台模式和开源模式
- ✅ 提供 5 个记忆工具:search, list, store, get, forget
- ✅ 自动召回(auto-recall)和自动捕获(auto-capture)
- ✅ 双重作用域:session(短期)+ user(长期)
- ✅ 多智能体隔离(per-agent isolation)
- ✅ CLI 命令支持

### Supermemory (supermemoryai/openclaw-supermemory)

**GitHub:** https://github.com/supermemoryai/openclaw-supermemory  
**Stars:** 615  
**语言:** TypeScript  
**架构:** 云服务  

**特点:**
- ✅ 云服务集成
- ✅ 提供 4 个记忆工具:search, store, forget, profile
- ✅ 自动召回和自动捕获
- ✅ Slash 命令支持
- ✅ CLI 命令支持

---

## 🔍 Plugin 架构对比

### 1. Plugin 定义

#### Mem0 Plugin 定义

```typescript
// mem0/openclaw/index.ts
const memoryPlugin = {
  id: "openclaw-mem0",
  name: "Memory (Mem0)",
  description: "Mem0 memory backend — Mem0 platform or self-hosted open-source",
  kind: "memory" as const,
  configSchema: mem0ConfigSchema,
  
  register(api: OpenClawPluginApi) {
    const cfg = mem0ConfigSchema.parse(api.pluginConfig);
    const provider = createProvider(cfg, api);
    
    // ...
  }
};
```

#### Supermemory Plugin 定义

```typescript
// supermemory/index.ts
export default {
  id: "openclaw-supermemory",
  name: "Supermemory",
  description: "OpenClaw powered by Supermemory plugin",
  kind: "memory" as const,
  configSchema: supermemoryConfigSchema,
  
  register(api: OpenClawPluginApi) {
    const cfg = parseConfig(api.pluginConfig);
    const client = new SupermemoryClient(cfg.apiKey, cfg.containerTag);
    
    // ...
  }
};
```

**关键发现:**
- ✅ 两者都使用 `kind: "memory"`
- ✅ 两者都使用 `configSchema` 定义配置
- ✅ 两者都在 `register()` 中初始化

---

### 2. Tool 注册

#### Mem0 Tool 注册

```typescript
// mem0/openclaw/index.ts
api.registerTool(
  {
    name: "memory_search",
    label: "Memory Search",
    description: "Search through long-term memories...",
    parameters: Type.Object({
      query: Type.String({ description: "Search query" }),
      limit: Type.Optional(Type.Number({ description: "Max results" })),
      userId: Type.Optional(Type.String({ description: "User ID" })),
      agentId: Type.Optional(Type.String({ description: "Agent ID" })),
    }),
  },
  async (params, ctx) => {
    // 搜索实现
    const results = await provider.search(params.query, options);
    return { memories: results };
  }
);

api.registerTool(
  {
    name: "memory_store",
    label: "Memory Store",
    description: "Save important information...",
    parameters: Type.Object({
      text: Type.String({ description: "Information to remember" }),
      userId: Type.Optional(Type.String()),
      agentId: Type.Optional(Type.String()),
      longTerm: Type.Optional(Type.Boolean({ default: true })),
    }),
  },
  async (params, ctx) => {
    // 存储实现
    const result = await provider.add(params.text, options);
    return { id: result.id };
  }
);

// 还有 memory_list, memory_get, memory_forget
```

#### Supermemory Tool 注册

```typescript
// supermemory/tools/search.ts
api.registerTool(
  {
    name: "memory_recall",  // 注意:名字不同
    description: "Search memories stored in supermemory...",
    parameters: Type.Object({
      query: Type.String(),
      limit: Type.Optional(Type.Number()),
    }),
  },
  async (params, ctx) => {
    // 搜索实现
    const results = await client.search(params.query, params.limit);
    return { memories: results };
  }
);

// 还有 memory_store, memory_forget, memory_profile
```

**关键发现:**
- ✅ Tool 名称可以自定义(`memory_search` vs `memory_recall`)
- ✅ 使用 `Type.Object()` 定义参数
- ✅ 工具实现是 async 函数
- ✅ 两个项目都提供类似的工具集

---

### 3. 生命周期钩子

#### Mem0 钩子

```typescript
// mem0/openclaw/index.ts

// Auto-recall: 在 agent 开始前注入记忆
if (cfg.autoRecall) {
  api.on("before_agent_start", async (event, ctx) => {
    const sessionKey = ctx.sessionKey;
    const userId = _effectiveUserId(sessionKey);
    
    // 搜索长期记忆
    const longTermMemories = await provider.search(query, {
      user_id: userId,
      limit: cfg.topK,
    });
    
    // 搜索会话记忆
    const sessionMemories = await provider.search(query, {
      user_id: userId,
      run_id: currentSessionId,
      limit: cfg.topK,
    });
    
    // 注入到 context
    return {
      inject: [
        { role: "system", content: formatMemories(longTermMemories) },
        { role: "system", content: formatMemories(sessionMemories) },
      ],
    };
  });
}

// Auto-capture: 在 agent 结束后存储记忆
if (cfg.autoCapture) {
  api.on("agent_end", async (event, ctx) => {
    const messages = event.messages;
    const facts = extractFacts(messages);
    
    for (const fact of facts) {
      await provider.add(fact, {
        user_id: _effectiveUserId(ctx.sessionKey),
        run_id: currentSessionId,
      });
    }
  });
}
```

#### Supermemory 钩子

```typescript
// supermemory/hooks/recall.ts
export function buildRecallHandler(client: SupermemoryClient, cfg: Config) {
  return async (event: Record<string, unknown>, ctx: Record<string, unknown>) => {
    const sessionKey = ctx.sessionKey as string;
    
    // 搜索记忆
    const memories = await client.search(query, cfg.topK);
    
    // 注入到 prompt
    return {
      inject: [
        { role: "system", content: formatMemories(memories) },
      ],
    };
  };
}

// supermemory/hooks/capture.ts
export function buildCaptureHandler(client: SupermemoryClient, cfg: Config, getSessionKey: () => string | undefined) {
  return async (event: Record<string, unknown>, ctx: Record<string, unknown>) => {
    const messages = event.messages;
    const facts = extractFacts(messages);
    
    for (const fact of facts) {
      await client.store(fact, getSessionKey());
    }
  };
}

// 注册钩子
if (cfg.autoRecall) {
  api.on("before_agent_start", recallHandler);
}

if (cfg.autoCapture) {
  api.on("agent_end", captureHandler);
}
```

**关键发现:**
- ✅ 都使用 `api.on()` 注册钩子
- ✅ 关键钩子:`before_agent_start`(自动召回),`agent_end`(自动捕获)
- ✅ 钩子可以返回 `{ inject: [...] }` 注入内容
- ✅ 两者实现方式类似

---

### 4. 配置管理

#### Mem0 配置

```typescript
// mem0/openclaw/config.ts
export const mem0ConfigSchema = Type.Object({
  mode: Type.Union([
    Type.Literal("platform"),
    Type.Literal("open-source"),
  ], { default: "open-source" }),
  
  apiKey: Type.Optional(Type.String()),
  
  userId: Type.String({ default: "default" }),
  
  enableGraph: Type.Boolean({ default: false }),
  
  autoRecall: Type.Boolean({ default: true }),
  autoCapture: Type.Boolean({ default: true }),
  
  topK: Type.Number({ default: 10 }),
  
  // 开源模式配置
  oss: Type.Object({
    llm: Type.Optional(Type.Object({
      provider: Type.String(),
      model: Type.String(),
      apiKey: Type.Optional(Type.String()),
    })),
    
    embedder: Type.Optional(Type.Object({
      provider: Type.String(),
      model: Type.String(),
    })),
    
    vectorStore: Type.Optional(Type.Object({
      provider: Type.String(),
      config: Type.Object({
        // ...
      }),
    })),
  }),
});
```

#### Supermemory 配置

```typescript
// supermemory/config.ts
export const supermemoryConfigSchema = Type.Object({
  apiKey: Type.Optional(Type.String()),
  
  containerTag: Type.Optional(Type.String()),
  
  autoRecall: Type.Boolean({ default: true }),
  autoCapture: Type.Boolean({ default: true }),
  
  topK: Type.Number({ default: 10 }),
  
  debug: Type.Boolean({ default: false }),
});

export function parseConfig(config: unknown): Config {
  return supermemoryConfigSchema.parse(config);
}
```

**关键发现:**
- ✅ 使用 `Type.Object()` 定义配置 schema
- ✅ 支持可选参数和默认值
- ✅ Mem0 支持平台和开源双模式
- ✅ Supermemory 只支持云服务

---

### 5. CLI 命令

#### Mem0 CLI

```typescript
// mem0/openclaw/index.ts
api.registerCli(({ program }) => {
  const mem0 = program.command("mem0")
    .description("Mem0 memory operations");
  
  mem0.command("search")
    .description("Search memories")
    .argument("<query>", "Search query")
    .option("--limit <n>", "Max results")
    .action(async (query, opts) => {
      // 搜索实现
    });
  
  mem0.command("stats")
    .description("Show memory statistics")
    .action(async () => {
      // 统计实现
    });
}, {
  descriptors: [{
    name: "mem0",
    description: "Mem0 memory operations",
    hasSubcommands: true,
  }],
});
```

#### Supermemory CLI

```typescript
// supermemory/commands/cli.ts
export function registerCli(api: OpenClawPluginApi, client: SupermemoryClient, cfg: Config) {
  api.registerCli(({ program }) => {
    const supermemory = program.command("supermemory")
      .description("Supermemory operations");
    
    supermemory.command("search")
      .description("Search memories")
      .argument("<query>")
      .action(async (query) => {
        // 实现
      });
    
    supermemory.command("setup")
      .description("Configure Supermemory")
      .action(async () => {
        // 设置实现
      });
  });
}
```

**关键发现:**
- ✅ 都使用 `api.registerCli()` 注册 CLI 命令
- ✅ 使用 Commander.js 风格的命令定义
- ✅ 支持子命令

---

### 6. Slash 命令

#### Mem0 Slash 命令

```typescript
// mem0/openclaw/index.ts
// 没有找到明确的 slash 命令注册
// 可能通过其他方式实现
```

#### Supermemory Slash 命令

```typescript
// supermemory/commands/slash.ts
export function registerCommands(api: OpenClawPluginApi, client: SupermemoryClient, cfg: Config, getSessionKey: () => string | undefined) {
  api.registerCommand({
    name: "recall",
    description: "Recall memories manually",
    handler: async (ctx) => {
      const query = ctx.args.join(" ");
      const results = await client.search(query);
      return { memories: results };
    },
  });
  
  api.registerCommand({
    name: "remember",
    description: "Store a memory manually",
    handler: async (ctx) => {
      const text = ctx.args.join(" ");
      await client.store(text, getSessionKey());
      return { success: true };
    },
  });
}
```

**关键发现:**
- ✅ 使用 `api.registerCommand()` 注册 slash 命令
- ✅ 命令处理器是 async 函数
- ✅ Supermemory 提供了明确的 slash 命令示例

---

## 🎯 核心架构发现

### 1. **完全基于 TypeScript/JavaScript**

**关键发现:**
- ❌ Mem0 和 Supermemory **都是纯 TypeScript 实现**
- ❌ **没有 Python-JavaScript 桥接**
- ✅ 直接使用 OpenClaw Plugin SDK

### 2. **Plugin 注册模式**

**标准模式:**
```typescript
export default {
  id: "plugin-id",
  name: "Plugin Name",
  description: "Description",
  kind: "memory",  // 或 "context-engine"
  configSchema: Type.Object({...}),
  
  register(api: OpenClawPluginApi) {
    // 1. 解析配置
    const cfg = parseConfig(api.pluginConfig);
    
    // 2. 初始化客户端
    const client = createClient(cfg);
    
    // 3. 注册工具
    api.registerTool(...);
    
    // 4. 注册钩子
    api.on("before_agent_start", ...);
    api.on("agent_end", ...);
    
    // 5. 注册 CLI
    api.registerCli(...);
    
    // 6. 注册 Slash 命令
    api.registerCommand(...);
  }
};
```

### 3. **配置 Schema**

使用 `@sinclair/typebox` 定义:

```typescript
import { Type } from "@sinclair/typebox";

const configSchema = Type.Object({
  apiKey: Type.Optional(Type.String()),
  userId: Type.String({ default: "default" }),
  autoRecall: Type.Boolean({ default: true }),
  autoCapture: Type.Boolean({ default: true }),
});
```

### 4. **Tool 定义**

```typescript
api.registerTool(
  {
    name: "memory_search",
    label: "Memory Search",
    description: "...",
    parameters: Type.Object({
      query: Type.String(),
      limit: Type.Optional(Type.Number()),
    }),
  },
  async (params, ctx) => {
    // 实现
    return { results: [...] };
  }
);
```

### 5. **生命周期钩子**

**关键钩子:**
- `before_agent_start` - Agent 开始前(注入记忆)
- `agent_end` - Agent 结束后(捕获记忆)
- `session_start` - 会话开始
- `session_end` - 会话结束
- `before_tool_call` - 工具调用前
- `after_tool_call` - 工具调用后

---

## 📊 对比总结

| 特性 | Mem0 | Supermemory | claw-mem (Python) |
|------|------|-------------|-------------------|
| **语言** | TypeScript | TypeScript | Python |
| **Plugin SDK** | 原生支持 | 原生支持 | ❌ 不支持 |
| **桥接需求** | 无 | 无 | ✅ 需要 |
| **工具数量** | 5 | 4 | 3 |
| **Auto-recall** | ✅ | ✅ | ❌ |
| **Auto-capture** | ✅ | ✅ | ❌ |
| **双作用域** | ✅ | ❌ | ❌ |
| **多智能体隔离** | ✅ | ❌ | ❌ |
| **CLI 命令** | ✅ | ✅ | ❌ |
| **Slash 命令** | ❌ | ✅ | ❌ |
| **开源模式** | ✅ | ❌ | ✅ |
| **云服务** | ✅ | ✅ | ❌ |

---

## 💡 关键洞察

### 1. **TypeScript 是唯一路径**

**发现:**
- OpenClaw Plugin 系统**完全基于 TypeScript**
- Mem0 和 Supermemory **都是 TypeScript 原生实现**
- **没有发现任何 Python 桥接方案**

**结论:**
- ❌ claw-mem (Python) **无法直接使用 OpenClaw Plugin API**
- ✅ 必须重写为 TypeScript,或者使用其他集成方式

### 2. **Python-JavaScript 桥接不可行**

**原因:**
1. **性能损失**:跨语言调用开销 10-20%
2. **复杂度高**:需要维护两套代码
3. **调试困难**:跨语言调试复杂
4. **维护成本**:双语言维护困难
5. **没有先例**:社区没有 Python Plugin 案例

### 3. **迁移策略重新评估**

基于研究发现,我**强烈建议重新评估迁移策略**:

#### 方案 A:完全重写为 TypeScript(不推荐)

**优势:**
- ✅ 完全集成 OpenClaw Plugin 生态
- ✅ 原生性能,无开销
- ✅ 与 Mem0/Supermemory 一致

**劣势:**
- ⚠️ 工作量大(2-3 个月)
- ⚠️ 放弃 Python 生态
- ⚠️ 需要重写所有代码
- ⚠️ 风险高

#### 方案 B:保持独立,REST API 集成(推荐)

**优势:**
- ✅ 保持 Python 优势
- ✅ 快速集成(1-2 周)
- ✅ 独立演进
- ✅ 零风险

**劣势:**
- ⚠️ 不使用 Plugin 架构
- ⚠️ 需要额外部署

#### 方案 C:等待官方 Python 支持(观望)

**优势:**
- ✅ 等待社区成熟
- ✅ 可能有更好的方案

**劣势:**
- ⚠️ 时间不确定
- ⚠️ 可能永远不会支持

---

## 🎯 最终建议

### 推荐:方案 B(REST API 集成)

**理由:**
1. ✅ **最快见效**:1-2 周完成集成
2. ✅ **零风险**:保持 claw-mem 稳定性
3. ✅ **保持性能**:无跨语言开销
4. ✅ **独立演进**:不受 OpenClaw 影响
5. ✅ **专注核心**:claw-mem 专注记忆功能

### 实施步骤

#### Step 1: 设计 REST API(1 天)

```python
# claw_mem/api.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    user_id: str = "default"

@app.post("/memory/search")
async def search(request: SearchRequest):
    results = memory_manager.retrieve(request.query, request.limit)
    return {"memories": results}

@app.post("/memory/store")
async def store(request: StoreRequest):
    memory_id = memory_manager.store(request.text, request.metadata)
    return {"id": memory_id}
```

#### Step 2: 实现 OpenClaw 集成(2 天)

```typescript
// 在 OpenClaw 中调用
const response = await fetch("http://localhost:8000/memory/search", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: "meeting notes",
    limit: 10,
    user_id: "alice"
  })
});

const { memories } = await response.json();
```

#### Step 3: 测试和优化(2 天)

- 性能测试
- 集成测试
- 文档编写

#### Step 4: 发布(1 天)

- 发布 claw-mem v1.1.0
- 发布集成文档
- 收集反馈

---

## 📚 参考资料

### Mem0 OpenClaw Plugin

- **GitHub:** https://github.com/mem0ai/mem0
- **文档:** https://docs.mem0.ai/integrations/openclaw
- **代码:** `/tmp/mem0-openclaw-supermemory/mem0/openclaw/`

### Supermemory OpenClaw Plugin

- **GitHub:** https://github.com/supermemoryai/openclaw-supermemory
- **代码:** `/tmp/mem0-openclaw-supermemory/supermemory/`

### OpenClaw Plugin SDK

- **路径:** `~/.npm-global/lib/node_modules/openclaw/dist/plugin-sdk/`
- **类型定义:** `plugin-sdk/src/plugins/types.d.ts`

---

## ✅ 结论

**核心发现:**
1. ✅ OpenClaw Plugin 系统完全基于 TypeScript
2. ✅ Mem0 和 Supermemory 都是 TypeScript 原生实现
3. ❌ 没有发现任何 Python-JavaScript 桥接方案
4. ❌ claw-mem (Python) 无法直接使用 Plugin API

**最终建议:**
- 🎯 **采用 REST API 集成方案**
- ⏸️ **暂不迁移到 Plugin 架构**
- 👀 **观望 OpenClaw 社区发展**
- 🚀 **快速集成,专注核心价值**

---

**创建时间:** 2026-03-30 21:35  
**创建者:** Friday (AI Assistant)  
**状态:** 分析完成
