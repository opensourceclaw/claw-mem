import { describe, it, expect } from "vitest";

describe("Session module index", () => {
  it("should export all expected classes and constants", async () => {
    const mod = await import("../../src/session/index.js");
    expect(mod.SummaryExtractor).toBeDefined();
    expect(mod.CheckpointManager).toBeDefined();
    expect(mod.TagManager).toBeDefined();
    expect(mod.SessionRecovery).toBeDefined();
    expect(mod.SESSION_TAGS).toBeDefined();
    expect(mod.SESSION_TAGS.SUMMARY).toBe("session_summary");
    expect(mod.SESSION_TAGS.CONTINUITY).toBe("session_continuity");
  });
});
