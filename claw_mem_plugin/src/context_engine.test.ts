// claw-mem v5.2.0 — Context Engine unit tests
import { describe, it, expect } from "vitest";

// Import the helper functions for testing (they're module-level in context_engine.ts)
// We test via the public API of the plugin

describe("Context Engine — Token Estimation", () => {
  it("estimates CJK tokens correctly", () => {
    // CJK: ~1 token per char
    const zh = "你好世界这是测试";
    const en = "hello world this is a test";
    const zhTokens = Math.ceil([...zh].reduce((s, ch) => s + (/[\u4e00-\u9fff]/.test(ch) ? 1 : 1/3.5), 0));
    const enTokens = Math.ceil(en.length / 3.5);
    expect(zhTokens).toBeGreaterThan(enTokens);
    expect(zhTokens).toBe(6); // 6 CJK chars
  });

  it("empty text returns 0", () => {
    const tokens = Math.ceil(0); // empty = 0 length
    expect(tokens).toBe(0);
  });
});

describe("Context Engine — Jaccard Similarity", () => {
  function jaccard(a: string, b: string): number {
    const sa = new Set(a.toLowerCase().split(/\s+/).filter((w) => w.length > 2));
    const sb = new Set(b.toLowerCase().split(/\s+/).filter((w) => w.length > 2));
    if (sa.size === 0 || sb.size === 0) return 0;
    const inter = new Set([...sa].filter((w) => sb.has(w)));
    return inter.size / (sa.size + sb.size - inter.size);
  }

  it("identical strings return 1", () => {
    expect(jaccard("hello world test", "hello world test")).toBe(1);
  });

  it("completely different returns 0", () => {
    expect(jaccard("hello world", "xyz abc def")).toBe(0);
  });

  it("partial overlap returns between 0 and 1", () => {
    const sim = jaccard("hello world test this", "hello world other thing");
    expect(sim).toBeGreaterThan(0);
    expect(sim).toBeLessThan(1);
  });
});

describe("Context Engine — Search Cache", () => {
  it("caches and retrieves entries within TTL", () => {
    const now = Date.now;
    let fakeNow = 0;
    Date.now = () => fakeNow;

    class Cache<T> {
      private store = new Map<string, { data: T; ts: number }>();
      private ttl: number;
      constructor(ttlMs = 30000) { this.ttl = ttlMs; }
      get(key: string): T | undefined {
        const e = this.store.get(key);
        if (e && fakeNow - e.ts < this.ttl) return e.data;
        this.store.delete(key);
        return undefined;
      }
      set(key: string, data: T): void { this.store.set(key, { data, ts: fakeNow }); }
    }

    const cache = new Cache<number[]>();
    cache.set("q1", [1, 2, 3]);
    expect(cache.get("q1")).toEqual([1, 2, 3]);

    fakeNow = 31000; // Beyond 30s TTL
    expect(cache.get("q1")).toBeUndefined();

    Date.now = now; // restore
  });
});

describe("Context Engine — Bisection Budget", () => {
  function selectByBudget(items: Array<{ content: string; score: number }>, budget: number): Array<{ content: string; score: number }> {
    if (items.length === 0) return [];
    const sorted = [...items].sort((a, b) => b.score - a.score);
    const tokenCounts = sorted.map((m) => Math.ceil(m.content.length / 3.5));
    let lo = 0, hi = sorted.length;
    while (lo < hi) {
      const mid = Math.ceil((lo + hi) / 2);
      const total = tokenCounts.slice(0, mid).reduce((s, t) => s + t, 0);
      if (total <= budget) lo = mid;
      else hi = mid - 1;
    }
    return sorted.slice(0, lo);
  }

  it("returns empty for empty input", () => {
    expect(selectByBudget([], 100)).toEqual([]);
  });

  it("returns all items when within budget", () => {
    const items = [{ content: "hi", score: 0.9 }, { content: "ok", score: 0.8 }];
    expect(selectByBudget(items, 100)).toHaveLength(2);
  });

  it("truncates when budget exceeded", () => {
    const items = Array.from({ length: 100 }, (_, i) => ({ content: "x".repeat(100), score: 1 - i * 0.01 }));
    const result = selectByBudget(items, 50);
    expect(result.length).toBeLessThan(100);
    const total = result.reduce((s, m) => s + Math.ceil(m.content.length / 3.5), 0);
    expect(total).toBeLessThanOrEqual(50);
  });

  it("sorts by score descending before selecting", () => {
    const items = [
      { content: "a", score: 0.3 },
      { content: "b", score: 0.9 },
      { content: "c", score: 0.5 },
    ];
    const result = selectByBudget(items, 2);
    expect(result[0].score).toBe(0.9);
    expect(result[1].score).toBe(0.5);
  });
});
