import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { MemoryContextBridge } from "../../src/bridge/MemoryContextBridge";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

describe("MemoryContextBridge", () => {
  let bridge: MemoryContextBridge;
  let tmpDir: string;
  let testFile: string;

  beforeEach(() => {
    tmpDir = path.join(os.tmpdir(), `claw-mem-bridge-${Date.now()}`);
    fs.mkdirSync(tmpDir, { recursive: true });
    testFile = path.join(tmpDir, "transcripts", "session-test.md");
    fs.mkdirSync(path.dirname(testFile), { recursive: true });
    fs.writeFileSync(testFile, "**User**: Hello\n**Assistant**: Hi\n".repeat(50));
    bridge = new MemoryContextBridge();
  });

  afterEach(() => {
    try { fs.rmSync(tmpDir, { recursive: true }); } catch {}
  });

  it("should report memory size", () => {
    const report = bridge.reportMemorySize("test", testFile);
    expect(report.sessionId).toBe("test");
    expect(report.totalBytes).toBeGreaterThan(0);
    expect(report.tokenEstimate).toBeGreaterThan(0);
    expect(report.entryCount).toBeGreaterThan(0);
  });

  it("should handle large files", () => {
    const largeContent = "**User**: Test\n**Assistant**: Reply\n".repeat(200);
    fs.writeFileSync(testFile, largeContent);
    const report = bridge.reportMemorySize("large", testFile);
    expect(report.totalBytes).toBeGreaterThan(5000);
  });

  it("should start and stop periodic reporting", () => {
    bridge.startPeriodicReporting("test", 100);
    bridge.stopPeriodicReporting("test");
    // Should not throw
  });

  it("should execute truncate strategy", async () => {
    const result = await bridge.executeCompression("test", "truncate", 100, testFile);
    expect(result.strategy).toBe("truncate");
    expect(result.savedTokens).toBeGreaterThan(0);
  });

  it("should execute summarize strategy", async () => {
    const result = await bridge.executeCompression("test", "summarize", 100, testFile);
    expect(result.strategy).toBe("summarize");
  });

  it("should handle unknown strategy gracefully", async () => {
    const result = await bridge.executeCompression("test", "unknown", 100);
    expect(result.error).toBeDefined();
    expect(result.savedTokens).toBe(0);
  });

  it("should emit and receive events", () => {
    let received: any = null;
    bridge.on("test-event", (data: any) => { received = data; });
    bridge.emit("test-event", { value: 42 });
    expect(received).toEqual({ value: 42 });
  });

  it("should handle listener errors gracefully", () => {
    bridge.on("error-event", () => { throw new Error("listener error"); });
    expect(() => bridge.emit("error-event", {})).not.toThrow();
  });
});
