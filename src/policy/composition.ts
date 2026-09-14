// Policy composition framework (v7.8.0 T3, design §4 — CLC methodology).
// 显式化 = 只读投影：describeActivePolicies() 从现散点（importance / retention-engine /
// card constants）**读出**当前有效组合（参数即现值），不改任何行为。apply() 本版仅
// 支持「原样回放」（零行为差）；组合间自动切换/调参不在本版范围（立项件明示）。

import * as fs from "fs";
import * as path from "path";
import { IMPORTANCE_WEIGHTS } from "../importance.js";
import { DEFAULT_RETENTION_CONFIG } from "../retention/retention-engine.js";
import { GRACE_PERIOD_DAYS, HIT_WINDOW } from "../storage/error-pattern-card/constants.js";

export type PolicyDimension = "retain" | "store" | "retire";

export interface MemoryPolicySlot {
  id: string;
  dimension: PolicyDimension;
  params: Record<string, number | string | boolean>;
  enabled: boolean;
}

export interface PolicyComposition {
  slots: MemoryPolicySlot[];
}

/** 配置文件（可选）：`{workspace}/memory/policy-composition.json`——槽位参数覆盖面。 */
export const POLICY_COMPOSITION_FILE = "memory/policy-composition.json";

/**
 * 只读投影：当前有效记忆策略组合（保什么 × 存哪里 × 何时退役）。
 * 全部参数从既有散点常量读取——显式化不改行为（design §4.1）。
 *
 * 可选 workspace：存在 `memory/policy-composition.json` 时按槽位 id 合并覆盖
 * （params 浅合并 / enabled 覆盖；dimension 属结构面，不可被覆盖；未知 id 不投影）。
 * 行为侧无热切换：本版 apply() 拒绝一切行为变更，宿主若要按覆盖执行需自行在
 * 启动时读入（重启生效，design §4.1）。配置缺失/损坏 → 回退散点现值，读取永不炸。
 */
export function describeActivePolicies(workspace?: string): PolicyComposition {
  const base = baseComposition();
  if (!workspace) return base;
  const overrides = readPolicyOverrides(workspace);
  if (!overrides) return base;
  const byId = new Map(overrides.slots.map((s) => [s.id, s]));
  return {
    slots: base.slots.map((s) => {
      const o = byId.get(s.id);
      if (!o) return s;
      return {
        id: s.id,
        dimension: s.dimension,
        params: { ...s.params, ...(o.params ?? {}) },
        enabled: typeof o.enabled === "boolean" ? o.enabled : s.enabled,
      };
    }),
  };
}

function readPolicyOverrides(workspace: string): PolicyComposition | null {
  try {
    const file = path.join(workspace, POLICY_COMPOSITION_FILE);
    if (!fs.existsSync(file)) return null;
    const parsed = JSON.parse(fs.readFileSync(file, "utf-8")) as { slots?: unknown };
    if (!parsed || !Array.isArray(parsed.slots)) return null;
    return {
      slots: (parsed.slots as MemoryPolicySlot[]).filter(
        (s) => s && typeof s.id === "string" && s.params !== undefined
      ),
    };
  } catch {
    return null;
  }
}

function baseComposition(): PolicyComposition {
  return {
    slots: [
      {
        id: "retain.importance-scoring",
        dimension: "retain",
        params: { ...IMPORTANCE_WEIGHTS },
        enabled: true,
      },
      {
        id: "retain.usage-boost",
        dimension: "retain",
        params: {
          selectedBoost: DEFAULT_RETENTION_CONFIG.selectedBoost,
          successScore: DEFAULT_RETENTION_CONFIG.successScore,
          failureScore: DEFAULT_RETENTION_CONFIG.failureScore,
          neutralScore: DEFAULT_RETENTION_CONFIG.neutralScore,
        },
        enabled: true,
      },
      {
        id: "store.layer-routing",
        dimension: "store",
        params: { routes: "episodic|semantic|procedural" },
        enabled: true,
      },
      {
        id: "retire.retention-decay",
        dimension: "retire",
        params: { rho: DEFAULT_RETENTION_CONFIG.rho, maxStreak: DEFAULT_RETENTION_CONFIG.maxStreak },
        enabled: true,
      },
      {
        id: "retire.grace-period",
        dimension: "retire",
        params: { gracePeriodDays: GRACE_PERIOD_DAYS },
        enabled: true,
      },
      {
        id: "retire.hit-window",
        dimension: "retire",
        params: { hitWindow: HIT_WINDOW },
        enabled: true,
      },
    ],
  };
}

