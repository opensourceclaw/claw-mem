// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem — Plugin Bridge (TypeScript)
 *
 * Direct JSON-RPC handler interface. Routes OpenClaw plugin calls
 * to MemoryManager without subprocess. Replaces Python subprocess bridge.
 */

import { VERSION } from "./version";
import { MemoryManager, getMemoryManager } from "./memory_manager.js";
import type { SessionSnapshot } from "./session/snapshot-types.js";
import { SnapshotStore } from "./session/snapshot-store.js";

// Lazy import for benchmarks to avoid loading during tests
let _runAll: ((opts: any) => Promise<any[]>) | null = null;
let _getLastBenchmarkResults: (() => { results: any[] | null; timestamp: string | null }) | null = null;

async function getBenchmarkFunctions() {
  if (!_runAll) {
    // Use dynamic require for CommonJS compatibility
    // Try dist path first (production), then source path (development)
    const path = require('path');
    const distPath = path.join(__dirname, 'benchmarks', 'runner.js');
    const srcPath = path.join(__dirname, '..', 'benchmarks', 'runner.js');

    let benchmark: any;
    try {
      benchmark = require(distPath);
    } catch {
      benchmark = require(srcPath);
    }
    _runAll = benchmark.runAll;
    _getLastBenchmarkResults = benchmark.getLastBenchmarkResults;
  }
  return { runAll: _runAll!, getLastBenchmarkResults: _getLastBenchmarkResults! };
}

export interface JsonRpcRequest {
  jsonrpc: "2.0";
  method: string;
  params?: Record<string, unknown>;
  id?: string | number;
}

export interface JsonRpcResponse {
  jsonrpc: "2.0";
  id?: string | number;
  result?: unknown;
  error?: { code: number; message: string };
}

export interface ClawMemPluginApi {
  registerService(svc: { id: string; start(): Promise<void>; stop(): Promise<void> }): void;
  registerTool(factory: unknown, opts: { names: string[] }): void;
  on(event: string, handler: (event: unknown, ctx: unknown) => Promise<void>): void;
  pluginConfig?: Record<string, unknown>;
  logger?: { info(...a: unknown[]): void; error(...a: unknown[]): void; warn(...a: unknown[]): void };
}

