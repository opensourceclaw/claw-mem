// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v5.0.0 — Retrieval Performance Benchmarks
 */

import { bench, describe } from "vitest";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { InMemoryIndex } from "../../src/storage/index";
import { KeywordRetriever } from "../../src/retrieval/keyword";
import { BM25 } from "../../src/retrieval/bm25";

const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-bench-"));
const INDEX_SIZE = 10000;

// Build test dataset
const entries: Array<{ id: string; content: string }> = [];
const topics = ["authentication", "database", "deployment", "testing", "performance",
  "security", "logging", "monitoring", "caching", "networking"];
for (let i = 0; i < INDEX_SIZE; i++) {
  const topic = topics[i % topics.length];
  entries.push({
    id: `mem_${i}`,
    content: `${topic} guide part ${i}: Implement ${topic} best practices for scalable applications`,
  });
}

describe("Retrieval Benchmarks (~10K memories)", () => {
  bench("InMemoryIndex search (N-gram)", () => {
    const idx = new InMemoryIndex(3, tmpDir, false);
    idx.loadOrBuild(entries.slice(0, 5000));
    idx.search("authentication database", 10);
  }, { time: 2000 });

  bench("KeywordRetriever search (BM25 + N-gram)", () => {
    const kw = new KeywordRetriever();
    kw.index(entries.slice(0, 2000).map(e => ({ id: e.id, text: e.content, metadata: {} })));
    kw.search("authentication database", undefined, 10);
  }, { time: 2000 });

  bench("BM25 pure scoring (5K docs)", () => {
    const bm25 = new BM25(1.5, 0.75);
    const docs = entries.slice(0, 5000);
    for (const doc of docs) {
      bm25.addDocument(doc.id, doc.content.split(/\s+/));
    }
    bm25.score(["authentication", "database"], "mem_0");
  }, { time: 2000 });
});

// Cleanup
try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch { /* ignore */ }