/**
 * 原样回放（本版唯一支持的形态）：composition 与 describeActivePolicies()
 * 逐字一致 → no-op 成功；任何参数差异 → 拒（本版不改行为）。
 */
export function apply(composition: PolicyComposition): { ok: true; noop: true } | { ok: false; reason: string } {
  if (canonical(composition) === canonical(describeActivePolicies())) {
    return { ok: true, noop: true };
  }
  return {
    ok: false,
    reason: "behaviour change not supported in this version — apply() only accepts a verbatim round-trip of describeActivePolicies()",
  };
}

function canonical(composition: PolicyComposition): string {
  const slots = [...(composition?.slots ?? [])]
    .map((s) => ({
      id: s.id,
      dimension: s.dimension,
      enabled: Boolean(s.enabled),
      params: Object.fromEntries(Object.entries(s.params ?? {}).sort(([a], [b]) => a.localeCompare(b))),
    }))
    .sort((a, b) => a.id.localeCompare(b.id));
  return JSON.stringify(slots);
}

// ── 因子实验评估协议 (design §4.2) ─────────────────────────────────────────
// 单因子轮换（一次只动一个槽位参数）× 固定观测窗 → 记录主效应；交互效应记录为
// 「组合对」差异（互补 = 超加性 / 互抵 = 次加性）。输出 = 结构化实验记录（JSON），
// append-only 落 `memory/policy-experiments/`。零新采集：observations 全部来自既有统计。

export interface PolicyExperimentRecord {
  experimentId: string;
  /** ISO-8601。 */
  startedAt: string;
  /** 固定观测窗（天）。 */
  windowDays: number;
  /** 单因子：轮换的槽位与参数。 */
  factor: {
    slotId: string;
    param: string;
    from: number | string | boolean;
    to: number | string | boolean;
  };
  /** 观测指标集（检索命中率 / 卡降级率 / 存储增长 / 复活率——来自既有统计）。 */
  observations: Record<string, number | string>;
  /** 交互效应（可选）：「组合对」差异记录。 */
  interaction?: { pairedWith: string; effect: "super-additive" | "sub-additive" };
  notes?: string;
}

/** append-only 落盘：一记录一文件（jsonl），永不改写既有文件。返回落盘路径。 */
export function appendExperimentRecord(workspace: string, record: PolicyExperimentRecord): string {
  const dir = path.join(workspace, "memory", "policy-experiments");
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `${record.startedAt.replace(/[:.]/g, "-")}-${Math.random().toString(36).slice(2, 6)}.jsonl`);
  fs.appendFileSync(file, JSON.stringify(record) + "\n", "utf-8");
  return file;
}

/** 读取全部实验记录（startedAt 升序）；损坏行跳过，读取永不炸。 */
export function listExperimentRecords(workspace: string): PolicyExperimentRecord[] {
  const dir = path.join(workspace, "memory", "policy-experiments");
  const records: PolicyExperimentRecord[] = [];
  if (!fs.existsSync(dir)) return records;
  for (const file of fs.readdirSync(dir)) {
    if (!file.endsWith(".jsonl")) continue;
    let text = "";
    try {
      text = fs.readFileSync(path.join(dir, file), "utf-8");
    } catch {
      continue;
    }
    for (const line of text.split("\n")) {
      if (!line.trim()) continue;
      try {
        records.push(JSON.parse(line) as PolicyExperimentRecord);
      } catch {
        // skip corrupt lines — the experiment log must never break reads
      }
    }
  }
  records.sort((a, b) => a.startedAt.localeCompare(b.startedAt));
  return records;
}

/** 空跑样例（不产结论）：验证记录格式与落盘路径的最小合法记录。 */
export function emptyRunSample(startedAt: string): PolicyExperimentRecord {
  return {
    experimentId: "dry-run-000",
    startedAt,
    windowDays: 7,
    factor: { slotId: "retire.hit-window", param: "hitWindow", from: 5, to: 5 },
    observations: { note: "empty run — format demonstration only, no conclusion" },
    notes: "空跑样例：协议 + 记录格式演示，不产结论（design §4.2）。",
  };
}