/** Handle a single JSON-RPC request. Returns response suitable for serialization. */
export async function handleRequest(req: JsonRpcRequest, mm?: MemoryManager): Promise<JsonRpcResponse> {
  const id = req.id;
  const params = req.params ?? {};
  const manager = mm ?? getMemoryManager();

  try {
    const method = req.method;
    let result: unknown;

    switch (method) {
      case "ping":
        result = { version: VERSION, status: "ok" };
        break;
      case "status":
        result = manager.getStats();
        break;
      case "start_session":
        manager.sessionId = String(params.sessionId ?? "");
        result = { sessionId: manager.sessionId, status: "started" };
        break;
      case "end_session":
        manager.sessionId = null;
        result = { status: "ended" };
        break;
      case "store": {
        const storeContent = String(params.content || params.text || "");
        const memoryType = String(params.memory_type ?? "episodic");
        const success = manager.store(
          storeContent,
          memoryType,
          (params.tags as string[]) ?? [],
          (params.metadata as Record<string, unknown>) ?? {},
        );
        result = {
          success,
          strategy: manager.getStoreStrategy(memoryType),
        };
        break;
      }
      case "search":
        result = {
          results: manager.search(
            String(params.query ?? ""),
            params.memory_type as string,
            Number(params.limit ?? 10),
          ),
        };
        break;
      // v7.6.0 (ADR-003): error pattern card queries
      case "query_error_pattern_cards":
        result = {
          cards: manager.queryErrorPatternCards({
            category: typeof params.category === "string" ? params.category : undefined,
            includeInactive: params.include_inactive === true,
            limit: params.limit != null ? Number(params.limit) : undefined,
          }),
        };
        break;
      case "match_error_pattern":
        result = {
          cards: manager.matchErrorPattern(
            String(params.query ?? ""),
            params.top_k != null ? Number(params.top_k) : 5,
          ),
        };
        break;
      // v7.6.0 (ADR-005): effectiveness hit recording
      case "record_error_pattern_hit":
        result = manager.recordErrorPatternHit(String(params.card_id ?? ""), {
          avoided: params.avoided === true,
          at: typeof params.at === "string" ? params.at : undefined,
        });
        break;
      case "get":
        result = { status: "deprecated", message: "Use 'search' method instead" };
        break;
      case "delete":
        result = { status: "deprecated", message: "Not implemented. Use decay engine for cleanup" };
        break;
      case "build_context":
        result = { status: "deprecated", message: "Use claw-ctx Context Engine instead" };
        break;
      case "system.health":
        result = manager.health();
        break;
      case "system.stats":
        result = manager.getStats();
        break;
      case "system.integrityCheck": {
        const { IntegrityChecker } = require("./integrity_checker");
        result = new IntegrityChecker(manager.workspace, manager.index).quickCheck();
        break;
      }
      // v5.1.0: Constitution RPC endpoints
      case "get_constitution":
        result = {
          entries: manager.constitutionStore.getAll(),
          stats: manager.constitutionStore.getStats(),
        };
        break;
      // v6.x: Alias for backward compatibility (critical_rules migrated to constitution)
      case "get_critical_rules":
        const allEntries = manager.constitutionStore.getAll();
        const criticalEntries = allEntries.filter((e: any) => e.layer === 2 || e.tags?.includes("critical"));
        result = {
          rules: criticalEntries.map((e: any) => ({
            id: e.id,
            text: e.content,
            layer: e.layer,
          })),
        };
        break;
      case "scan_and_suggest_rule":
        result = {
          suggestions: manager.constitutionStore.scanAndSuggest(
            (params.messages as Array<{ content: string }>) ?? [],
          ),
          count: 0,
        };
        break;
      case "promote_constitution_rule":
        result = {
          status: "ok",
          entryId: manager.constitutionStore.promoteToL2(
            String(params.content ?? ""),
            (params.tags as string[]) ?? [],
          ),
        };
        break;
      case "delete_constitution_rule":
        result = {
          status: manager.constitutionStore.delete(String(params.entryId ?? ""))
            ? "deleted" : "not_found",
        };
        break;
      case "export":
        result = {
          exported: new (require("./data_portability").DataPortability)(manager.workspace)
            .exportData(String(params.outputDir || "/tmp/claw-mem-export")),
        };
        break;
      case "import":
        result = {
          imported: new (require("./data_portability").DataPortability)(manager.workspace)
            .importData(String(params.inputDir || "/tmp/claw-mem-import")),
        };
        break;

      // v5.3.0: Dispatch History + Failure Classification
      case "store_dispatch_history": {
        const content = JSON.stringify({
          agent: params.agent, intent_type: params.intent_type,
          task: params.task, result: params.result,
          latency_ms: params.latency_ms, confidence: params.confidence,
          ts: Date.now(),
        });
        const tags = ["dispatch_history", `agent:${params.agent}`, `intent:${params.intent_type}`, `result:${params.result}`];
        const ok = manager.store(content, "episodic", tags, (params.metadata as Record<string, unknown>) ?? {});
        result = { id: `dh_${Date.now()}`, success: ok };
        break;
      }
      case "get_dispatch_history": {
        const agent = params.agent as string | undefined;
        const intent = params.intent_type as string | undefined;
        const target = params.result as string | undefined;
        const tags: string[] = ["dispatch_history"];
        if (agent) tags.push(`agent:${agent}`);
        if (intent) tags.push(`intent:${intent}`);
        if (target) tags.push(`result:${target}`);
        const raw = manager.search("dispatch_history", undefined, Number(params.limit ?? 100));
        const filtered = Array.isArray(raw) ? raw.filter((r: any) => {
          const t = r.tags ?? [];
          return tags.every((tag: string) => t.includes(tag));
        }) : [];
        result = { records: filtered.slice(0, Number(params.limit ?? 100)), total: filtered.length };
        break;
      }
      case "get_dispatch_stats": {
        const raw = manager.search("dispatch_history", undefined, 10000);
        const stats: Record<string, { total: number; success: number; failure: number; avg_latency: number }> = {};
        if (Array.isArray(raw)) {
          for (const r of raw) {
            try {
              const d = JSON.parse(String(r.content ?? "{}"));
              const key = `${d.agent ?? "?"}:${d.intent_type ?? "?"}`;
              if (!stats[key]) stats[key] = { total: 0, success: 0, failure: 0, avg_latency: 0 };
              stats[key].total++;
              if (d.result === "success") stats[key].success++;
              else stats[key].failure++;
              stats[key].avg_latency = (stats[key].avg_latency * (stats[key].total - 1) + (d.latency_ms ?? 0)) / stats[key].total;
            } catch { /* skip malformed */ }
          }
        }
        const enriched: Record<string, any> = {};
        for (const [k, v] of Object.entries(stats)) {
          enriched[k] = { ...v, success_rate: v.total > 0 ? v.success / v.total : 0.5 };
        }
        result = { stats: enriched, generatedAt: new Date().toISOString() };
        break;
      }
      case "classify_failure_signal": {
        const msg = String(params.error_message ?? "").toLowerCase();
        const ctx = (params.context as Record<string, any>) ?? {};
        const classKw = ["wrong agent", "incorrect routing", "mismatched intent", "意图分类错误", "路由错误"];
        const execKw = ["timeout", "exception", "error executing", "failed to complete", "超时", "执行失败", "异常"];
        const extKw = ["network error", "api rate limit", "connection refused", "service unavailable", "网络错误"];
        let type = "execution_error", severity = "medium";
        if (classKw.some((p) => msg.includes(p))) { type = "classification_error"; }
        else if (execKw.some((p) => msg.includes(p))) { severity = ctx.critical_task ? "critical" : (ctx.retry_count > 3 ? "high" : "medium"); }
        else if (extKw.some((p) => msg.includes(p))) { type = "external_error"; severity = "low"; }
        result = { type, severity, suggestion: type === "external_error" ? "Wait and retry" : "Retry with different agent", retry_recommended: type !== "classification_error", timestamp: new Date().toISOString() };
        break;
      }

      // v5.4.0: Cross-Domain Signal Pool
      case "store_cross_domain_signal": {
        const content = JSON.stringify({
          pillar: params.pillar, agent: params.agent,
          signal_type: params.signal_type, summary: params.summary,
          impact_score: params.impact_score, related_domains: params.related_domains,
          ts: Date.now(),
        });
        const tags = ["cross_domain_signal", `pillar:${params.pillar}`, `agent:${params.agent}`, `type:${params.signal_type}`];
        const meta: Record<string, unknown> = { ...(params.metadata as any ?? {}), impact_score: params.impact_score };
        if (params.ttl) (meta as any).ttl = params.ttl;
        const ok = manager.store(content, "episodic", tags, meta);
        result = { id: `cd_${Date.now()}`, success: ok };
        break;
      }
      case "get_cross_domain_signals": {
        const pillars = (params.pillars as string[]) ?? [];
        const raw = manager.search("cross_domain_signal", undefined, Number(params.limit ?? 100));
        let filtered = Array.isArray(raw) ? raw.filter((r: any) => {
          const t = r.tags ?? [];
          if (!t.includes("cross_domain_signal")) return false;
          if (pillars.length > 0 && !pillars.some((p: string) => t.includes(`pillar:${p}`))) return false;
          const impact = (r.metadata as any)?.impact_score ?? 0;
          if (params.min_impact && impact < Number(params.min_impact)) return false;
          return true;
        }) : [];
        result = { signals: filtered.slice(0, Number(params.limit ?? 100)), total: filtered.length };
        break;
      }
      case "detect_cross_domain_correlation": {
        const cp = String(params.current_pillar ?? ""), ci = String(params.current_intent ?? "");
        const rules = [
          { kw: ["性 can ","bug","紧急","deadline","performance"], src: "stark", tgtP: "pepper", tgtI: "health", score: 0.65, tip: "工作压力 can  can 影响健康" },
          { kw: ["压力","焦虑","睡眠","stress","anxiety"], src: "pepper", tgtP: "stark", tgtI: "work", score: 0.70, tip: "健康问题 can  can 影响工作效率" },
          { kw: ["收入","奖金","promotion","raise"], src: "stark", tgtP: "happy", tgtI: "wealth", score: 0.80, tip: "工作收入变化影响财富规划" },
          { kw: ["投资","理财","股票","基金","投资组合"], src: "happy", tgtP: "stark", tgtI: "economic", score: 0.60, tip: "财富决策影响经济认知" },
          { kw: ["运动","跑步","健身","锻炼","gym"], src: "pepper", tgtP: "stark", tgtI: "business", score: 0.55, tip: "运动习惯提升工作精力" },
        ];
        const others = ["stark","pepper","happy"].filter((p) => p !== cp);
        const raw = manager.search("cross_domain_signal", undefined, 200);
        const correlations: any[] = [];
        if (Array.isArray(raw)) {
          for (const r of raw) {
            try {
              const d = JSON.parse(String(r.content ?? "{}"));
              if (!others.includes(d.pillar)) continue;
              for (const rule of rules) {
                if (d.pillar === rule.src && cp === rule.tgtP && ci === rule.tgtI) {
                  if (rule.kw.some((kw: string) => (d.summary ?? "").toLowerCase().includes(kw))) {
                    if (rule.score >= Number(params.threshold ?? 0.5))
                      correlations.push({ source_id: r.id, pillar: d.pillar, agent: d.agent, score: rule.score, suggestion: rule.tip });
                  }
                }
              }
            } catch { /* skip */ }
          }
        }
        result = { correlations: correlations.sort((a: any, b: any) => b.score - a.score), count: correlations.length };
        break;
      }
      case "generate_signal_summary": {
        const agent = String(params.agent ?? ""), task = String(params.task ?? ""), res = String(params.result ?? "success");
        const dm: Record<string, string> = { tech: "Tech", business: "Business", economic: "Economic", body: "Body", mind: "Mind", relationship: "Relationship", asset: "Asset", investment: "Investment", risk: "Risk" };
        const domain = String(params.domain ?? dm[agent] ?? agent);
        const outcome = res === "success" ? "completed" : res === "failure" ? "failed" : res;
        const human = `${agent}/${domain}: ${task}, ${outcome}`;
        result = { agent, domain, summary: human, token_count: Math.ceil(human.length / 4) };
        break;
      }
      case "cleanup_expired_signals": {
        let cleaned = 0;
        const raw = manager.search("cross_domain_signal", undefined, 1000);
        if (Array.isArray(raw)) {
          for (const r of raw) {
            const ttl = (r.metadata as any)?.ttl;
            if (ttl && r.timestamp) {
              if (Date.now() - new Date(String(r.timestamp)).getTime() > Number(ttl) * 1000) cleaned++;
            }
          }
        }
        result = { cleaned, timestamp: new Date().toISOString() };
        break;
      }

      // v5.5.0: Tech Debt Tracking
      case "store_tech_debt": {
        const p = params;
        const svToPri: Record<string, string> = { critical: "urgent", high: "high", medium: "normal", low: "low" };
        const priority = (p.priority as string) ?? svToPri[String(p.severity)] ?? "normal";
        const recordId = `debt_${Date.now()}`;
        const content = JSON.stringify({
          id: recordId, project: p.project, debt_type: p.debt_type, location: p.location,
          description: p.description, severity: p.severity, priority,
          impact_score: p.impact_score, status: "open",
          assigned_to: p.assigned_to, ts: Date.now(),
        });
        const tags = ["tech_debt", `project:${p.project}`, `type:${p.debt_type}`, `severity:${p.severity}`, "status:open"];
        const meta: Record<string, unknown> = { ...(p.metadata as any ?? {}), priority, impact_score: p.impact_score, location: p.location };
        const ok = manager.store(content, "episodic", tags, meta);
        result = { id: recordId, success: ok };
        break;
      }
      case "get_tech_debts": {
        const raw = manager.search("tech_debt", undefined, Number(params.limit ?? 100));
        let filtered = Array.isArray(raw) ? raw.filter((r: any) => {
          const t = r.tags ?? [];
          if (!t.includes("tech_debt")) return false;
          if (params.project && !t.includes(`project:${params.project}`)) return false;
          if ((params.severities as string[])?.length && !(params.severities as string[]).some((s) => t.includes(`severity:${s}`))) return false;
          return true;
        }) : [];
        result = { debts: filtered.slice(0, Number(params.limit ?? 100)), total: filtered.length };
        break;
      }
      case "update_debt_status": {
        const raw = manager.search("tech_debt", undefined, 1000);
        let updated = false;
        if (Array.isArray(raw)) {
          const target = raw.find((r: any) => String(r.id) === String(params.debt_id));
          if (target) {
            try {
              const d = JSON.parse(String((target as any).content ?? "{}"));
              d.status = params.status;
              if (params.status === "resolved") { d.resolved_at = Date.now(); d.resolution = params.resolution; }
              const newTags = ((target as any).tags as string[]).filter((t: string) => !t.startsWith("status:"));
              newTags.push(`status:${params.status}`);
              manager.store(JSON.stringify(d), "episodic", newTags, (target as any).metadata ?? {});
              updated = true;
            } catch { /* skip */ }
          }
        }
        result = { debt_id: params.debt_id, updated, status: params.status };
        break;
      }
      case "update_debt_priority": {
        const raw = manager.search("tech_debt", undefined, 1000);
        let updated = false;
        if (Array.isArray(raw)) {
          const target = raw.find((r: any) => String(r.id) === String(params.debt_id));
          if (target) {
            try {
              const d = JSON.parse(String((target as any).content ?? "{}"));
              d.priority = params.priority;
              if (params.reason) d.priority_reason = params.reason;
              manager.store(JSON.stringify(d), "episodic", (target as any).tags as string[], { ...((target as any).metadata ?? {}), priority: params.priority });
              updated = true;
            } catch { /* skip */ }
          }
        }
        result = { debt_id: params.debt_id, updated, priority: params.priority };
        break;
      }
      case "get_debt_stats": {
        const raw = manager.search("tech_debt", undefined, 10000);
        const by_sev: Record<string, number> = {}, by_type: Record<string, number> = {}, by_st: Record<string, number> = {};
        let total = 0, totalImp = 0;
        if (Array.isArray(raw)) {
          for (const r of raw) {
            try {
              const d = JSON.parse(String((r as any).content ?? "{}"));
              if (params.project && d.project !== params.project) continue;
              total++;
              const sv = d.severity ?? "unknown"; by_sev[sv] = (by_sev[sv] ?? 0) + 1;
              const tp = d.debt_type ?? "unknown"; by_type[tp] = (by_type[tp] ?? 0) + 1;
              const st = d.status ?? "open"; by_st[st] = (by_st[st] ?? 0) + 1;
              totalImp += d.impact_score ?? 0;
            } catch { /* skip */ }
          }
        }
        result = { project: params.project ?? "all", total, by_severity: by_sev, by_type, by_status: by_st, avg_impact_score: total > 0 ? totalImp / total : 0, last_updated: new Date().toISOString() };
        break;
      }

      // v6.27.0: Session Snapshot
      case "session_snapshot": {
        const snapshot = params.snapshot as SessionSnapshot;
        const store = new SnapshotStore(manager);
        result = store.store(snapshot);
        break;
      }
      case "session_get_latest": {
        const store = new SnapshotStore(manager);
        result = store.getLatest(params.sessionId ? String(params.sessionId) : undefined);
        break;
      }
      case "session_close": {
        const store = new SnapshotStore(manager);
        result = store.close(String(params.sessionId ?? ""));
        break;
      }
      case "session_get_unclosed": {
        const store = new SnapshotStore(manager);
        result = { sessions: store.getUnclosed() };
        break;
      }

      // v6.28.0: Transcript Storage
      case "transcript_get": {
        const sessionId = String(params.sessionId ?? "");
        if (!sessionId) {
          return { jsonrpc: "2.0", id, error: { code: -32602, message: "Missing sessionId" } };
        }
        const content = manager.getTranscript(sessionId);
        result = { content, sessionId };
        break;
      }
      case "transcript_get_path": {
        const sessionId = String(params.sessionId ?? "");
        if (!sessionId) {
          return { jsonrpc: "2.0", id, error: { code: -32602, message: "Missing sessionId" } };
        }
        const filePath = manager.getTranscriptPath(sessionId, params.date as string | undefined);
        result = { path: filePath, sessionId };
        break;
      }
      case "transcript_search": {
        const query = String(params.query ?? "");
        if (!query) {
          return { jsonrpc: "2.0", id, error: { code: -32602, message: "Missing query" } };
        }
        const results = manager.searchTranscripts(query, { limit: Number(params.limit ?? 10) });
        result = { results, query };
        break;
      }
      case "transcript_start": {
        const sessionId = String(params.sessionId ?? "");
        if (!sessionId) {
          return { jsonrpc: "2.0", id, error: { code: -32602, message: "Missing sessionId" } };
        }
        manager.startTranscriptSession(sessionId, params.channel as string | undefined);
        result = { ok: true, sessionId };
        break;
      }
      case "transcript_end": {
        manager.endTranscriptSession();
        result = { ok: true };
        break;
      }

      // v6.29.0: Hybrid Search
      case "hybrid_search": {
        const query = String(params.query ?? "");
        if (!query) {
          return { jsonrpc: "2.0", id, error: { code: -32602, message: "Missing query" } };
        }

        const hybridResult = manager.hybridSearch(query, {
          topK: Number(params.topK ?? params.limit ?? 10),
          minScore: Number(params.minScore ?? 0),
          filters: params.filters as any,
          fusion: params.fusion as any,
          includeCompleteness: params.includeCompleteness !== false,
        });

        result = {
          results: hybridResult.results,
          completeness_score: hybridResult.completenessScore,
          metadata: hybridResult.metadata,
        };
        break;
      }

      // v6.30.0: Entity Search
      case "entity_search": {
        const name = String(params.name ?? "");
        if (!name) {
          return { jsonrpc: "2.0", id, error: { code: -32602, message: "Missing name" } };
        }

        const entityResult = manager.entitySearch(name);
        if (!entityResult) {
          result = null;
          break;
        }

        result = {
          entity: {
            name: entityResult.entity.name,
            type: entityResult.entity.type,
            memory_ids: entityResult.entity.memoryIds,
            occurrence_count: entityResult.entity.occurrenceCount,
            first_seen: entityResult.entity.firstSeen,
            last_seen: entityResult.entity.lastSeen,
          },
          related_entities: entityResult.related,
        };
        break;
      }

      // v6.30.0: Entity Resolve
      case "entity_resolve": {
        const name = String(params.name ?? "");
        if (!name) {
          return { jsonrpc: "2.0", id, error: { code: -32602, message: "Missing name" } };
        }

        const resolveResult = manager.entityResolve(name);
        if (!resolveResult) {
          result = null;
          break;
        }

        result = {
          canonical: resolveResult.canonical,
          alternatives: resolveResult.alternatives,
          is_new: resolveResult.isNew,
        };
        break;
      }

      // v6.30.0: Entity List
      case "entity_list": {
        const limit = Number(params.limit ?? 100);
        const offset = Number(params.offset ?? 0);
        const entities = manager.listEntities(limit, offset);
        const total = manager.getEntityCount();
        result = {
          entities: entities.map(e => ({
            name: e.name,
            type: e.type,
            memory_count: e.memoryIds.length,
            occurrence_count: e.occurrenceCount,
          })),
          total,
          limit,
          offset,
        };
        break;
      }

      // v6.30.0: Entity Stats
      case "entity_stats": {
        result = manager.getEntityStats();
        break;
      }

      // 6.33.0: List Strategies
      case "list_strategies": {
        result = {
          strategies: manager.listStrategies(),
        };
        break;
      }

      // 6.33.0: Get Preference
      case "get_preference": {
        const prefKey = String(params.pref_key ?? "");
        if (!prefKey) {
          return { jsonrpc: "2.0", id, error: { code: -32602, message: "Missing pref_key" } };
        }

        const pref = manager.getPreference(prefKey);
        result = { preference: pref };
        break;
      }

      // 6.33.0: Get Preference History
      case "get_preference_history": {
        const prefKey = String(params.pref_key ?? "");
        if (!prefKey) {
          return { jsonrpc: "2.0", id, error: { code: -32602, message: "Missing pref_key" } };
        }

        const versions = manager.getPreferenceHistory(prefKey);
        result = { pref_key: prefKey, versions };
        break;
      }

      // 6.33.0: Rollback Preference
      case "rollback_preference": {
        const prefKey = String(params.pref_key ?? "");
        const version = Number(params.version ?? 0);

        if (!prefKey) {
          return { jsonrpc: "2.0", id, error: { code: -32602, message: "Missing pref_key" } };
        }
        if (!version) {
          return { jsonrpc: "2.0", id, error: { code: -32602, message: "Missing or invalid version" } };
        }

        const rolledBack = manager.rollbackPreference(prefKey, version);
        if (!rolledBack) {
          result = { error: "Rollback failed" };
        } else {
          result = { preference: rolledBack };
        }
        break;
      }

      // v6.32.0: Run Benchmarks
      case "benchmark_run": {
        const { runAll } = await getBenchmarkFunctions();
        const opts = {
          name: params.name as string | undefined,
          seed: params.seed as number | undefined,
          format: (params.format as "json" | "markdown" | "both") || "json",
          outputDir: params.outputDir as string | undefined,
          factCount: params.factCount as number | undefined,
          queryCount: params.queryCount as number | undefined,
        };

        // Run synchronously (async would require handleRequest to return Promise)
        const results = await runAll(opts);
        result = { results, count: results.length };
        break;
      }

      // v6.32.0: Get Last Benchmark Results
      case "benchmark_last": {
        const { getLastBenchmarkResults } = await getBenchmarkFunctions();
        const cached = getLastBenchmarkResults();
        result = {
          results: cached.results,
          timestamp: cached.timestamp,
        };
        break;
      }

      // v6.34.0: Inference Engine
      case "inference_derive": {
        const { InferenceEngine } = await import("./inference/index.js");

        // Create engine with search function bound to MemoryManager
        const engine = new InferenceEngine({
          searchFn: (query: string, limit: number) => {
            const raw = manager.search(query, undefined, limit);
            return (Array.isArray(raw) ? raw : []).map((r: any) => ({
              id: r.id || String(r.timestamp),
              content: r.content || r.text || "",
              metadata: r.metadata,
              timestamp: r.timestamp ? new Date(r.timestamp).getTime() : Date.now(),
              confidence: 0.8,
            }));
          },
        });

        const deriveResult = await engine.derive(
          String(params.query ?? ""),
          {
            maxSteps: params.maxSteps as number | undefined,
            confidenceThreshold: params.confidenceThreshold as number | undefined,
            maxMemories: params.maxMemories as number | undefined,
            visualize: Boolean(params.visualize),
          }
        );

        result = {
          knowledge: deriveResult.knowledge.map((k) => ({
            id: k.id,
            type: k.type,
            subject: k.subject,
            predicate: k.predicate,
            object: k.object,
            confidence: k.confidence,
            sourceMemoryIds: k.sourceMemoryIds,
          })),
          chain: deriveResult.chain,
          confidence: deriveResult.confidence,
          cacheHit: deriveResult.cacheHit,
          processingTimeMs: deriveResult.processingTimeMs,
          visualization: deriveResult.visualization,
        };
        break;
      }

      case "inference_detect_contradictions": {
        const { InferenceEngine } = await import("./inference/index.js");

        // Get memories to check
        let memories: Array<{
          id: string;
          content: string;
          metadata?: Record<string, unknown>;
          timestamp?: number;
          confidence?: number;
        }> = [];

        if (params.memoryIds) {
          // Check specific memories
          const ids = params.memoryIds as string[];
          for (const id of ids) {
            const raw = manager.search(id, undefined, 1);
            if (Array.isArray(raw) && raw.length > 0) {
              const r = raw[0] as any;
              memories.push({
                id: (r.id as string) || id,
                content: (r.content as string) || (r.text as string) || "",
                metadata: r.metadata as Record<string, unknown> | undefined,
                timestamp: r.timestamp ? new Date(r.timestamp as string).getTime() : Date.now(),
                confidence: 0.8,
              });
            }
          }
        } else {
          // Check all memories (limited)
          const raw = manager.search("", undefined, (params.limit as number) ?? 100);
          memories = (Array.isArray(raw) ? raw : []).map((r: any) => ({
            id: (r.id as string) || String(r.timestamp),
            content: (r.content as string) || (r.text as string) || "",
            metadata: r.metadata,
            timestamp: r.timestamp ? new Date(r.timestamp).getTime() : Date.now(),
            confidence: 0.8,
          }));
        }

        const engine = new InferenceEngine();
        const reports = await engine.detectContradictions(memories, {
          minConfidence: params.minConfidence as number | undefined,
          includeSuggestions: Boolean(params.includeSuggestions ?? true),
          maxResults: params.maxResults as number | undefined,
        });

        result = {
          contradictions: reports,
          count: reports.length,
        };
        break;
      }

      case "inference_stats": {
        const { InferenceEngine } = await import("./inference/index.js");
        const engine = new InferenceEngine();
        result = engine.getStats();
        break;
      }

      // v6.35.0: Structure Optimizer
      case "optimizer_assess": {
        const { StructureOptimizer } = await import("./optimizer/index.js");
        const optimizer = new StructureOptimizer();
        const report = await optimizer.assess(Boolean(params.refresh ?? false));

        result = {
          healthReport: {
            overallScore: report.overallScore,
            indexStats: report.indexStats.map((s) => ({
              name: s.name,
              type: s.type,
              hitRate: s.hitRate,
              avgLatency: s.avgLatency,
              size: s.size,
              queryCount: s.queryCount,
            })),
            unusedIndexes: report.unusedIndexes,
            missingIndexes: report.missingIndexes.map((m) => ({
              id: m.id,
              type: m.type,
              reason: m.reason,
              confidence: m.confidence,
            })),
            degradedQueries: report.degradedQueries,
          },
          metadata: report.metadata,
        };
        break;
      }

      case "optimizer_suggest": {
        const { StructureOptimizer } = await import("./optimizer/index.js");
        const optimizer = new StructureOptimizer();
        const suggestions = await optimizer.suggest();

        const limit = Number(params.limit ?? 20);
        const filtered = suggestions.slice(0, limit);

        result = {
          suggestions: filtered.map((s) => ({
            id: s.id,
            type: s.type,
            targetIndex: s.targetIndex,
            description: s.description,
            estimatedBenefit: s.estimatedBenefit,
            confidence: s.confidence,
          })),
          totalCount: suggestions.length,
        };
        break;
      }

      case "optimizer_history": {
        const { StructureOptimizer } = await import("./optimizer/index.js");
        const optimizer = new StructureOptimizer();
        const records = await optimizer.getHistory(Number(params.limit ?? 10));

        result = {
          records: records.map((r) => ({
            id: r.id,
            timestamp: r.timestamp,
            result: r.result,
            duration: r.duration,
            healthBefore: r.healthBefore,
          })),
          totalCount: records.length,
        };
        break;
      }

      case "optimizer_stats": {
        const { StructureOptimizer } = await import("./optimizer/index.js");
        const optimizer = new StructureOptimizer();
        result = optimizer.getStats();
        break;
      }

      default:
        return { jsonrpc: "2.0", id, error: { code: -32601, message: `Method '${method}' not found` } };
    }

    return { jsonrpc: "2.0", id, result };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return { jsonrpc: "2.0", id, error: { code: -32000, message: msg } };
  }
}

/** OpenClaw plugin registration entry point. */
export const plugin = {
  id: "claw-mem",
  name: `Claw Memory System (TS ${VERSION})`,
  description: "Local-First Three-Tier Memory System",
  version: VERSION,
  register(api: ClawMemPluginApi) {
    const config = api.pluginConfig ?? {};
    void new MemoryManager({
      workspace: (config.workspaceDir as string) || undefined,
      enableGating: !!(config.enableGating ?? false),
      enableDecay: !!(config.enableDecay ?? false),
      enableCompression: !!(config.enableCompression ?? true),
    });

    api.logger?.info(`[claw-mem TS] ${VERSION} initialized`);

    api.registerService({
      id: "claw-mem-ts",
      start: async () => { api.logger?.info("[claw-mem TS] service started"); },
      stop: async () => { api.logger?.info("[claw-mem TS] service stopped"); },
    });
  },
};
