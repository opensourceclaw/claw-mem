/**
 * claw-mem v5.2.0 — Context Engine implementation
 *
 * Implements OpenClaw's ContextEngine interface using the TS MemoryManager backend.
 */
import * as path from "path";
import { getMemoryManager, type MemoryManager } from "../../src/memory_manager";
import { ConstitutionStore } from "../../src/constitution";
import { TieredDecayEngine } from "../../src/decay/tiered_decay";
import { MemoryCompressor, CompressionLevel } from "../../src/compression/memory_compression";

// ── SDK Types ────────────────────────────────────────────────────────────────

interface ClawMemCEConfig {
  workspaceDir?: string;
  topK?: number;
  debug?: boolean;
}

interface ClawMemCELogger {
  info: (...args: any[]) => void;
  error: (...args: any[]) => void;
  warn: (...args: any[]) => void;
  debug?: (...args: any[]) => void;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function extractText(msg: any): string {
  if (!msg) return "";
  const c = msg.content;
  if (typeof c === "string") return c;
  if (Array.isArray(c)) return c.map((b: any) => typeof b === "string" ? b : b?.text ?? b?.thinking ?? "").join(" ");
  return String(c ?? "");
}

function estimateTokens(text: string): number {
  let tokens = 0;
  for (const ch of text) tokens += /[\u4e00-\u9fff\u3400-\u4dbf]/.test(ch) ? 1 : 1 / 3.5;
  return Math.ceil(tokens);
}

function jaccardSimilarity(a: string, b: string): number {
  const sa = new Set(a.toLowerCase().split(/\s+/).filter((w) => w.length > 2));
  const sb = new Set(b.toLowerCase().split(/\s+/).filter((w) => w.length > 2));
  if (sa.size === 0 || sb.size === 0) return 0;
  const inter = new Set([...sa].filter((w) => sb.has(w)));
  return inter.size / (sa.size + sb.size - inter.size);
}

function contentHash(text: string): string {
  return text.slice(0, 80).replace(/\s+/g, " ").trim().toLowerCase();
}

interface ScoredItem { content: string; score: number; raw: any }

function selectByBudget(items: ScoredItem[], budget: number): ScoredItem[] {
  if (items.length === 0) return [];
  const sorted = [...items].sort((a, b) => b.score - a.score);
  const tokenCounts = sorted.map((m) => estimateTokens(m.content));
  let lo = 0, hi = sorted.length;
  while (lo < hi) {
    const mid = Math.ceil((lo + hi) / 2);
    if (tokenCounts.slice(0, mid).reduce((s, t) => s + t, 0) <= budget) lo = mid;
    else hi = mid - 1;
  }
  return sorted.slice(0, lo);
}

class SearchCache<T> {
  private store = new Map<string, { data: T; ts: number }>();
  private ttlMs: number;
  constructor(ttlMs = 30000) { this.ttlMs = ttlMs; }
  get(key: string): T | undefined {
    const e = this.store.get(key);
    if (e && Date.now() - e.ts < this.ttlMs) return e.data;
    this.store.delete(key);
    return undefined;
  }
  set(key: string, data: T): void {
    this.store.set(key, { data, ts: Date.now() });
    if (this.store.size > 50) {
      const oldest = [...this.store.entries()].sort((a, b) => a[1].ts - b[1].ts)[0];
      if (oldest) this.store.delete(oldest[0]);
    }
  }
}

// ── Context Engine Info ──────────────────────────────────────────────────────

const CLAW_MEM_CE_INFO = {
  id: "claw-mem",
  name: "Claw Memory Context Engine",
  version: "5.2.0",
  ownsCompaction: false,
  turnMaintenanceMode: "foreground" as const,
  hostRequirements: {},
};

// ── ContextEngine Implementation ─────────────────────────────────────────────

export class ClawMemContextEngine {
  readonly info = CLAW_MEM_CE_INFO;

  private manager: MemoryManager;
  private constitution: ConstitutionStore;
  private compressor: MemoryCompressor;
  private config: ClawMemCEConfig;
  private logger: ClawMemCELogger;
  private initialized = false;
  private currentSessionId: string | null = null;
  private ingestedHashes: Set<string> = new Set();
  private searchCache = new SearchCache<any[]>(30000);

  constructor(config: ClawMemCEConfig, logger: ClawMemCELogger) {
    this.config = config;
    this.logger = logger;
    const ws = config.workspaceDir || process.cwd();
    this.manager = getMemoryManager({ workspace: ws, autoDetect: false });
    this.constitution = this.manager.constitutionStore;
    this.compressor = new MemoryCompressor(CompressionLevel.MEDIUM, true);
  }

  // ── bootstrap ──────────────────────────────────────────────────────────────

