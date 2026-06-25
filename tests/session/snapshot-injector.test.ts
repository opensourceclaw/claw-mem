// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

import { describe, it, expect } from "vitest";
import { formatRecoveryContext } from "../../src/session/snapshot-injector.js";
import { SessionSnapshot } from "../../src/session/snapshot-types.js";

function makeSnapshot(overrides: Partial<SessionSnapshot> = {}): SessionSnapshot {
  return {
    sessionId: "sess_test",
    startedAt: Date.now() - 3600_000,
    lastActiveAt: Date.now(),
    turnCount: 5,
    currentTopic: "Testing",
    recentDecisions: ["Decision 1", "Decision 2"],
    pendingItems: ["Item 1"],
    keyEntities: ["claw-mem"],
    isClosed: false,
    ...overrides,
  };
}

describe("formatRecoveryContext", () => {
  // 11
  it("includes all required fields", () => {
    const snap = makeSnapshot();
    const ctx = formatRecoveryContext(snap);
    expect(ctx).toContain("[Session Recovery]");
    expect(ctx).toContain("**Topic**: Testing");
    expect(ctx).toContain("**Key Decisions**:");
    expect(ctx).toContain("- Decision 1");
    expect(ctx).toContain("**Pending Items**:");
    expect(ctx).toContain("- Item 1");
    expect(ctx).toContain("**Last Active**:");
  });

  // 12
  it("omits activeTask section when not present", () => {
    const snap = makeSnapshot();
    delete snap.activeTask;
    const ctx = formatRecoveryContext(snap);
    expect(ctx).not.toContain("**Active Task**");
    expect(ctx).not.toContain("**Progress**");
  });

  // 13
  it("truncates long fields with ellipsis", () => {
    const snap = makeSnapshot({
      currentTopic: "A".repeat(200),
      recentDecisions: ["B".repeat(200)],
    });
    const ctx = formatRecoveryContext(snap);
    expect(ctx).toContain("…");
    // 120 chars max for topic
    const topicLine = ctx.split("\n").find((l) => l.startsWith("**Topic**"));
    expect(topicLine!.length).toBeLessThanOrEqual("**Topic**: ".length + 120);
  });

  // 14
  it("omits empty recentDecisions and pendingItems sections", () => {
    const snap = makeSnapshot({ recentDecisions: [], pendingItems: [] });
    const ctx = formatRecoveryContext(snap);
    expect(ctx).not.toContain("**Key Decisions**");
    expect(ctx).not.toContain("**Pending Items**");
  });
});
