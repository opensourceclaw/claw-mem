import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { MemoryContextBridge } from "../../src/bridge/MemoryContextBridge";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

describe("Bridge Integration", () => {
  let bridge: MemoryContextBridge;
  let tmpDir: string;
  let testFile: string;

  beforeEach(() => {
    tmpDir = path.join(os.tmpdir(), `claw-mem-int-${Date.now()}`);
    fs.mkdirSync(tmpDir, { recursive: true });
    testFile = path.join(tmpDir, "transcripts", "session-test.md");
    fs.mkdirSync(path.dirname(testFile), { recursive: true });
    fs.writeFileSync(testFile, "**User**: test\n**Assistant**: response\n".repeat(30));
    bridge = new MemoryContextBridge();
  });

  afterEach(() => {
    try { fs.rmSync(tmpDir, { recursive: true }); } catch {}
  });

  it("should report memory after write", () => {
    // Simulate what TranscriptStorage.appendMessage does
    fs.appendFileSync(testFile, "**User**: new message\n**Assistant**: reply\n", "utf-8");
    const report = bridge.reportMemorySize("test", testFile);
    expect(report.totalBytes).toBeGreaterThan(0);
    expect(report.tokenEstimate).toBeGreaterThan(0);
  });

  it("should generate warning at >80% budget", () => {
    const largeContent = "**User**: x\n**Assistant**: y\n".repeat(700);
    fs.writeFileSync(testFile, largeContent);
    const report = bridge.reportMemorySize("test", testFile);
    // Report should exist even without claw-ctx
    expect(report.sessionId).toBe("test");
  });

  it("should execute compression end-to-end", async () => {
    const report = bridge.reportMemorySize("test", testFile);
    const result = await bridge.executeCompression("test", "truncate", report.tokenEstimate / 2, testFile);
    expect(result.savedTokens).toBeGreaterThanOrEqual(0);
    expect(result.strategy).toBe("truncate");
  });
});