  async bootstrap(params: { sessionId: string; sessionKey?: string; sessionFile: string }): Promise<{ bootstrapped: boolean; importedMessages?: number; reason?: string }> {
    this.currentSessionId = params.sessionId;
    this.manager.sessionId = params.sessionId;
    try { this.manager.injectConstitution?.(); } catch { this.logger.warn("[claw-mem CE] Constitution injection skipped"); }
    this.initialized = true;
    return { bootstrapped: true, importedMessages: 0, reason: "Claw Memory bootstrapped" };
  }

  // ── ingest ─────────────────────────────────────────────────────────────────

  async ingest(params: { sessionId: string; sessionKey?: string; message: any; isHeartbeat?: boolean }): Promise<{ ingested: boolean }> {
    if (params.isHeartbeat) return { ingested: false };
    this._ensureSession(params.sessionId);
    const content = extractText(params.message);
    if (!content || content.length < 20) return { ingested: false };
    try { this.manager.store(content, "episodic"); return { ingested: true }; }
    catch (e) { this.logger.error("[claw-mem CE] ingest error:", e); return { ingested: false }; }
  }

  // ── ingestBatch ────────────────────────────────────────────────────────────

  async ingestBatch(params: { sessionId: string; sessionKey?: string; messages: any[]; isHeartbeat?: boolean }): Promise<{ ingestedCount: number }> {
    if (params.isHeartbeat) return { ingestedCount: 0 };
    this._ensureSession(params.sessionId);
    const candidates: string[] = [];
    for (const msg of params.messages) {
      const c = extractText(msg);
      if (!c || c.length < 20) continue;
      const h = contentHash(c);
      if (this.ingestedHashes.has(h)) continue;
      if (candidates.some((x) => jaccardSimilarity(c, x) > 0.8)) continue;
      candidates.push(c); this.ingestedHashes.add(h);
    }
    let count = 0;
    for (const c of candidates) { try { this.manager.store(c, "episodic"); count++; } catch { /* skip */ } }
    if (this.ingestedHashes.size > 500) { const arr = [...this.ingestedHashes]; this.ingestedHashes = new Set(arr.slice(-200)); }
    return { ingestedCount: count };
  }

  // ── assemble ───────────────────────────────────────────────────────────────

  async assemble(params: { sessionId: string; sessionKey?: string; messages: any[]; tokenBudget?: number; availableTools?: Set<string>; citationsMode?: string; model?: string; prompt?: string }): Promise<{ messages: any[]; estimatedTokens: number; systemPromptAddition?: string; promptAuthority?: string }> {
    this._ensureSession(params.sessionId);
    const query = params.prompt || extractText(params.messages[params.messages.length - 1]) || "";
    const topK = this.config.topK ?? 10;
    const budget = params.tokenBudget ?? 4000;

    let memories: any[] = this.searchCache.get(query) ?? [];
    if (!memories.length) {
      try { const r = this.manager.search(query, undefined, topK); memories = (r as any)?.memories ?? r ?? []; if (Array.isArray(memories)) this.searchCache.set(query, memories); }
      catch (e) { this.logger.warn("[claw-mem CE] Search failed:", e); }
    }
    if (!Array.isArray(memories) || memories.length === 0) return { messages: params.messages, estimatedTokens: 0 };

    const candidates: ScoredItem[] = memories.filter((m: any) => (m.score ?? 0) >= 0.3).map((m: any) => ({ content: m.content ?? "", score: m.score ?? 0, raw: m }));
    const selected = selectByBudget(candidates, budget);
    const tokenCount = selected.reduce((s, m) => s + estimateTokens(m.content), 0);

    let graphCtx = "";
    try { const mem = this.manager as any; if (mem.graph?.retrieve) { const gr = mem.graph.retrieve(query, 3, 0.5); if (gr?.length) { const cs = gr.map((r: any) => `[${r.type}] ${r.node?.content ?? ""}`).filter(Boolean); if (cs.length) graphCtx = `\nRelated concepts:\n${cs.join("\n")}`; } } } catch { /* optional */ }

    const lines = selected.map((m) => { const tags = Array.isArray(m.raw?.tags) ? m.raw.tags.join(", ") : ""; return `- ${tags ? `[${tags}] ` : ""}${m.content}`; });
    const memSection = lines.length ? `[Memory] Relevant context from past sessions:\n${lines.join("\n")}` : "";
    const sysAdd = (memSection + graphCtx).trim() || undefined;
    return { messages: params.messages, estimatedTokens: tokenCount, systemPromptAddition: sysAdd };
  }

  // ── compact ────────────────────────────────────────────────────────────────

