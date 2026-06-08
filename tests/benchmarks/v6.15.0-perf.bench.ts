/**
 * claw-mem v6.15.0 — Comprehensive Performance Benchmarks
 *
 * Covers: retrieval, storage, compression, and cache operations.
 * Baseline for v6.15.0 performance targets:
 *   - Retrieval latency < 10ms
 *   - Storage latency < 50ms
 */
import { bench, describe } from "vitest";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

// ── Helpers ──────────────────────────────────────────────────────────

const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-bench-v615-"));
import { InMemoryIndex } from "../../src/storage/index";
import { KeywordRetriever } from "../../src/retrieval/keyword";
import { BM25 } from "../../src/retrieval/bm25";
import { EpisodicStorage } from "../../src/storage/episodic";

// Build test dataset
const topics = [
  "authentication", "database", "deployment", "testing", "performance",
  "security", "logging", "monitoring", "caching", "networking",
];

function makeEntries(count: number): Array<{ id: string; content: string }> {
  const out: Array<{ id: string; content: string }> = [];
  for (let i = 0; i < count; i++) {
    const topic = topics[i % topics.length];
    out.push({
      id: `mem_${i}`,
      content: `${topic} guide part ${i}: Implement ${topic} best practices for scalable applications with CJK 中文支持`,
    });
  }
  return out;
}

// ── Retrieval Benchmarks ─────────────────────────────────────────────

describe("Retrieval (v6.15.0 baseline)", () => {
  const entries = makeEntries(10000);

  bench("InMemoryIndex search 5K docs", () => {
    const idx = new InMemoryIndex(3, tmpDir, false);
    idx.loadOrBuild(entries.slice(0, 5000));
    idx.search("authentication database 中文", 10);
  }, { time: 2000 });

  bench("BM25 scoring 5K docs", () => {
    const bm25 = new BM25(1.5, 0.75);
    for (const doc of entries.slice(0, 5000)) {
      bm25.addDocument(doc.id, doc.content.split(/\s+/));
    }
    bm25.getScores(["authentication", "database", "performance"]);
  }, { time: 2000 });

  bench("KeywordRetriever search 2K docs (BM25 + n-gram)", () => {
    const kw = new KeywordRetriever();
    kw.index(entries.slice(0, 2000).map(e => ({
      id: e.id, text: e.content, metadata: {},
    })));
    kw.search("authentication database 部署 性能", 10);
  }, { time: 2000 });

  bench("InMemoryIndex small search 500 docs", () => {
    const idx = new InMemoryIndex(3, tmpDir, false);
    idx.loadOrBuild(entries.slice(0, 500));
    for (let i = 0; i < 100; i++) {
      idx.search(`topic_${i % 10}`, 5);
    }
  }, { time: 1000 });
});

// ── Storage Benchmarks ───────────────────────────────────────────────

describe("Storage (v6.15.0 baseline)", () => {
  const storeDir = path.join(tmpDir, "store-bench");
  fs.mkdirSync(storeDir, { recursive: true });
  const episodic = new EpisodicStorage(storeDir, 30);

  bench("episodic store 100 entries", () => {
    for (let i = 0; i < 100; i++) {
      episodic.store({
        id: `store_${i}`,
        content: `Storage benchmark entry ${i} with content about ${topics[i % topics.length]}`,
        timestamp: new Date().toISOString(),
      });
    }
    // Cleanup after benchmark
    const files = fs.readdirSync(storeDir).filter(f => f.endsWith(".md"));
    for (const f of files) fs.unlinkSync(path.join(storeDir, f));
  }, { time: 5000 });

  bench("episodic getRecent 50 entries", () => {
    // Pre-populate
    for (let i = 0; i < 200; i++) {
      episodic.store({
        id: `recent_${i}`,
        content: `Recent benchmark ${i}: ${topics[i % topics.length]} best practices`,
        timestamp: new Date(Date.now() - i * 60000).toISOString(),
      });
    }
    episodic.getRecent(50);
    const files = fs.readdirSync(storeDir).filter(f => f.endsWith(".md"));
    for (const f of files) fs.unlinkSync(path.join(storeDir, f));
  }, { time: 3000 });
});

// ── Cache Benchmarks ─────────────────────────────────────────────────

describe("Cache (v6.15.0 baseline)", () => {
  bench("LRU-style search cache (simulated)", () => {
    const cache = new Map<string, { results: unknown; ts: number }>();
    const ttl = 5000;
    let hits = 0;
    for (let i = 0; i < 1000; i++) {
      const key = `query_${i % 50}`;
      const cached = cache.get(key);
      if (cached && Date.now() - cached.ts < ttl) {
        hits++;
        continue;
      }
      // Simulate cache store
      cache.set(key, { results: { id: i }, ts: Date.now() });
      if (cache.size > 200) {
        const firstKey = cache.keys().next().value;
        if (firstKey) cache.delete(firstKey);
      }
    }
    // Hits should be > 0 due to repeated keys
  }, { time: 2000 });
});

// ── Cleanup ──────────────────────────────────────────────────────────

try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch { /* ignore */ }
