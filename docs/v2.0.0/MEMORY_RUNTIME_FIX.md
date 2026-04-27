# claw-mem Memory Runtime Provider Fix

## Status: DEFERRED (Known Issue, Does Not Affect Core Functionality)

**Decision Date:** 2026-04-01
**Decision:** Do not fix at this time. Wait for OpenClaw official Plugin Memory Provider API documentation.

## Problem

claw-mem v2.0.0 Plugin only registers Tools (`memory_search`, `memory_store`), but does not register a **Memory Runtime Provider** with OpenClaw.

This causes `openclaw status` to show:
```
Memory: unavailable
```

## Impact Analysis

### ✅ Working (Not Affected)

| Feature | Status | Notes |
|---------|--------|-------|
| `memory_search` tool | ✅ Normal | Registered as Tool, independent of Memory Runtime |
| `memory_store` tool | ✅ Normal | Registered as Tool, independent of Memory Runtime |
| Auto-recall | ✅ Normal | Works via Tool calls |
| Auto-capture | ✅ Normal | Works via Tool calls |
| Bridge communication | ✅ Normal | stdio JSON-RPC working (~6ms latency) |

### ⚠️ Affected (Display Only)

| Feature | Status | Notes |
|---------|--------|-------|
| `openclaw status` | ❌ Shows "unavailable" | Cosmetic issue only |
| `openclaw doctor memory` | ❌ Would fail | Not critical for end users |

### Future Considerations

- Post-compaction sync may require MemorySearchManager
- Advanced features may need deeper integration

Even though the plugin loads successfully and tools work.

## Root Cause

OpenClaw's `doctor.memory.status` checks for a Memory Search Manager via:
- QMD Backend (built-in SQLite)
- Memory Index Manager (built-in fallback)
- Plugin-registered Memory Runtime Provider (`registerMemoryRuntime`)

claw-mem Plugin implements:
- ✅ Tool registration (`api.registerTool`)
- ✅ Lifecycle hooks (`api.on('before_agent_start')`, etc.)
- ❌ Memory Runtime Provider registration

## Solution

Add Memory Runtime Provider registration in `claw_mem_plugin/index.ts`:

```typescript
// Register Memory Runtime Provider
// This enables OpenClaw's memory status checks to work
api.registerMemoryRuntime?.({
  async search(query, opts) {
    return await bridge.call('search', { query, ...opts });
  },
  
  async store(text, metadata) {
    return await bridge.call('store', { text, metadata });
  },
  
  async probeEmbeddingAvailability() {
    // Check if bridge is ready and can connect to Python backend
    if (!bridge.isReady()) {
      return { ok: false, error: 'Bridge not initialized' };
    }
    
    try {
      // Probe the Python backend
      await bridge.call('status', {});
      return { ok: true };
    } catch (error) {
      return { ok: false, error: error.message };
    }
  },
  
  status() {
    return {
      provider: 'claw-mem',
      version: '2.0.0',
      backend: 'sqlite',
      ready: bridge.isReady(),
    };
  },
  
  async close() {
    await bridge.stop();
  },
});
```

## Implementation Steps

### Phase 1: Research OpenClaw Plugin API (1-2 hours)

1. Check if `registerMemoryRuntime` exists in OpenClaw Plugin API
2. Study the expected interface from OpenClaw source:
   - `memory-DyCqaz7n.js`
   - `memory-state-CKh9RZhV.js`
   - `qmd-manager-Bdi-TUef.js`
3. Document the exact interface required

### Phase 2: Implement Provider (2-3 hours)

1. Add `status()` method to Python bridge
2. Implement Memory Runtime Provider in TypeScript
3. Handle all required methods:
   - `search(query, opts)`
   - `probeEmbeddingAvailability()`
   - `status()`
   - `close()` (optional)

### Phase 3: Testing (1-2 hours)

1. Rebuild plugin: `cd claw_mem_plugin && npm run build`
2. Restart OpenClaw
3. Verify: `openclaw status` shows `Memory: claw-mem (ready)`
4. Test memory search/store still works
5. Test auto-recall and auto-capture hooks

## Fallback Option

If `registerMemoryRuntime` doesn't exist or has a different API, investigate:

1. Check OpenClaw's `api` object for memory-related methods
2. Look at how `memory-core` plugin registers
3. May need to implement a custom provider class

## Files to Modify

- `claw_mem_plugin/index.ts` - Add Memory Runtime Provider
- `claw_mem/bridge.py` - Add `status` method (if needed)
- `claw_mem/memory_manager.py` - Add status check (if needed)

## Success Criteria

- [ ] `openclaw status` shows `Memory: claw-mem (ready)` or similar
- [ ] `openclaw doctor memory` passes
- [ ] Memory tools still work (`memory_search`, `memory_store`)
- [ ] Auto-recall and auto-capture still work

## Timeline

- **Start**: DEFERRED
- **Est. Duration**: 4-7 hours (when implemented)
- **Priority**: Low (cosmetic issue, core functionality works)
- **Dependencies**: Wait for OpenClaw official Plugin Memory Provider API docs

## References

- OpenClaw Memory API: `~/.npm-global/lib/node_modules/openclaw/dist/memory-DyCqaz7n.js`
- QMD Manager: `~/.npm-global/lib/node_modules/openclaw/dist/qmd-manager-Bdi-TUef.js`
- Memory State: `~/.npm-global/lib/node_modules/openclaw/dist/memory-state-CKh9RZhV.js`