  async compact(params: { sessionId: string; sessionKey?: string; sessionFile: string; tokenBudget?: number; force?: boolean; currentTokenCount?: number; compactionTarget?: string; customInstructions?: string; abortSignal?: AbortSignal }): Promise<{ ok: boolean; compacted: boolean; reason?: string; result?: { summary?: string; tokensBefore: number; tokensAfter?: number; details?: unknown } }> {
    if (params.abortSignal?.aborted) return { ok: false, compacted: false, reason: "aborted" };
    this._ensureSession(params.sessionId);
    try {
      const cur = params.currentTokenCount ?? 50000;
      if (!params.force && cur < 80000) return { ok: true, compacted: false, reason: "below threshold" };
      const all = this.manager.search("", undefined, 100);
      const arr = Array.isArray(all) ? all : [];
      const oldContent = arr.map((m: any) => m.content ?? "").join("\n");
      const before = estimateTokens(oldContent);
      if (arr.length > 0) {
        const cr = this.compressor.compress(oldContent);
        if (cr.summary) this.manager.store(cr.summary, "semantic", ["compaction", "summary"]);
        return { ok: true, compacted: true, result: { summary: cr.summary, tokensBefore: before, tokensAfter: estimateTokens(cr.summary ?? ""), details: { compressionRatio: cr.compressionRatio, extractedKeys: cr.extractedKeys } } };
      }
      return { ok: true, compacted: true, result: { summary: "Compaction complete", tokensBefore: cur } };
    } catch (e) { return { ok: false, compacted: false, reason: (e as Error).message }; }
  }

  // ── maintain ───────────────────────────────────────────────────────────────

  async maintain(params: { sessionId: string; sessionKey?: string; sessionFile: string; runtimeContext?: Record<string, unknown> }): Promise<{ changed: boolean; bytesFreed: number; rewrittenEntries: number }> {
    this._ensureSession(params.sessionId);
    let changed = false, bytesFreed = 0;
    try { const mem = this.manager as any; if (mem.decayEngine) { const r = mem.decayEngine.runCycle(); changed = (r.evicted ?? 0) > 0; bytesFreed = (r.evicted ?? 0) * 500; } }
    catch (e) { this.logger.warn("[claw-mem CE] Decay engine unavailable:", e); }
    return { changed, bytesFreed, rewrittenEntries: 0 };
  }

  // ── afterTurn ──────────────────────────────────────────────────────────────

  async afterTurn(params: { sessionId: string; sessionKey?: string; sessionFile: string; messages: any[]; prePromptMessageCount: number; autoCompactionSummary?: string; isHeartbeat?: boolean; tokenBudget?: number }): Promise<void> {
    if (params.isHeartbeat) return;
    this._ensureSession(params.sessionId);
    if (params.autoCompactionSummary) { try { this.manager.store(params.autoCompactionSummary, "episodic", ["compaction"]); } catch { /* ok */ } }
    const newMsgs = params.messages.slice(params.prePromptMessageCount);
    for (const msg of newMsgs) { const c = extractText(msg); if (c && c.length >= 30) { try { this.manager.store(c.slice(0, 500), "episodic", [msg?.role ?? "unknown", "recent"]); } catch { /* skip */ } } }
  }

  // ── Subagent Lifecycle ─────────────────────────────────────────────────────

  async prepareSubagentSpawn(params: { parentSessionKey: string; childSessionKey: string; contextMode?: "isolated" | "fork"; parentSessionId?: string; parentSessionFile?: string; childSessionId?: string; childSessionFile?: string; ttlMs?: number }): Promise<{ rollback: () => void } | undefined> {
    const mode = params.contextMode ?? "isolated";
    const childId = params.childSessionId ?? params.childSessionKey;
    let prev: string | null = null; let spawned = false;
    if (mode === "fork" && params.parentSessionId) { prev = this.currentSessionId; this.manager.sessionId = childId; spawned = true; }
    else { this.manager.sessionId = childId; spawned = true; }
    return { rollback: () => { if (spawned && prev) this.manager.sessionId = prev; } };
  }

  async onSubagentEnded(params: { childSessionKey: string; reason: "deleted" | "completed" | "swept" | "released" }): Promise<void> {
    if (params.reason === "completed") {
      try { const r = this.manager.search("important", undefined, 5); if (Array.isArray(r)) { for (const m of r) { this.manager.store(`[subagent] ${(m.content as any)?.slice?.(0, 200) ?? ""}`, "episodic", ["subagent", "merged"]); } } } catch { /* ok */ }
    }
  }

  // ── dispose ────────────────────────────────────────────────────────────────

  async dispose(): Promise<void> { this.initialized = false; this.currentSessionId = null; this.searchCache = new SearchCache<any[]>(30000); }

  // ── helpers ────────────────────────────────────────────────────────────────

  private _ensureSession(sessionId: string): void {
    if (this.currentSessionId !== sessionId) { this.currentSessionId = sessionId; this.manager.sessionId = sessionId; }
  }
}

// ── Factory ──────────────────────────────────────────────────────────────────

export function createClawMemContextEngine(config: ClawMemCEConfig, logger: ClawMemCELogger): ClawMemContextEngine {
  return new ClawMemContextEngine(config, logger);
}
