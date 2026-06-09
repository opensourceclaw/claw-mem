// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v5.0.0 — Plugin Bridge (TypeScript)
 *
 * Direct JSON-RPC handler interface. Routes OpenClaw plugin calls
 * to MemoryManager without subprocess. Replaces Python subprocess bridge.
 */

import { MemoryManager, getMemoryManager } from "./memory_manager";

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
export function handleRequest(req: JsonRpcRequest, mm?: MemoryManager): JsonRpcResponse {
  const id = req.id;
  const params = req.params ?? {};
  const manager = mm ?? getMemoryManager();

  try {
    const method = req.method;
    let result: unknown;

    switch (method) {
      case "ping":
        result = { version: "5.0.0", status: "ok" };
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
      case "store":
        result = {
          success: manager.store(
            String(params.content ?? ""),
            String(params.memory_type ?? "episodic"),
            (params.tags as string[]) ?? [],
            (params.metadata as Record<string, unknown>) ?? {},
          ),
        };
        break;
      case "search":
        result = {
          results: manager.search(
            String(params.query ?? ""),
            params.memory_type as string,
            Number(params.limit ?? 10),
          ),
        };
        break;
      case "get":
        result = { status: "not_implemented" };
        break;
      case "delete":
        result = { status: "not_implemented" };
        break;
      case "build_context":
        result = { context: "" };
        break;
      case "dreaming_run": {
        result = { staged: 0, scored: 0, passed: 0, promoted: 0, duration_ms: 0 };
        break;
      }
      case "dreaming_status":
        result = { status: "no_run" };
        break;
      case "dreaming_dry_run":
        result = { staged: 0, scored: 0, passed: 0, promoted: 0, duration_ms: 0, dry_run: true };
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
          { kw: ["性能","bug","紧急","deadline","performance"], src: "stark", tgtP: "pepper", tgtI: "health", score: 0.65, tip: "工作压力可能影响健康" },
          { kw: ["压力","焦虑","睡眠","stress","anxiety"], src: "pepper", tgtP: "stark", tgtI: "work", score: 0.70, tip: "健康问题可能影响工作效率" },
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
        const outcome = res === "success" ? "完成" : res === "failure" ? "失败" : res;
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
  name: "Claw Memory System (TS v5.0.0)",
  description: "Local-First Three-Tier Memory System",
  version: "5.0.0",
  register(api: ClawMemPluginApi) {
    const config = api.pluginConfig ?? {};
    void new MemoryManager({
      workspace: (config.workspaceDir as string) || undefined,
      enableGating: !!(config.enableGating ?? false),
      enableDecay: !!(config.enableDecay ?? false),
      enableCompression: !!(config.enableCompression ?? true),
    });

    api.logger?.info("[claw-mem TS] v5.0.0 initialized");

    api.registerService({
      id: "claw-mem-ts",
      start: async () => { api.logger?.info("[claw-mem TS] service started"); },
      stop: async () => { api.logger?.info("[claw-mem TS] service stopped"); },
    });
  },
};
