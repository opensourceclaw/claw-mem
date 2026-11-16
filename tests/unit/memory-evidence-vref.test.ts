// Copyright 2026 OpenSourceClaw Contributors
// v7.10.0 (ADR-007 §4): V-ref write gate — resolvable sourceRefs, span
// substring, optional evidence, and append-only rejection tracing.

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager.js";

describe("ADR-007 V-ref evidence gate", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-vref-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
    manager.startTranscriptSession("session-evidence-1", "api");
    manager.appendTranscriptMessage({
      role: "user",
      content: "Peter said dark mode is preferred.",
      timestamp: "2026-11-15T10:00:00.000Z",
    });
    manager.endTranscriptSession();
    fs.mkdirSync(path.join(tmpDir, "memory"), { recursive: true });
    fs.writeFileSync(path.join(tmpDir, "memory", "2026-11-15.md"), "# daily note\n", "utf-8");
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  it("accepts evidence with a transcript id and returns it from search", () => {
    const text = "Peter prefers dark mode in all editors.";
    const ok = manager.store(text, "semantic", [], {}, {
      eventTime: "2026-11-15",
      evidence: [{ span: "dark mode", sourceRefs: ["session-evidence-1"] }],
    });
    expect(ok).toBe(true);

    const results = manager.search("dark mode");
    const hit = results.find((r) => String(r.content ?? r.text ?? "").includes("dark mode"));
    expect(hit).toBeTruthy();
    expect(hit!.eventTime).toBe("2026-11-15");
    expect(hit!.evidence).toEqual([{ span: "dark mode", sourceRefs: ["session-evidence-1"] }]);
  });

  it("accepts evidence supplied via metadata and a daily-note path", () => {
    const ok = manager.store("The release shipped on 2026-11-15.", "episodic", [], {
      evidence: [{ span: "shipped", sourceRefs: ["memory/2026-11-15.md"] }],
      eventTime: "2026-11-15",
    });
    expect(ok).toBe(true);

    const results = manager.search("shipped");
    expect(results).toHaveLength(1);
    expect(results[0].evidence).toEqual([{ span: "shipped", sourceRefs: ["memory/2026-11-15.md"] }]);
    // Convenience metadata keys never reach storage in raw form.
    const meta = results[0].metadata as Record<string, unknown>;
    expect(meta.evidence).toBeUndefined();
    expect(meta.eventTime).toBeUndefined();
  });

  it("accepts records without evidence (legacy behavior unchanged)", () => {
    expect(manager.store("plain legacy record", "episodic")).toBe(true);
    const results = manager.search("plain legacy record");
    expect(results).toHaveLength(1);
    expect("evidence" in results[0]).toBe(false);
    expect("eventTime" in results[0]).toBe(false);
  });

  it("accepts evidence with an empty sourceRefs array", () => {
    expect(manager.store("empty refs record", "episodic", [], {}, {
      evidence: [{ span: "empty refs", sourceRefs: [] }],
    })).toBe(true);
  });

  it("rejects a span that is not a substring and traces it", () => {
    expect(manager.store("the actual text", "episodic", [], {}, {
      evidence: [{ span: "missing fragment", sourceRefs: [] }],
    })).toBe(false);
    expect(manager.episodic.count()).toBe(0);

    const trail = manager.listEvidenceRejections({ ruleId: "v-ref-span-not-substring" });
    expect(trail).toHaveLength(1);
    expect(trail[0].action).toBe("reject");
    expect(trail[0].reason).toContain("not a substring");
    expect(fs.existsSync(path.join(tmpDir, "memory", "evidence-rejections"))).toBe(true);
  });

  it("rejects an unresolvable transcript id and traces the ref", () => {
    expect(manager.store("some text", "episodic", [], {}, {
      evidence: [{ span: "some text", sourceRefs: ["no-such-session"] }],
    })).toBe(false);
    expect(manager.episodic.count()).toBe(0);

    const trail = manager.listEvidenceRejections({ ruleId: "v-ref-unresolvable" });
    expect(trail).toHaveLength(1);
    expect(trail[0].reason).toContain("no-such-session");
  });

  it("rejects paths outside the workspace", () => {
    expect(manager.store("some text", "episodic", [], {}, {
      evidence: [{ span: "some text", sourceRefs: ["../outside.md"] }],
    })).toBe(false);
    expect(manager.listEvidenceRejections({ ruleId: "v-ref-unresolvable" })).toHaveLength(1);
  });

  it("rejects malformed evidence payloads (non-array, missing fields)", () => {
    expect(manager.store("some text", "episodic", [], {}, { evidence: "nope" as any })).toBe(false);
    expect(manager.listEvidenceRejections({ ruleId: "v-ref-malformed" })).toHaveLength(1);

    expect(manager.store("some text", "episodic", [], {}, {
      evidence: [{ sourceRefs: [] } as any],
    })).toBe(false);
    expect(manager.listEvidenceRejections({ ruleId: "v-ref-span-missing" })).toHaveLength(1);

    expect(manager.store("some text", "episodic", [], {}, {
      evidence: [{ span: "some" } as any],
    })).toBe(false);
    expect(manager.listEvidenceRejections({ ruleId: "v-ref-refs-missing" })).toHaveLength(1);
  });

  it("rejects invalid eventTime and negative offsets", () => {
    expect(manager.store("some text", "episodic", [], {}, { eventTime: "16/11/2026" })).toBe(false);
    expect(manager.listEvidenceRejections({ ruleId: "event-time-format" })).toHaveLength(1);

    expect(manager.store("some text", "episodic", [], {}, {
      evidence: [{ span: "some", offset: -1, sourceRefs: [] }],
    })).toBe(false);
    expect(manager.listEvidenceRejections({ ruleId: "v-ref-offset-invalid" })).toHaveLength(1);
  });
});
